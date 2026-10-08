"""Contain a backend and every descendant it starts (Windows job objects).

The backend is created suspended, assigned to a job with
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE and only then resumed, so no descendant can
start outside the job. Closing the job, or the death of the gateway that holds
its only handle, terminates the whole tree. Breakaway is not permitted.

This bounds what a backend leaves running; it is not a sandbox. A backend can
still ask another service (WMI, the task scheduler) to start a process.
Without job support, containment is reported as unavailable and callers must
not rely on it (a kept verified copy is then never reused).
"""
from __future__ import annotations

import os
import time

CREATE_SUSPENDED = 0x00000004
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
_JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION = 1

if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    class _BasicLimit(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                    ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]

    class _IoCounters(ctypes.Structure):
        _fields_ = [(name, ctypes.c_uint64) for name in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                                                         "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

    class _ExtendedLimit(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", _BasicLimit), ("IoInfo", _IoCounters),
                    ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

    class _Accounting(ctypes.Structure):
        _fields_ = [("TotalUserTime", ctypes.c_int64), ("TotalKernelTime", ctypes.c_int64),
                    ("ThisPeriodTotalUserTime", ctypes.c_int64), ("ThisPeriodTotalKernelTime", ctypes.c_int64),
                    ("TotalPageFaultCount", wintypes.DWORD), ("TotalProcesses", wintypes.DWORD),
                    ("ActiveProcesses", wintypes.DWORD), ("TotalTerminatedProcesses", wintypes.DWORD)]

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _ntdll = ctypes.WinDLL("ntdll")
    _kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    _kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    _kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    _kernel32.SetInformationJobObject.restype = wintypes.BOOL
    _kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    _kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    _kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    _kernel32.TerminateJobObject.restype = wintypes.BOOL
    _kernel32.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p]
    _kernel32.QueryInformationJobObject.restype = wintypes.BOOL
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel32.CloseHandle.restype = wintypes.BOOL
    _ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
    _ntdll.NtResumeProcess.restype = ctypes.c_long


def supported():
    return os.name == "nt"


def creation_flags():
    """Flags for Popen when the process will be contained by contain()."""
    return CREATE_SUSPENDED if supported() else 0


class ProcessTree:
    """Owns the job of one backend process tree."""

    def __init__(self, handle):
        self._handle = handle

    @classmethod
    def contain(cls, process):
        """Assign a suspended Popen process to a new kill-on-close job and resume it.

        Returns None if the job cannot be created or assigned; the process is
        resumed in every case where it can be, and the caller decides whether
        running without containment is acceptable. Raises OSError only if the
        suspended process cannot be resumed.
        """
        if not supported():
            return None
        handle = _kernel32.CreateJobObjectW(None, None)
        tree = None
        if handle:
            info = _ExtendedLimit()
            info.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if (_kernel32.SetInformationJobObject(handle, _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
                                                  ctypes.byref(info), ctypes.sizeof(info)) and
                    _kernel32.AssignProcessToJobObject(handle, int(process._handle))):
                tree = cls(handle)
            else:
                _kernel32.CloseHandle(handle)
        if _ntdll.NtResumeProcess(int(process._handle)) != 0:
            if tree is not None:
                tree.terminate()
            raise OSError("não foi possível retomar o backend suspenso")
        return tree

    def active_processes(self):
        info = _Accounting()
        if not _kernel32.QueryInformationJobObject(self._handle, _JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION,
                                                   ctypes.byref(info), ctypes.sizeof(info), None):
            return None
        return info.ActiveProcesses

    def terminate(self, timeout=5.0):
        """Kill every process in the tree; True only if none remains."""
        if self._handle is None:
            return True
        _kernel32.TerminateJobObject(self._handle, 1)
        deadline = time.monotonic() + timeout
        empty = False
        while time.monotonic() < deadline:
            if self.active_processes() == 0:
                empty = True
                break
            time.sleep(0.02)
        _kernel32.CloseHandle(self._handle)
        self._handle = None
        return empty

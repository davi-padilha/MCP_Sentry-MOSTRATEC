"""Contain a backend and every descendant it starts (Windows job objects).

The backend is created suspended and atomically assigned to a job with
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
import subprocess
import sys
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

    class _StartupInfo(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("lpReserved", wintypes.LPWSTR),
                    ("lpDesktop", wintypes.LPWSTR), ("lpTitle", wintypes.LPWSTR),
                    *[(name, wintypes.DWORD) for name in ("dwX", "dwY", "dwXSize", "dwYSize",
                                                        "dwXCountChars", "dwYCountChars", "dwFillAttribute", "dwFlags")],
                    ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD),
                    ("lpReserved2", ctypes.c_void_p), ("hStdInput", wintypes.HANDLE),
                    ("hStdOutput", wintypes.HANDLE), ("hStdError", wintypes.HANDLE)]

    class _StartupInfoEx(ctypes.Structure):
        _fields_ = [("StartupInfo", _StartupInfo), ("lpAttributeList", ctypes.c_void_p)]

    class _ProcessInformation(ctypes.Structure):
        _fields_ = [("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE),
                    ("dwProcessId", wintypes.DWORD), ("dwThreadId", wintypes.DWORD)]

    _kernel32.InitializeProcThreadAttributeList.argtypes = [ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
                                                           ctypes.POINTER(ctypes.c_size_t)]
    _kernel32.InitializeProcThreadAttributeList.restype = wintypes.BOOL
    _kernel32.UpdateProcThreadAttribute.argtypes = [ctypes.c_void_p, wintypes.DWORD, ctypes.c_size_t,
                                                   ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p]
    _kernel32.UpdateProcThreadAttribute.restype = wintypes.BOOL
    _kernel32.DeleteProcThreadAttributeList.argtypes = [ctypes.c_void_p]
    _kernel32.DeleteProcThreadAttributeList.restype = None
    _kernel32.CreateProcessW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.c_void_p, ctypes.c_void_p,
                                       wintypes.BOOL, wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR,
                                       ctypes.POINTER(_StartupInfoEx), ctypes.POINTER(_ProcessInformation)]
    _kernel32.CreateProcessW.restype = wintypes.BOOL

    class _JobPopen(subprocess.Popen):
        """Popen pipe/wait semantics with a job assigned inside CreateProcessW.

        This private launcher supports the gateway's direct stdio launch only.
        No global monkeypatch is used, so concurrent launches keep their jobs
        and explicit inheritable-handle lists separate.
        """
        def __init__(self, command, *, job_handle, **kwargs):
            self._job_handle = job_handle
            super().__init__(command, **kwargs)

        def _execute_child(self, args, executable, preexec_fn, close_fds, pass_fds, cwd, env,
                           startupinfo, creationflags, shell, p2cread, p2cwrite, c2pread, c2pwrite,
                           errread, errwrite, *unused):
            try:
                if shell or startupinfo is not None or pass_fds:
                    raise ValueError("contenção requer execução direta sem startupinfo externo")
                command = args if isinstance(args, str) else subprocess.list2cmdline(args)
                if "\0" in command:
                    raise ValueError("comando contém NUL")
                info = _StartupInfoEx()
                info.StartupInfo.cb = ctypes.sizeof(info)
                handles = self._filter_handle_list([int(h) for h in (p2cread, c2pwrite, errwrite) if h != -1])
                count = 2 if handles else 1
                size = ctypes.c_size_t()
                _kernel32.InitializeProcThreadAttributeList(None, count, 0, ctypes.byref(size))
                if not size.value:
                    raise ctypes.WinError(ctypes.get_last_error())
                attributes = ctypes.create_string_buffer(size.value)
                if not _kernel32.InitializeProcThreadAttributeList(attributes, count, 0, ctypes.byref(size)):
                    raise ctypes.WinError(ctypes.get_last_error())
                try:
                    jobs = (wintypes.HANDLE * 1)(self._job_handle)
                    if not _kernel32.UpdateProcThreadAttribute(attributes, 0, 0x0002000D,
                                                               jobs, ctypes.sizeof(jobs), None, None):
                        raise ctypes.WinError(ctypes.get_last_error())
                    if handles:
                        inherited = (wintypes.HANDLE * len(handles))(*handles)
                        if not _kernel32.UpdateProcThreadAttribute(attributes, 0, 0x00020002,
                                                                   inherited, ctypes.sizeof(inherited), None, None):
                            raise ctypes.WinError(ctypes.get_last_error())
                        info.StartupInfo.dwFlags = 0x100  # STARTF_USESTDHANDLES
                        info.StartupInfo.hStdInput = p2cread
                        info.StartupInfo.hStdOutput = c2pwrite
                        info.StartupInfo.hStdError = errwrite
                    info.lpAttributeList = ctypes.cast(attributes, ctypes.c_void_p)
                    environment = None
                    if env is not None:
                        entries = []
                        for key, value in sorted(env.items(), key=lambda item: item[0].upper()):
                            if not isinstance(key, str) or not isinstance(value, str) or "\0" in key + value or "=" in key:
                                raise ValueError("ambiente de execução inválido")
                            entries.append(key + "=" + value)
                        environment = ctypes.create_unicode_buffer("\0".join(entries) + "\0\0")
                    result = _ProcessInformation()
                    sys.audit("subprocess.Popen", executable, command, cwd, env)
                    if not _kernel32.CreateProcessW(
                            os.fsdecode(executable) if executable is not None else None,
                            ctypes.create_unicode_buffer(command), None, None, bool(handles),
                            creationflags | CREATE_SUSPENDED | 0x80000 | 0x400,
                            environment, os.fsdecode(cwd) if cwd is not None else None,
                            ctypes.byref(info), ctypes.byref(result)):
                        raise ctypes.WinError(ctypes.get_last_error())
                    self._child_created = True
                    self._handle = subprocess.Handle(result.hProcess)
                    self.pid = result.dwProcessId
                    _kernel32.CloseHandle(result.hThread)
                finally:
                    _kernel32.DeleteProcThreadAttributeList(attributes)
            finally:
                self._close_pipe_fds(p2cread, p2cwrite, c2pread, c2pwrite, errread, errwrite)


def supported():
    return os.name == "nt"


def creation_flags():
    """Flags for Popen when the process will be contained by contain()."""
    return CREATE_SUSPENDED if supported() else 0


class ProcessTree:
    """Owns the job of one backend process tree."""

    def __init__(self, handle):
        self._handle = handle
        self._empty_confirmed = False

    @classmethod
    def create(cls):
        handle = _kernel32.CreateJobObjectW(None, None)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        info = _ExtendedLimit()
        info.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not _kernel32.SetInformationJobObject(handle, _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
                                                 ctypes.byref(info), ctypes.sizeof(info)):
            error = ctypes.WinError(ctypes.get_last_error())
            _kernel32.CloseHandle(handle)
            raise error
        return cls(handle)

    @classmethod
    def contain(cls, process):
        """Assign a suspended Popen process to a new kill-on-close job and resume it.

        Legacy helper for an already suspended process. Failure kills it,
        never resumes it uncontained. The gateway uses spawn() to eliminate
        the crash window before assignment as well.
        """
        if not supported():
            return None
        tree = None
        try:
            tree = cls.create()
            if not _kernel32.AssignProcessToJobObject(tree._handle, int(process._handle)):
                raise ctypes.WinError(ctypes.get_last_error())
            if _ntdll.NtResumeProcess(int(process._handle)) != 0:
                raise OSError("não foi possível retomar o backend suspenso")
            return tree
        except BaseException:
            if tree is not None:
                tree.terminate()
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
            raise

    def active_processes(self):
        info = _Accounting()
        if not _kernel32.QueryInformationJobObject(self._handle, _JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION,
                                                   ctypes.byref(info), ctypes.sizeof(info), None):
            return None
        return info.ActiveProcesses

    def terminate(self, timeout=5.0):
        """Kill every process in the tree; True only if none remains."""
        if self._handle is None:
            return self._empty_confirmed
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
        self._empty_confirmed = empty
        return empty


def spawn(command, **kwargs):
    """Create a backend inside its job; no Windows fallback runs uncontained.

    Job-list assignment happens atomically in CreateProcessW, including when
    the gateway dies between process creation and resume. On POSIX fresh
    copies remain mandatory; no kept-copy containment is claimed.
    """
    if not supported():
        return subprocess.Popen(command, **kwargs), None
    tree = ProcessTree.create()
    process = None
    try:
        process = _JobPopen(command, job_handle=tree._handle, **kwargs)
        if _ntdll.NtResumeProcess(int(process._handle)) != 0:
            raise OSError("não foi possível retomar o backend suspenso")
        return process, tree
    except BaseException:
        tree.terminate()
        if process is not None:
            process.wait(timeout=5)
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
        raise

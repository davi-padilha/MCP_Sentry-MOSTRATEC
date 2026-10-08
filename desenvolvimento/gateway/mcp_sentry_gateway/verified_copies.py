"""Exclusive leases on verified copies, kept between connections for reuse.

A kept copy is reused only for the permanently approved version and only after
a full check: the exact set of expected files and of their parent directories,
no links, junctions or other reparse points, no extra hard links, and the
SHA-256 of every file. Anything else discards the copy and a fresh one is made.
Each copy is held by one connection at a time through an OS file lock, which is
released automatically if the process dies; concurrent connections get their
own copy. Copies of other versions are removed once no connection holds them.
"""
from __future__ import annotations

import os
import shutil
import stat
import uuid
from pathlib import Path, PurePosixPath

from .core import digest

PREFIX_LENGTH = 16
NAME_LENGTH = 32


def _lock(path: Path):
    """Return an open descriptor holding an exclusive lock, or None if held elsewhere."""
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(descriptor)
        return None
    return descriptor


def _unlock(descriptor):
    try:
        if os.name == "nt":
            import msvcrt
            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


def _is_link(info):
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _remove(root: Path):
    """Delete a copy without following links or junctions planted inside it."""
    if not os.path.lexists(root):
        return
    if _is_link(os.lstat(root)):
        os.unlink(root) if not os.path.isdir(root) else os.rmdir(root)
        return
    with os.scandir(root) as entries:
        for entry in entries:
            info = os.lstat(entry.path)
            if _is_link(info):
                # A directory junction/symlink is removed as a link, never traversed.
                try: os.unlink(entry.path)
                except (IsADirectoryError, PermissionError): os.rmdir(entry.path)
            elif stat.S_ISDIR(info.st_mode):
                _remove(Path(entry.path))
            else:
                os.chmod(entry.path, stat.S_IWRITE | stat.S_IREAD)
                os.unlink(entry.path)
    os.rmdir(root)


def expected_files(files):
    return {("manifest.json" if item["path"] == "@manifest" else item["path"]): item["sha256"] for item in files}


def matches(root: Path, files, cwd: str) -> bool:
    """True only if root holds exactly the expected bytes and nothing else."""
    expected = expected_files(files)
    allowed_dirs = set()
    cwd_parts = [part for part in PurePosixPath(cwd.replace("\\", "/")).parts if part != "."]
    for relative in list(expected):
        parts = PurePosixPath(relative).parts
        allowed_dirs.update("/".join(parts[:n]) for n in range(1, len(parts)))
    allowed_dirs.update("/".join(cwd_parts[:n]) for n in range(1, len(cwd_parts) + 1))
    try:
        if _is_link(os.lstat(root)) or not root.is_dir():
            return False
        seen, pending = set(), [(root, "")]
        while pending:
            folder, prefix = pending.pop()
            with os.scandir(folder) as entries:
                for entry in entries:
                    relative = prefix + entry.name
                    info = os.lstat(entry.path)
                    if _is_link(info):
                        return False
                    if stat.S_ISDIR(info.st_mode):
                        if relative not in allowed_dirs:
                            return False
                        pending.append((entry.path, relative + "/"))
                    elif stat.S_ISREG(info.st_mode):
                        if relative not in expected or info.st_nlink > 1:
                            return False
                        seen.add(relative)
                    else:
                        return False
        if seen != set(expected):
            return False
        return all(digest((root / relative).read_bytes()) == sha256 for relative, sha256 in expected.items())
    except OSError:
        return False


class CopyLease:
    """One connection's exclusive use of one verified copy directory."""

    def __init__(self, root: Path, descriptor, *, reused: bool, reusable: bool):
        self.root, self._descriptor = root, descriptor
        self.reused, self.reusable = reused, reusable

    def release(self, *, keep: bool):
        """Keep the copy for reuse, or delete it; the lock is always released."""
        try:
            if not (keep and self.reusable) or self._free_sibling_exists():
                _remove(self.root)
        finally:
            if self._descriptor is not None:
                _unlock(self._descriptor)
                self._descriptor = None

    def _free_sibling_exists(self):
        """At most one idle copy per version is kept."""
        for sibling in _copies(self.root.parent):
            if sibling != self.root and sibling.name[:PREFIX_LENGTH] == self.root.name[:PREFIX_LENGTH]:
                descriptor = _lock(_lock_path(sibling))
                if descriptor is not None:
                    _unlock(descriptor)
                    return True
        return False


def _lock_path(root: Path) -> Path:
    return root.with_name(root.name + ".lock")


def _copies(pool: Path):
    """Copy directories managed by leases (those with a lock file)."""
    if not pool.is_dir():
        return []
    return sorted(path for path in pool.iterdir()
                  if len(path.name) == NAME_LENGTH and _lock_path(path).exists() and not path.name.endswith(".lock"))


def remove_other_versions(pool: Path, expected_hash: str):
    """Remove idle copies of other versions; copies in use are left alone."""
    for copy in _copies(pool):
        if copy.name[:PREFIX_LENGTH] == expected_hash[:PREFIX_LENGTH]:
            continue
        descriptor = _lock(_lock_path(copy))
        if descriptor is None:
            continue
        try:
            _remove(copy)
        finally:
            _unlock(descriptor)


def lease(pool: Path, expected_hash: str, files, cwd: str, *, reusable: bool) -> CopyLease:
    """Lease a verified copy; reused only when reusable and matches() holds.

    A returned lease with reused=False points to an empty, newly created
    directory that the caller fills and verifies byte by byte.
    """
    pool.mkdir(parents=True, exist_ok=True)
    if reusable:
        remove_other_versions(pool, expected_hash)
        for copy in _copies(pool):
            if copy.name[:PREFIX_LENGTH] != expected_hash[:PREFIX_LENGTH]:
                continue
            descriptor = _lock(_lock_path(copy))
            if descriptor is None:
                continue
            try:
                if matches(copy, files, cwd):
                    return CopyLease(copy, descriptor, reused=True, reusable=True)
                _remove(copy)
                copy.mkdir()
            except BaseException:
                _unlock(descriptor)
                raise
            return CopyLease(copy, descriptor, reused=False, reusable=True)
    prefix = expected_hash[:PREFIX_LENGTH] if reusable else uuid.uuid4().hex[:PREFIX_LENGTH]
    root = pool / (prefix + uuid.uuid4().hex[:NAME_LENGTH - PREFIX_LENGTH])
    descriptor = _lock(_lock_path(root))
    if descriptor is None:
        raise OSError("cópia verificada nova já está em uso")
    try:
        root.mkdir(exist_ok=False)
    except BaseException:
        _unlock(descriptor)
        raise
    return CopyLease(root, descriptor, reused=False, reusable=reusable)

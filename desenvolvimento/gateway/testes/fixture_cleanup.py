"""Remove fixture links before their targets, and report cleanup errors."""
import os
import shutil
import stat
from pathlib import Path


def remove_fixture(root):
    root = Path(root)
    if not root.exists():
        return
    def unlink_children(folder):
        with os.scandir(folder) as entries:
            for entry in entries:
                info = os.lstat(entry.path)
                attrs = getattr(info, "st_file_attributes", 0)
                if stat.S_ISLNK(info.st_mode) or attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                    if os.name == "nt" and attrs & stat.FILE_ATTRIBUTE_DIRECTORY:
                        os.rmdir(entry.path)
                    else:
                        os.unlink(entry.path)
                elif stat.S_ISDIR(info.st_mode):
                    unlink_children(entry.path)
    unlink_children(root)
    shutil.rmtree(root)

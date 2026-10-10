"""Exclusive sparse scratch files with bounded I/O and measured disk allocation."""

import os
from threading import Lock


class SparseWorkspace:
    """Keep logical address space distinct from allocated disk and resident RAM.

    Sparse files are scratch space, never a replacement for VFS authority.
    The caller supplies the actual owner coordinate-folding implementation.
    """
    def __init__(self, path, logical_bytes, write_budget, fold):
        if type(logical_bytes) is not int or not 0 < logical_bytes <= 32 * 1024**3:
            raise ValueError("invalid logical capacity")
        if type(write_budget) is not int or not 0 < write_budget <= logical_bytes:
            raise ValueError("invalid write budget")
        if not callable(fold):
            raise ValueError("owner coordinate fold is required")
        self.logical_bytes, self.write_budget, self.fold = logical_bytes, write_budget, fold
        self.written = 0
        self.lock = Lock()
        self.fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.ftruncate(self.fd, logical_bytes)
        except BaseException:
            os.close(self.fd)
            self.fd = None
            os.unlink(path)
            raise

    def _range(self, offset, length):
        if self.fd is None:
            raise ValueError("workspace closed")
        if type(offset) is not int or type(length) is not int or not 0 <= length <= 65536:
            raise ValueError("invalid bounded range")
        if offset < 0 or offset + length > self.logical_bytes:
            raise ValueError("range exceeds logical capacity")

    def write(self, payload):
        if type(payload) is not bytes or not payload:
            raise ValueError("nonempty bytes required")
        with self.lock:
            offset = self.fold(payload)
            self._range(offset, len(payload))
            if self.written + len(payload) > self.write_budget:
                raise ValueError("write budget exhausted")
            # Charge before I/O: partial failures must not replenish the budget.
            self.written += len(payload)
            count = os.pwrite(self.fd, payload, offset)
            if count != len(payload):
                raise OSError("short sparse write")
            os.fsync(self.fd)
            return offset

    def read(self, offset, length):
        with self.lock:
            self._range(offset, length)
            return os.pread(self.fd, length, offset)

    def usage(self):
        with self.lock:
            self._range(0, 0)
            info = os.fstat(self.fd)
            return {"logical_bytes": info.st_size, "allocated_disk_bytes": info.st_blocks * 512,
                    "written_bytes": self.written, "max_io_bytes": 65536}

    def close(self):
        with self.lock:
            if self.fd is not None:
                os.close(self.fd)
                self.fd = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

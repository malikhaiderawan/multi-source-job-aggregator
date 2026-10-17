import os
import json
import logging
import tempfile
import threading
from typing import Any, Optional, Dict
from contextlib import contextmanager

try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

logger = logging.getLogger("FileUtils")

class _ReentrantFileLockState(threading.local):
    def __init__(self):
        super().__init__()
        self.held_locks: Dict[str, Dict[str, Any]] = {}

_LOCAL_STATE = _ReentrantFileLockState()
_THREAD_RLOCKS: Dict[str, threading.RLock] = {}
_THREAD_RLOCKS_MUTEX = threading.Lock()

def _get_thread_rlock(lock_path: str) -> threading.RLock:
    with _THREAD_RLOCKS_MUTEX:
        if lock_path not in _THREAD_RLOCKS:
            _THREAD_RLOCKS[lock_path] = threading.RLock()
        return _THREAD_RLOCKS[lock_path]

@contextmanager
def file_lock(filepath: str, shared: bool = False):
    """
    Fully reentrant context manager providing mutual exclusion across threads
    (via threading.RLock) and across processes (via fcntl.flock on POSIX / macOS systems).
    
    Safe against nested lock acquisitions within the same thread or process.
    
    NOTE: A local file lock provides concurrency safety between cooperating processes
    on the host machine. It is NOT an operating system security boundary against a
    user who has direct access to the local filesystem.
    """
    lock_path = os.path.abspath(f"{filepath}.lock")
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    
    thread_rlock = _get_thread_rlock(lock_path)
    thread_rlock.acquire()
    
    held = _LOCAL_STATE.held_locks.get(lock_path)
    if held is not None:
        held['count'] += 1
        try:
            yield
        finally:
            held['count'] -= 1
            thread_rlock.release()
        return

    fd = None
    if HAS_FCNTL:
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
        mode = fcntl.LOCK_SH if shared else fcntl.LOCK_EX
        fcntl.flock(fd, mode)

    _LOCAL_STATE.held_locks[lock_path] = {'fd': fd, 'count': 1}
    try:
        yield
    finally:
        del _LOCAL_STATE.held_locks[lock_path]
        if HAS_FCNTL and fd is not None:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except Exception as e:
                logger.warning(f"Error unlocking flock for {lock_path}: {e}")
            try:
                os.close(fd)
            except Exception as e:
                logger.warning(f"Error closing fd for {lock_path}: {e}")
        thread_rlock.release()

def atomic_write_json(filepath: str, data: Any, indent: int = 2) -> None:
    """
    Safely writes JSON data by writing to a temporary file in the same directory,
    fsyncing to disk, and performing an atomic rename via os.replace.
    If an error occurs during write or serialization, the existing file remains intact
    and the temporary file is unlinked.
    """
    abs_path = os.path.abspath(filepath)
    directory = os.path.dirname(abs_path)
    os.makedirs(directory, exist_ok=True)

    tmp_file = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=directory,
        delete=False,
        prefix=".tmp_",
        suffix=".json"
    )
    tmp_path = tmp_file.name

    try:
        json.dump(data, tmp_file, indent=indent, ensure_ascii=False)
        tmp_file.flush()
        os.fsync(tmp_file.fileno())
        tmp_file.close()
        os.replace(tmp_path, abs_path)
    except Exception as e:
        tmp_file.close()
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception as unlink_err:
                logger.warning(f"Failed to remove temporary file {tmp_path}: {unlink_err}")
        raise e

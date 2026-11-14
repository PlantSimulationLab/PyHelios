"""
Shared, thread-safe switch into the build directory for native asset lookup.

Parts of Helios open asset files by bare relative path (for example the SolarPosition data files
and the Vulkan radiation shaders) instead of resolving them through ``HELIOS_BUILD``, so those
calls only work while the process is running from the build directory. The working directory is
process-global: when each wrapper saved and restored it independently, overlapping calls from two
threads restored it out of order, pulling the directory out from under a call still in progress and
leaving the process stranded in the build directory afterward.

``build_working_directory`` is reference counted under a lock: the first caller to enter changes
directory, later callers join it, and the directory is restored only when the last caller leaves,
whatever order the callers leave in.
"""

import logging
import os
import threading
from contextlib import contextmanager
from typing import Optional, Union

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_depth = 0
_active_dir: Optional[str] = None
_restore_dir: Optional[str] = None


@contextmanager
def build_working_directory(directory: Union[str, os.PathLike]):
    """
    Run the enclosed block with ``directory`` as the process working directory.

    Safe to use from several threads at once and to nest. While any caller is inside, every caller
    must request the same directory; a conflicting request raises ``RuntimeError`` rather than
    moving the directory out from under the callers already inside.

    Args:
        directory: The build directory containing the ``plugins/<name>/`` asset trees.

    Yields:
        The directory, as given.

    Raises:
        RuntimeError: If a different directory is already active.
        OSError: If the directory cannot be entered.
    """
    global _depth, _active_dir, _restore_dir

    target = os.path.realpath(directory)
    with _lock:
        if _depth == 0:
            restore = os.getcwd()
            os.chdir(target)
            _active_dir, _restore_dir = target, restore
            logger.debug(f"Changed working directory to {target} for native asset access")
        elif target != _active_dir:
            raise RuntimeError(
                f"Cannot switch the working directory to {target}: another PyHelios call has "
                f"already switched it to {_active_dir} and is still running. Both paths should "
                f"be the same build directory; check that HELIOS_BUILD and the installed "
                f"PyHelios assets point at one build."
            )
        _depth += 1

    try:
        yield directory
    finally:
        with _lock:
            _depth -= 1
            if _depth == 0:
                restore = _restore_dir
                _active_dir = _restore_dir = None
                os.chdir(restore)
                logger.debug(f"Restored working directory to {restore}")

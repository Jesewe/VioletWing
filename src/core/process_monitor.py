import locale
import os
import platform
import sys

import psutil

# Matches the constant in game_process.py - defined here directly to avoid
# pulling in pygetwindow, which is Windows-only and not needed by this module.
_CS2_PROCESS = "cs2.exe"

# Cached Process objects so cpu_percent() measures over an interval.
# psutil returns 0.0 on the first call for any new Process instance;
# reusing the same object across polls gives accurate readings from poll 2 onward.
_cs2_proc_cache: psutil.Process | None = None
_self_proc: psutil.Process = psutil.Process(os.getpid())
# psutil.cpu_percent sums across all logical cores (e.g. 200% on a 2-core burst);
# normalizing here keeps callers in the [0, 100] range Windows Task Manager uses.
_CPU_COUNT: int = max(psutil.cpu_count(logical=True) or 1, 1)

class ProcessMonitor:
    @staticmethod
    def get_cs2_stats() -> dict | None:
        """Return {pid, cpu_percent, mem_mb} for cs2.exe, or None if not running."""
        global _cs2_proc_cache
        try:
            # Validate cached process is still the right one
            if _cs2_proc_cache is not None:
                if not _cs2_proc_cache.is_running() or _cs2_proc_cache.name().lower() != _CS2_PROCESS:
                    _cs2_proc_cache = None

            if _cs2_proc_cache is None:
                for proc in psutil.process_iter(attrs=["name", "pid"]):
                    if proc.info["name"].lower() == _CS2_PROCESS:
                        _cs2_proc_cache = psutil.Process(proc.info["pid"])
                        break

            if _cs2_proc_cache is None:
                return None

            return {
                "pid":         _cs2_proc_cache.pid,
                "cpu_percent": _cs2_proc_cache.cpu_percent(interval=None) / _CPU_COUNT,
                "mem_mb":      _cs2_proc_cache.memory_info().rss / (1024 ** 2),
            }
        except Exception:
            _cs2_proc_cache = None
            return None

    @staticmethod
    def get_self_stats() -> dict | None:
        """Return {cpu_percent, mem_mb} for the VioletWing process itself."""
        try:
            return {
                "cpu_percent": _self_proc.cpu_percent(interval=None) / _CPU_COUNT,
                "mem_mb":      _self_proc.memory_info().rss / (1024 ** 2),
            }
        except Exception:
            return None

    @staticmethod
    def get_system_ram() -> dict | None:
        """Return {total_gb, used_gb, percent} from virtual_memory(), or None on error."""
        try:
            vm = psutil.virtual_memory()
            return {
                "total_gb": vm.total / (1024 ** 3),
                "used_gb":  vm.used  / (1024 ** 3),
                "percent":  vm.percent,
            }
        except Exception:
            return None

    @staticmethod
    def log_system_info(logger) -> None:
        """Log OS, Python, RAM, and Locale information."""
        win_ver = platform.version()
        _, _, win32_build, _ = platform.win32_ver()
        logger.debug("Windows version: %s (build %s)", win_ver, win32_build)

        if not getattr(sys, "frozen", False):
            logger.debug("Python version: %s", sys.version)

        ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        logger.debug("Total RAM: %.1f GB", ram_gb)

        lang, encoding = locale.getlocale()
        logger.debug("Locale: %s / %s", lang, encoding)
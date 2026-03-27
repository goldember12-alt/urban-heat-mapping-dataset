import ctypes
import os
import time
from typing import Dict, List, Set, Tuple

import psutil

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001

CODEX_PROCESS_NAMES = {
    "codex.exe",
    "codex",
}

PYTHON_PROCESS_NAMES = {
    "python.exe",
    "python",
    "pythonw.exe",
    "py.exe",
}

CHECK_INTERVAL_SECONDS = 10
CPU_THRESHOLD_PERCENT = 1.0
IO_BYTES_THRESHOLD = 4096
CODEX_GRACE_PERIOD_SECONDS = 30

SELF_PID = os.getpid()


def prevent_sleep() -> None:
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    )


def allow_sleep() -> None:
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)


def safe_name(proc: psutil.Process) -> str:
    try:
        return (proc.name() or "").lower()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return ""


def safe_cmdline(proc: psutil.Process) -> str:
    try:
        return " ".join(proc.info.get("cmdline") or []).lower()
    except Exception:
        return ""


def safe_io_counters(proc: psutil.Process):
    try:
        return proc.io_counters()
    except Exception:
        return None


def is_watchdog_process(proc: psutil.Process) -> bool:
    if proc.pid == SELF_PID:
        return True
    return "codex_awake_guard.py" in safe_cmdline(proc)


def get_all_non_watchdog_python_processes() -> List[psutil.Process]:
    result: List[psutil.Process] = []

    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if is_watchdog_process(proc):
                continue

            if safe_name(proc) in PYTHON_PROCESS_NAMES:
                result.append(proc)
        except Exception:
            pass

    return result


def get_codex_processes() -> List[psutil.Process]:
    result: List[psutil.Process] = []

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if safe_name(proc) in CODEX_PROCESS_NAMES:
                result.append(proc)
        except Exception:
            pass

    return result


def get_descendants(proc: psutil.Process) -> List[psutil.Process]:
    try:
        return proc.children(recursive=True)
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return []


def get_descendant_pid_set(proc: psutil.Process) -> Set[int]:
    pids: Set[int] = set()

    for child in get_descendants(proc):
        try:
            pids.add(child.pid)
        except Exception:
            pass

    return pids


def get_all_codex_descendant_pids() -> Set[int]:
    pids: Set[int] = set()

    for codex_proc in get_codex_processes():
        pids.update(get_descendant_pid_set(codex_proc))

    return pids


def get_codex_descendants() -> List[psutil.Process]:
    descendants: List[psutil.Process] = []
    seen: Set[int] = set()

    for codex_proc in get_codex_processes():
        for child in get_descendants(codex_proc):
            try:
                if child.pid == SELF_PID:
                    continue
                if child.pid in seen:
                    continue

                descendants.append(child)
                seen.add(child.pid)
            except Exception:
                pass

    return descendants


def split_python_processes() -> Tuple[List[psutil.Process], List[psutil.Process]]:
    codex_descendant_pids = get_all_codex_descendant_pids()
    external_python: List[psutil.Process] = []
    codex_python: List[psutil.Process] = []

    for proc in get_all_non_watchdog_python_processes():
        try:
            if proc.pid in codex_descendant_pids:
                codex_python.append(proc)
            else:
                external_python.append(proc)
        except Exception:
            pass

    return external_python, codex_python


def prime_cpu_counters(processes: List[psutil.Process]) -> None:
    for proc in processes:
        try:
            proc.cpu_percent(interval=None)
        except Exception:
            pass


def snapshot_io(processes: List[psutil.Process]) -> Dict[int, Tuple[int, int]]:
    snapshot: Dict[int, Tuple[int, int]] = {}

    for proc in processes:
        try:
            io = safe_io_counters(proc)
            if io is not None:
                snapshot[proc.pid] = (io.read_bytes, io.write_bytes)
        except Exception:
            pass

    return snapshot


def any_cpu_active(processes: List[psutil.Process]) -> bool:
    for proc in processes:
        try:
            if proc.cpu_percent(interval=None) >= CPU_THRESHOLD_PERCENT:
                return True
        except Exception:
            pass

    return False


def any_io_active(
    processes: List[psutil.Process],
    old_snapshot: Dict[int, Tuple[int, int]],
) -> bool:
    for proc in processes:
        try:
            old = old_snapshot.get(proc.pid)
            if old is None:
                continue

            io = safe_io_counters(proc)
            if io is None:
                continue

            read_delta = io.read_bytes - old[0]
            write_delta = io.write_bytes - old[1]

            if read_delta >= IO_BYTES_THRESHOLD or write_delta >= IO_BYTES_THRESHOLD:
                return True
        except Exception:
            pass

    return False


def codex_is_actively_working(
    codex_descendants: List[psutil.Process],
    old_io_snapshot: Dict[int, Tuple[int, int]],
) -> bool:
    if not codex_descendants:
        return False

    return (
        any_cpu_active(codex_descendants)
        or any_io_active(codex_descendants, old_io_snapshot)
    )


def describe_processes(processes: List[psutil.Process], limit: int = 8) -> str:
    parts: List[str] = []

    for proc in processes[:limit]:
        try:
            parts.append(f"{safe_name(proc)}:{proc.pid}")
        except Exception:
            pass

    if len(processes) > limit:
        parts.append("...")

    return ", ".join(parts) if parts else "(none)"


def main() -> None:
    print("Sleep guard started.")
    print("Rules:")
    print("  - Ignore watchdog itself")
    print("  - Any other Python process prevents sleep")
    print("  - Codex descendants prevent sleep only when actively working")
    print("  - Codex open but idle allows sleep")
    print("Press Ctrl+C to stop.\n")

    sleep_blocked = False
    last_codex_active_time = 0.0

    while True:
        external_python, codex_python = split_python_processes()
        codex_descendants = get_codex_descendants()

        prime_cpu_counters(external_python)
        prime_cpu_counters(codex_python)
        prime_cpu_counters(codex_descendants)
        old_codex_io = snapshot_io(codex_descendants)

        time.sleep(CHECK_INTERVAL_SECONDS)

        external_python, codex_python = split_python_processes()
        codex_descendants = get_codex_descendants()

        external_python_running = len(external_python) > 0
        codex_python_running = len(codex_python) > 0
        codex_active_now = codex_is_actively_working(
            codex_descendants, old_codex_io
        )

        now = time.time()
        if codex_active_now:
            last_codex_active_time = now

        codex_recently_active = (
            now - last_codex_active_time
        ) <= CODEX_GRACE_PERIOD_SECONDS

        should_block_sleep = (
            external_python_running
            or codex_python_running
            or codex_recently_active
        )

        if should_block_sleep and not sleep_blocked:
            prevent_sleep()
            sleep_blocked = True

            if external_python_running:
                print(
                    f"[AWAKE] External Python: "
                    f"{describe_processes(external_python)}"
                )
            elif codex_python_running:
                print(
                    f"[AWAKE] Codex Python: "
                    f"{describe_processes(codex_python)}"
                )
            else:
                print(
                    f"[AWAKE] Codex active: "
                    f"{describe_processes(codex_descendants)}"
                )

        elif not should_block_sleep and sleep_blocked:
            allow_sleep()
            sleep_blocked = False
            print("[IDLE] No external Python and Codex is idle. Sleep allowed.")

        elif external_python_running:
            print(f"[PYTHON-EXT] {describe_processes(external_python)}")

        elif codex_python_running:
            print(f"[PYTHON-CODEX] {describe_processes(codex_python)}")

        elif codex_active_now or codex_recently_active:
            print(f"[CODEX] {describe_processes(codex_descendants)}")

        else:
            print("[WAITING] Codex idle. No Python running. Sleep allowed.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        allow_sleep()
        print("\nStopped. Sleep behavior restored to normal.")
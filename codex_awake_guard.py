import ctypes
import time
from typing import List, Set

import psutil

# Windows power flags
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001

# Adjust if needed after checking Task Manager -> Details
CODEX_PROCESS_NAMES = {
    "codex.exe",
    "codex",
    "chatgpt.exe",
    "chatgpt",
}

PYTHON_PROCESS_NAMES = {
    "python.exe",
    "python",
    "pythonw.exe",
    "py.exe",
}

CHECK_INTERVAL_SECONDS = 10
CPU_THRESHOLD_PERCENT = 1.0
GRACE_PERIOD_SECONDS = 30


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


def get_all_python_processes() -> List[psutil.Process]:
    result = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if safe_name(proc) in PYTHON_PROCESS_NAMES:
                result.append(proc)
        except Exception:
            pass
    return result


def get_codex_processes() -> List[psutil.Process]:
    result = []
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


def get_codex_tree_processes() -> List[psutil.Process]:
    relevant = []
    seen: Set[int] = set()

    for codex_proc in get_codex_processes():
        try:
            if codex_proc.pid not in seen:
                relevant.append(codex_proc)
                seen.add(codex_proc.pid)
        except Exception:
            pass

        for child in get_descendants(codex_proc):
            try:
                if child.pid not in seen:
                    relevant.append(child)
                    seen.add(child.pid)
            except Exception:
                pass

    return relevant


def has_python_descendant(processes: List[psutil.Process]) -> bool:
    for proc in processes:
        if safe_name(proc) in PYTHON_PROCESS_NAMES:
            return True
    return False


def prime_cpu_counters(processes: List[psutil.Process]) -> None:
    for proc in processes:
        try:
            proc.cpu_percent(interval=None)
        except Exception:
            pass


def active_cpu(processes: List[psutil.Process]) -> bool:
    for proc in processes:
        try:
            cpu = proc.cpu_percent(interval=None)
            if cpu >= CPU_THRESHOLD_PERCENT:
                return True
        except Exception:
            pass
    return False


def describe_activity(processes: List[psutil.Process]) -> str:
    names = []
    for proc in processes:
        try:
            names.append(f"{safe_name(proc)}:{proc.pid}")
        except Exception:
            pass
    return ", ".join(names[:8]) + (" ..." if len(names) > 8 else "")


def main() -> None:
    print("Sleep guard started.")
    print("Rules:")
    print("  - Any Python process prevents sleep")
    print("  - Codex active work prevents sleep")
    print("  - Codex idle with no Python running allows sleep")
    print("Press Ctrl+C to stop.\n")

    last_codex_active_time = 0.0
    sleep_blocked = False

    prime_cpu_counters(get_all_python_processes())
    prime_cpu_counters(get_codex_tree_processes())

    while True:
        all_python = get_all_python_processes()
        codex_tree = get_codex_tree_processes()
        codex_has_python = has_python_descendant(codex_tree)

        # Wait one cycle so cpu_percent() becomes meaningful
        time.sleep(CHECK_INTERVAL_SECONDS)

        all_python = get_all_python_processes()
        codex_tree = get_codex_tree_processes()

        any_python_running = len(all_python) > 0
        codex_busy = codex_has_python and active_cpu(codex_tree)

        now = time.time()
        if codex_busy:
            last_codex_active_time = now

        codex_recently_active = (now - last_codex_active_time) <= GRACE_PERIOD_SECONDS

        should_block_sleep = any_python_running or codex_recently_active

        if should_block_sleep and not sleep_blocked:
            prevent_sleep()
            sleep_blocked = True
            if any_python_running:
                print(f"[AWAKE] Python running: {describe_activity(all_python)}")
            else:
                print(f"[AWAKE] Codex active: {describe_activity(codex_tree)}")

        elif not should_block_sleep and sleep_blocked:
            allow_sleep()
            sleep_blocked = False
            print("[IDLE] No Python running and Codex is idle. Sleep is now allowed.")

        elif any_python_running:
            print(f"[PYTHON] {describe_activity(all_python)}")

        elif codex_busy or codex_recently_active:
            print(f"[CODEX] {describe_activity(codex_tree)}")

        else:
            print("[WAITING] No Python running. Codex idle. Sleep allowed.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        allow_sleep()
        print("\nStopped. Sleep behavior restored to normal.")
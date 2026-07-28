import os
import gzip
import json
import time
import threading
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from zoneinfo import ZoneInfo
import colorama

colorama.init(autoreset=True)

# --- Worker ID tracking (persistent per-thread) ---
_worker_id_counter = itertools.count(1)
_worker_id_local = threading.local()

def get_worker_id() -> int:
    if not hasattr(_worker_id_local, "id"):
        _worker_id_local.id = next(_worker_id_counter)
    return _worker_id_local.id


# --- 256-color ANSI palette ---
RESET = "\033[0m"
_COLOR_POOL = list(range(21, 231))

def get_worker_color_code(worker_id: int) -> str:
    color_num = _COLOR_POOL[(worker_id - 1) % len(_COLOR_POOL)]
    return f"\033[38;5;{color_num}m"


def cprint(worker_id: int, message: str):
    color = get_worker_color_code(worker_id)
    print(f"{color}{message}{RESET}")


# --- Global progress tracking (now per gz file, not per folder) ---
_progress_lock = threading.Lock()
_progress_counter = itertools.count(1)

# --- Active worker tracking ---
_active_lock = threading.Lock()
_active_count = 0

def enter_active() -> int:
    global _active_count
    with _active_lock:
        _active_count += 1
        return _active_count

def exit_active() -> int:
    global _active_count
    with _active_lock:
        _active_count -= 1
        return _active_count


# --- Per-output-file locks, so concurrent writers to the same folder's
# .jsonl don't interleave/corrupt each other's lines ---
_output_locks_guard = threading.Lock()
_output_locks: dict[str, threading.Lock] = {}

def get_output_lock(output_path: str) -> threading.Lock:
    with _output_locks_guard:
        if output_path not in _output_locks:
            _output_locks[output_path] = threading.Lock()
        return _output_locks[output_path]


def get_foldernames(path: str) -> list[str]:
    return [
        f for f in os.listdir(path)
        if os.path.isdir(os.path.join(path, f))
    ]


def get_filenames(path: str) -> list[str]:
    return [
        f for f in os.listdir(path)
        if os.path.isfile(os.path.join(path, f))
    ]


def parse_abstract(inverted_index: dict) -> str:
    if not inverted_index:
        return ""

    max_pos = max(pos for positions in inverted_index.values() for pos in positions)

    words = [""] * (max_pos + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word

    return " ".join(words)


def append_line(filepath, line):
    lock = get_output_lock(filepath)
    with lock:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(line)


def process_gz_file(update_folder: str, gz_file: str, openalex_works_folder: str, output_dir: str,
                     search_type: str, search_terms: list[str], total_files: int, max_workers: int):
    worker_id = get_worker_id()

    with _progress_lock:
        current_index = next(_progress_counter)

    active_now = enter_active()

    try:
        output_path = os.path.join(output_dir, f"{update_folder}.jsonl")
        gz_path = os.path.join(openalex_works_folder, update_folder, gz_file)

        pct = (current_index / total_files * 100) if total_files else 100.0

        cprint(worker_id, f'Worker_{worker_id} [active: {active_now}/{max_workers}]:\t{update_folder}/{gz_file}\t({current_index}/{total_files} files, {pct:.1f}%)')

        with gzip.open(gz_path, 'rt', encoding='utf-8') as lines:
            for line in lines:
                work = json.loads(line)
                work_type = work.get('type') or ''
                if search_type in work_type.lower():
                    work_title = work.get('title') or ''
                    title_lower = work_title.lower()
                    if any(term in title_lower for term in search_terms):
                        append_line(output_path, line)
    finally:
        exit_active()


def main():
    start_time = time.time()
    start = datetime.fromtimestamp(start_time, tz=ZoneInfo("Europe/Berlin"))
    print(f'Start time: {start}')

    openalex_works_folder = 'D:\\openalex-snapshot\\data\\works'
    output_dir = os.path.join(os.getcwd(), 'outputs')
    os.makedirs(output_dir, exist_ok=True)

    update_folders = get_foldernames(openalex_works_folder)

    search_type = 'article'
    search_terms = [
        'vector database',
        'vectordatabase',
        'vektordatenbank',
        'vektor datenbank',
    ]

    max_workers = 32

    # --- Build a flat list of (update_folder, gz_file) tasks across ALL folders ---
    print('Scanning folders to build task list...')
    tasks = []
    for update_folder in update_folders:
        folder_path = os.path.join(openalex_works_folder, update_folder)
        gz_files = sorted(get_filenames(folder_path))
        for gz_file in gz_files:
            tasks.append((update_folder, gz_file))

    total_files = len(tasks)
    print(f'Found {total_files} .gz files across {len(update_folders)} update folders.')

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {
            executor.submit(
                process_gz_file,
                update_folder, gz_file, openalex_works_folder, output_dir,
                search_type, search_terms, total_files, max_workers,
            ): (update_folder, gz_file)
            for update_folder, gz_file in tasks
        }

        for future in as_completed(future_to_task):
            update_folder, gz_file = future_to_task[future]
            try:
                future.result()
            except Exception as exc:
                print(f'File {update_folder}/{gz_file} raised an exception: {exc}')

    end_time = time.time()
    end = datetime.fromtimestamp(end_time, tz=ZoneInfo("Europe/Berlin"))
    print(f'Start time: {start}')
    print(f'End time:   {end}')
    print("--- %s minutes ---" % ((end_time - start_time) / 60))


if __name__ == '__main__':
    main()
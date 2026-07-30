import os
import gzip
import json
import csv
import glob
import shutil
import time
import threading
import itertools
import colorsys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse
import colorama

colorama.init(autoreset=True)

# --- Work IDs from OpenAlex CSV file ---
_work_ids = {} # global work_ids used from all workers
_total_target_count = 0

def get_works_id_from_csv(csv_path: str) -> dict:
    ids = []
    with open(csv_path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            ids.append(row["Work ID"])

    work_ids = {}
    for id in ids:
        work_ids[id] = False
    
    return work_ids

def get_only_false_work_ids(work_ids) -> dict:
     return {key: value for key, value in work_ids.items() if value is False}

# --- Worker ID tracking (persistent per-thread) ---
_worker_id_counter = itertools.count(1)
_worker_id_local = threading.local()

def get_worker_id() -> int:
    if not hasattr(_worker_id_local, "id"):
        _worker_id_local.id = next(_worker_id_counter)
    return _worker_id_local.id

# --- Rainbow ANSI truecolor palette, evenly spread across max_workers ---
RESET = "\033[0m"
_max_workers_for_color = 1  # set in main(), used to spread the rainbow evenly

def get_worker_color_code(worker_id: int) -> str:
    hue = ((worker_id - 1) / max(_max_workers_for_color, 1)) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    return f"\033[38;2;{int(r * 255)};{int(g * 255)};{int(b * 255)}m"

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

# --- Found work-ids tracking (how many target ids matched so far) ---
_found_lock = threading.Lock()
_found_count = 0

def register_found() -> int:
    global _found_count
    with _found_lock:
        _found_count += 1
        return _found_count

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

def cprint(worker_id: int, message: str):
    color = get_worker_color_code(worker_id)
    timestamp = datetime.now(ZoneInfo("Europe/Berlin")).strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{color}{timestamp} {message}{RESET}")

def process_gz_file(update_folder: str, gz_file: str, openalex_works_folder: str, output_dir: str, total_files: int, max_workers: int):

    worker_id = get_worker_id()

    with _progress_lock:
        current_index = next(_progress_counter)

    active_now = enter_active()
    active_decremented = False

    try:
        output_path = os.path.join(output_dir, f"output_worker_{worker_id}.jsonl")
        gz_path = os.path.join(openalex_works_folder, update_folder, gz_file)

        pct = (current_index / total_files * 100) if total_files else 100.0

        cprint(
            worker_id,
            f"{f'worker_{worker_id}':<9} [active: {active_now:>2}/{max_workers}]: "
            f"{update_folder}/{gz_file:<12} "
            f"({current_index}/{total_files} files, {pct:.1f}%) "
            f"[{found_so_far}/{_total_target_count} work_ids found]"
        )

        with gzip.open(gz_path, 'rt', encoding='utf-8') as lines:
            for line in lines:
                work = json.loads(line)
                id = work.get('id') or ''
                work_id = id.split("/")[-1]
                if _work_ids.get(work_id) is not None:
                    output_line = json.dumps(work, ensure_ascii=True) + "\n"
                    append_line(output_path, output_line)
                    _work_ids[work_id] = True
                    register_found()

        active_now = exit_active()
        active_decremented = True

        found_so_far = _found_count
        cprint(
            worker_id,
            f"{f'worker_{worker_id}':<9} [active:{active_now:>2}/{max_workers}]: "
            f"{update_folder}/{gz_file:<12} "
            f"({current_index}/{total_files} files, {pct:.1f}%) "
            f"[{found_so_far}/{_total_target_count} work_ids found] finished"
        )

    finally:
        if not active_decremented:
            exit_active()

def main():
    parser = argparse.ArgumentParser(description="Extract target Work IDs from an OpenAlex snapshot.")
    parser.add_argument("openalex_works_folder", help="Path to the openalex-snapshot 'works' folder")
    parser.add_argument("openalex_csv_file", help="Path to the openalex csv file containing target Work IDs")
    parser.add_argument(
        "--max-workers",
        type=int,
        default=8,
        help="Maximum number of concurrent worker threads (default: 32, max recommended: 128)"
    )
    args = parser.parse_args()

    start_timestamp = time.time()
    start_time = datetime.fromtimestamp(start_timestamp, tz=ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d_%H-%M-%S")
    print(f'Start time: {start_time}')

    max_workers = args.max_workers

    global _max_workers_for_color
    _max_workers_for_color = max_workers

    openalex_works_folder = args.openalex_works_folder
    update_folders = get_foldernames(openalex_works_folder)

    global _work_ids, _total_target_count
    _work_ids = get_works_id_from_csv(args.openalex_csv_file)
    _total_target_count = len(_work_ids)
    print(f'Loaded {len(_work_ids)} target Work IDs from CSV.')

    output_dir = os.path.join(os.getcwd(), f'outputs-{start_time}')
    os.makedirs(output_dir, exist_ok=True)   

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
            executor.submit(process_gz_file, update_folder, gz_file, openalex_works_folder, output_dir, total_files, max_workers): (update_folder, gz_file)
            for update_folder, gz_file in tasks
        }

        for future in as_completed(future_to_task):
            update_folder, gz_file = future_to_task[future]
            try:
                future.result()
            except Exception as exc:
                print(f'File {update_folder}/{gz_file} raised an exception: {exc}')

    # Combine worker outputs into one single jsonl file
    print('Combining per-worker output files...')
    combined_path = os.path.join(output_dir, "output_combined.jsonl")
    worker_files = sorted(glob.glob(os.path.join(output_dir, "output_worker_*.jsonl")))
    with open(combined_path, "w", encoding="utf-8") as outfile:
        for fname in worker_files:
            with open(fname, "r", encoding="utf-8") as infile:
                shutil.copyfileobj(infile, outfile)
    print(f'Combined {len(worker_files)} worker files into {combined_path}')

    # Write work ids that were not found in openalex-snapshot to json file
    with open(os.path.join(output_dir, "missing-work-ids.json"), "w") as file:
        json.dump(get_only_false_work_ids(_work_ids), file, indent=4)
    print(f'Created file with {len(get_only_false_work_ids(_work_ids))} entries for work ids not found in openalex-snapshot.')

    # Calculate script run time
    end_timestamp = time.time()
    end_time = datetime.fromtimestamp(end_timestamp, tz=ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d_%H-%M-%S")
    print(f'Start time: {start_time}')
    print(f'End time:   {end_time}')
    print("Total minutes: %s" % ((end_timestamp - start_timestamp) / 60))

if __name__ == '__main__':
    main()
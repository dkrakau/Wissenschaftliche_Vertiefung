import os
import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo

lines_counter = 0

with open("output.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        lines_counter = lines_counter + 1
        record = json.loads(line)
        print(record)

print(f'Total lines: {lines_counter}')
import csv
import json
import os


with open('data1.json', 'r', encoding='utf-8') as f:
    lines = f.readlines()

data = []
for i, line in enumerate(lines):
    try:
        obj = json.loads(line)
        data.append(obj)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON on line {i}: {e}")

print(type(data))
FIELDNAMES = ['loại nhà đất', 'địa chỉ', 'giá', 'diện tích', 'giá/m2', 'mặt tiền', 'phòng ngủ', 'pháp lý', 'tọa độ x', 'tọa độ y', 'số tầng']

csv_path = 'data_1.csv'
write_header = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0

with open(csv_path, 'a', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    if write_header:
        writer.writeheader()

    for obj in data:
        if not isinstance(obj, dict):
            # skip malformed entries
            continue

        # Normalize: only keep keys that are in FIELDNAMES. This avoids ValueError when
        # JSON objects contain extra fields (e.g., 'tọa độ').
        row = {k: obj.get(k, '') for k in FIELDNAMES}
        writer.writerow(row)


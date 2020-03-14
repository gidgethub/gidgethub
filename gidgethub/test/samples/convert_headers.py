"""Convert the header output from ``curl --head`` to a JSON object representing
those headers.

All keys will be lowercase and the status code will be used for the file name.
"""
import json
import sys


raw_headers = sys.stdin.read()
print(raw_headers)
header_lines = raw_headers.splitlines()
status_code = int(header_lines[0].split()[1])
del header_lines[0]
headers = {}
for line in header_lines:
    key, _, value = line.partition(":")
    headers[key.lower().strip()] = value.strip()
with open(f"{status_code}.json", "w") as file:
    json.dump(headers, file, ensure_ascii=False)

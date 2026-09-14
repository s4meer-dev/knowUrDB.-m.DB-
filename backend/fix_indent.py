import os

filepath = r"c:\Users\samee\OneDrive\Desktop\xd\my projects\knowUrDB\backend\app\api\query.py"
with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    # lines 219 to 305 (0-indexed 218 to 304)
    if 218 <= i <= 304:
        new_lines.append("    " + line)
    else:
        new_lines.append(line)

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Dedented lines 202-305 successfully.")

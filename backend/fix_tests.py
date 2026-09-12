import os
import glob

files = glob.glob('tests/api/test_query*.py')
for filename in files:
    with open(filename, 'r') as f:
        content = f.read()
    
    content = content.replace('json={"question": q}', 'json={"question": q, "source_id": "demo-source-id"}')
    content = content.replace('json={"question": question}', 'json={"question": question, "source_id": "demo-source-id"}')
    content = content.replace('json={"question": "How many students are in the database?"}', 'json={"question": "How many students are in the database?", "source_id": "demo-source-id"}')
    content = content.replace('json={"question": "Get students and courses."}', 'json={"question": "Get students and courses.", "source_id": "demo-source-id"}')
    content = content.replace('json={"question": "Drop the database."}', 'json={"question": "Drop the database.", "source_id": "demo-source-id"}')
    content = content.replace('json={"question": "Delete all students"}', 'json={"question": "Delete all students", "source_id": "demo-source-id"}')
    content = content.replace('json={"question": "how many students are there"}', 'json={"question": "how many students are there", "source_id": "demo-source-id"}')
    content = content.replace('json={"question": "list students named asdfghjklqwerty"}', 'json={"question": "list students named asdfghjklqwerty", "source_id": "demo-source-id"}')

    with open(filename, 'w') as f:
        f.write(content)

print('Updated test files')

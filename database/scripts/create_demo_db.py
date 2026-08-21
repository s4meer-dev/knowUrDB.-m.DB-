import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DB_DIR = BASE_DIR / "demo"
DB_PATH = DB_DIR / "knowurdb_demo.db"
SCHEMA_PATH = DB_DIR / "schema.sql"
SEED_SCRIPT = BASE_DIR / "scripts" / "seed_demo_db.py"
VALIDATE_SCRIPT = BASE_DIR / "scripts" / "validate_demo_db.py"

def run_command(cmd, desc):
    print(f"\n--- {desc} ---")
    result = subprocess.run(cmd, shell=True, text=True)
    if result.returncode != 0:
        print(f"FAILED: {desc}")
        sys.exit(1)

def main():
    print("Starting database creation process...")
    
    # 1. Remove existing DB
    if DB_PATH.exists():
        print(f"Removing existing database at {DB_PATH}")
        DB_PATH.unlink()
        
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    # 2. Create Schema
    print("Creating schema...")
    # Using python sqlite3 to run script instead of relying on sqlite3 CLI which might not be in PATH on windows
    import sqlite3
    with sqlite3.connect(DB_PATH) as conn:
        with open(SCHEMA_PATH, 'r') as f:
            conn.executescript(f.read())
    print("Schema created.")
    
    # 3. Seed Data
    run_command(f"{sys.executable} \"{SEED_SCRIPT}\"", "Seeding deterministic data")
    
    # 4. Validate Data
    run_command(f"{sys.executable} \"{VALIDATE_SCRIPT}\"", "Validating database")
    
    print("\nDatabase creation completed successfully!")

if __name__ == "__main__":
    main()

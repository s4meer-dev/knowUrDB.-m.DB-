import json
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / "database" / "demo" / "knowurdb_demo.db"
BENCHMARK_FILE = BASE_DIR / "tests" / "evaluation" / "benchmark_questions.json"

def main():
    print("Benchmark Validation")
    print("--------------------")
    
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        sys.exit(1)
        
    if not BENCHMARK_FILE.exists():
        print(f"Error: Benchmark file not found at {BENCHMARK_FILE}")
        sys.exit(1)
        
    with open(BENCHMARK_FILE, "r") as f:
        questions = json.load(f)
        
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    passed = 0
    failed = 0
    failures = []
    
    for q in questions:
        qid = q["id"]
        sql = q["expected_sql"]
        try:
            cur.execute(sql)
            # Fetch one to ensure execution actually produces something / works
            _ = cur.fetchone()
            print(f"{qid} PASS")
            passed += 1
        except Exception as e:
            print(f"{qid} FAIL: {e}")
            failed += 1
            failures.append((qid, sql, str(e)))
            
    conn.close()
    
    print("\nTotal:")
    print(passed + failed)
    print("\nPassed:")
    print(passed)
    print("\nFailed:")
    print(failed)
    
    if failed > 0:
        print("\nFailures:")
        for qid, sql, error in failures:
            print(f"- {qid}: {error} (SQL: {sql})")
        print("\nOverall:\nFAIL")
        sys.exit(1)
    else:
        print("\nOverall:\nPASS")

if __name__ == "__main__":
    main()

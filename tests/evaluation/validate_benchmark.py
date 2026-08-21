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
            results = cur.fetchall()
            
            def normalize_row(row):
                return tuple(round(val, 4) if isinstance(val, float) else val for val in row)
                
            normalized = [normalize_row(r) for r in results]
            if "ORDER BY" not in sql.upper():
                normalized.sort(key=lambda x: str(x))
                
            expected = [tuple(r) for r in q.get("expected_result", [])]
            
            if normalized == expected:
                print(f"{qid} | PASS | PASS | PASS")
                passed += 1
            else:
                print(f"{qid} | PASS | FAIL | FAIL")
                failed += 1
                failures.append((qid, sql, "Result mismatch"))
        except Exception as e:
            print(f"{qid} | FAIL | FAIL | FAIL ({e})")
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

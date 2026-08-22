import json
import sqlite3
import sys
from pathlib import Path

# Add project root to path so we can import app modules
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / 'backend'))

from app.services.text_to_sql_service import TextToSQLService
from app.services.schema_service import SchemaService
from app.core.database import demo_db_provider
from app.services.sql_validator import SQLValidator, SQLSafetyError

DB_PATH = BASE_DIR / "database" / "demo" / "knowurdb_demo.db"
BENCHMARK_FILE = BASE_DIR / "tests" / "evaluation" / "benchmark_questions.json"

def main():
    print("Phase 3 Text-to-SQL Benchmark Validation")
    print("----------------------------------------")
    
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
    
    schema_service = SchemaService(demo_db_provider)
    text_to_sql_service = TextToSQLService(schema_service)
    
    passed = 0
    failed = 0
    failures = []
    
    print("Question ID | Gen | Exec | Match")
    
    for q in questions:
        qid = q["id"]
        question_text = q["question"]
        expected_sql = q["expected_sql"]
        
        try:
            # 1. Generate SQL
            generated_sql = text_to_sql_service.translate(question_text)
            gen_status = "PASS"
            
            # 2. Validate SQL
            try:
                SQLValidator.validate(generated_sql)
            except SQLSafetyError as e:
                print(f"{qid} | FAIL | FAIL | FAIL (Unsafe: {e})")
                failed += 1
                failures.append((qid, question_text, str(e)))
                continue

            # 3. Execute SQL
            try:
                cur.execute(generated_sql)
                results = cur.fetchall()
                exec_status = "PASS"
                
                # 4. Compare Results
                def normalize_row(row):
                    return tuple(round(val, 4) if isinstance(val, float) else val for val in row)
                    
                normalized = [normalize_row(r) for r in results]
                if "ORDER BY" not in generated_sql.upper():
                    normalized.sort(key=lambda x: str(x))
                    
                expected = [tuple(r) for r in q.get("expected_result", [])]
                
                # We sort the expected if we didn't have order by in generated, just to be fair, 
                # but standard script sorts both if no ORDER BY in expected.
                # Actually, the standard script sorts normalized if ORDER BY not in *expected* sql. 
                # Let's align with that.
                if "ORDER BY" not in expected_sql.upper():
                    normalized.sort(key=lambda x: str(x))
                    expected.sort(key=lambda x: str(x))
                
                if normalized == expected:
                    match_status = "PASS"
                    passed += 1
                else:
                    match_status = "FAIL"
                    failed += 1
                    failures.append((qid, question_text, f"Result mismatch. Gen: {generated_sql}"))
                    
                print(f"{qid} | {gen_status} | {exec_status} | {match_status}")
                
            except Exception as e:
                print(f"{qid} | {gen_status} | FAIL | FAIL ({e})")
                failed += 1
                failures.append((qid, question_text, f"Exec Error: {e} | Gen: {generated_sql}"))
                
        except Exception as e:
            print(f"{qid} | FAIL | FAIL | FAIL ({e})")
            failed += 1
            failures.append((qid, question_text, f"Gen Error: {e}"))
            
    conn.close()
    
    print("\nTotal:")
    print(passed + failed)
    print("\nGenerated & Matched:")
    print(passed)
    print("\nFailed:")
    print(failed)
    
    if failed > 0:
        print("\nFailures:")
        for qid, qtext, error in failures:
            print(f"- {qid} ({qtext}): {error}")
        
    print(f"\nOverall Score: {passed}/{passed+failed}")

if __name__ == "__main__":
    main()

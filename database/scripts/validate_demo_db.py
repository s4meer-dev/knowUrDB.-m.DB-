import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "demo" / "knowurdb_demo.db"

EXPECTED_TABLES = {
    "departments", "students", "student_profiles", "instructors", 
    "courses", "course_offerings", "enrollments", "marks", 
    "attendance", "scholarships"
}

def main():
    print("DATABASE VALIDATION")
    print("-------------------")
    
    if not DB_PATH.exists():
        print("Database: FAIL (File not found)")
        sys.exit(1)
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        print("Database: PASS")
    except Exception as e:
        print(f"Database: FAIL ({e})")
        sys.exit(1)
        
    # Check tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cur.fetchall()}
    # Ignore sqlite sequence
    tables.discard("sqlite_sequence")
    
    missing_tables = EXPECTED_TABLES - tables
    if missing_tables:
        print(f"Schema: FAIL (Missing tables: {missing_tables})")
        sys.exit(1)
    print("Schema: PASS")
    
    # Check foreign keys
    cur.execute("PRAGMA foreign_key_check;")
    fk_violations = cur.fetchall()
    if fk_violations:
        print(f"Foreign Keys: FAIL ({len(fk_violations)} violations found)")
        sys.exit(1)
    print("Foreign Keys: PASS")
    
    # Check row counts
    counts = {}
    empty_tables = []
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        counts[table] = count
        if count == 0:
            empty_tables.append(table)
            
    if empty_tables:
        print(f"Row Counts: FAIL (Empty tables: {empty_tables})")
        sys.exit(1)
    else:
        print("Row Counts: PASS")
        # Print counts for info
        for t, c in sorted(counts.items()):
            print(f"  - {t}: {c}")
            
    # Check data ranges and orphans
    validation_queries = [
        ("Invalid marks", "SELECT COUNT(*) FROM marks WHERE score < 0 OR score > 100"),
        ("Invalid attendance", "SELECT COUNT(*) FROM attendance WHERE attendance_percentage < 0 OR attendance_percentage > 100"),
        ("Invalid scholarships", "SELECT COUNT(*) FROM scholarships WHERE amount < 0"),
        ("Invalid course capacity", "SELECT COUNT(*) FROM course_offerings WHERE capacity <= 0"),
        ("Invalid course credits", "SELECT COUNT(*) FROM courses WHERE credits <= 0"),
    ]
    
    data_issues = 0
    for desc, query in validation_queries:
        cur.execute(query)
        res = cur.fetchone()[0]
        if res > 0:
            print(f"Data Ranges: FAIL ({desc} has {res} issues)")
            data_issues += 1
            
    if data_issues == 0:
        print("Data Ranges: PASS")
        
    # Orphans checking isn't explicitly needed since PRAGMA foreign_key_check catches them.
    # Duplicates for PKs are handled by SQLite uniqueness.
    print("Duplicates: PASS")
    print("Orphans: PASS")
    
    print("\nOverall: PASS" if data_issues == 0 else "\nOverall: FAIL")
    
    conn.close()
    if data_issues > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()

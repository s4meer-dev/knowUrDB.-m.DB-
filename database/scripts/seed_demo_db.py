import sqlite3
import random
import datetime
import os
import math
from pathlib import Path

# Fixed seed for reproducibility
SEED = 42
random.seed(SEED)

# Database path
DB_PATH = Path(__file__).parent.parent / "demo" / "knowurdb_demo.db"

# Data scales
NUM_DEPARTMENTS = 12
NUM_STUDENTS = 4000
NUM_INSTRUCTORS = 200
NUM_COURSES = 150
NUM_OFFERINGS = 600

def get_connection():
    # Ensure directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def generate_departments(conn):
    names = [
        "Computer Science", "Mathematics", "Physics", "Chemistry", "Biology",
        "English", "History", "Philosophy", "Economics", "Psychology",
        "Sociology", "Political Science"
    ]
    random.shuffle(names)
    data = []
    for i in range(NUM_DEPARTMENTS):
        name = names[i]
        est_year = random.randint(1890, 1990)
        data.append((name, est_year))
    
    conn.executemany(
        "INSERT INTO departments (name, established_year) VALUES (?, ?)",
        data
    )
    print(f"Inserted {NUM_DEPARTMENTS} departments.")

def generate_instructors(conn):
    first_names = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Charles", "Joseph", "Thomas", "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
    titles = ["Professor", "Professor", "Associate Professor", "Assistant Professor", "Lecturer"]
    
    data = []
    for i in range(NUM_INSTRUCTORS):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        title = random.choice(titles)
        dept_id = random.randint(1, NUM_DEPARTMENTS)
        hire_year = random.randint(1995, 2023)
        data.append((fname, lname, title, dept_id, hire_year))
        
    conn.executemany(
        "INSERT INTO instructors (first_name, last_name, title, department_id, hire_year) VALUES (?, ?, ?, ?, ?)",
        data
    )
    print(f"Inserted {NUM_INSTRUCTORS} instructors.")

def generate_courses(conn):
    data = []
    course_codes_used = set()
    for i in range(NUM_COURSES):
        dept_id = random.randint(1, NUM_DEPARTMENTS)
        
        # generate a unique code
        while True:
            code_prefix = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=3))
            code_num = random.randint(100, 499)
            code = f"{code_prefix}{code_num}"
            if code not in course_codes_used:
                course_codes_used.add(code)
                break
        
        name = f"Introduction to {code}" if code_num < 200 else f"Advanced {code}"
        credits = random.choices([3, 4, 1, 2], weights=[70, 20, 5, 5])[0]
        data.append((code, name, credits, dept_id))
        
    conn.executemany(
        "INSERT INTO courses (course_code, name, credits, department_id) VALUES (?, ?, ?, ?)",
        data
    )
    print(f"Inserted {NUM_COURSES} courses.")

def generate_course_offerings(conn):
    data = []
    # Fetch instructor depts to match them correctly
    cur = conn.cursor()
    cur.execute("SELECT instructor_id, department_id FROM instructors")
    instructors_by_dept = {}
    for i_id, d_id in cur.fetchall():
        instructors_by_dept.setdefault(d_id, []).append(i_id)
        
    cur.execute("SELECT course_id, department_id FROM courses")
    courses_info = cur.fetchall()
    
    semesters = ["Fall", "Spring", "Summer"]
    
    for i in range(NUM_OFFERINGS):
        course_id, dept_id = random.choice(courses_info)
        # pick instructor from same dept or random if none
        if dept_id in instructors_by_dept and instructors_by_dept[dept_id]:
            instructor_id = random.choice(instructors_by_dept[dept_id])
        else:
            instructor_id = random.randint(1, NUM_INSTRUCTORS)
            
        semester = random.choices(semesters, weights=[45, 45, 10])[0]
        year = random.randint(2020, 2024)
        capacity = random.choices([30, 60, 150, 300], weights=[40, 40, 15, 5])[0]
        
        data.append((course_id, instructor_id, semester, year, capacity))
        
    conn.executemany(
        "INSERT INTO course_offerings (course_id, instructor_id, semester, academic_year, capacity) VALUES (?, ?, ?, ?, ?)",
        data
    )
    print(f"Inserted {NUM_OFFERINGS} course offerings.")

def generate_students(conn):
    first_names = ["Alex", "Jordan", "Taylor", "Casey", "Morgan", "Riley", "Cameron", "Quinn", "Avery", "Skyler", "Drew", "Jesse", "Sam", "Jamie", "Chris", "Pat", "Kelly", "Ashley", "Terry", "Tracy"]
    last_names = ["Evans", "Stone", "Roberts", "Walker", "Scott", "Phillips", "Campbell", "Parker", "Evans", "Edwards", "Collins", "Stewart", "Sanchez", "Morris", "Rogers", "Reed", "Cook", "Morgan", "Bell", "Murphy"]
    
    data_students = []
    data_profiles = []
    
    for i in range(1, NUM_STUDENTS + 1):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        # DOB between 1995 and 2005
        dob_year = random.randint(1995, 2005)
        dob_month = random.randint(1, 12)
        dob_day = random.randint(1, 28)
        dob = f"{dob_year}-{dob_month:02d}-{dob_day:02d}"
        
        enroll_year = dob_year + random.randint(17, 19)
        dept_id = random.randint(1, NUM_DEPARTMENTS)
        
        data_students.append((fname, lname, dob, enroll_year, dept_id))
        
        address = f"{random.randint(100, 9999)} {random.choice(['Main', 'Maple', 'Oak', 'Pine', 'Cedar'])} St"
        email = f"{fname.lower()}.{lname.lower()}{i}@university.edu"
        phone = f"555-{random.randint(100, 999):03d}-{random.randint(0, 9999):04d}"
        data_profiles.append((i, address, email, phone))
        
    conn.executemany(
        "INSERT INTO students (first_name, last_name, date_of_birth, enrollment_year, department_id) VALUES (?, ?, ?, ?, ?)",
        data_students
    )
    conn.executemany(
        "INSERT INTO student_profiles (student_id, address, email, phone_number) VALUES (?, ?, ?, ?)",
        data_profiles
    )
    print(f"Inserted {NUM_STUDENTS} students and profiles.")

def generate_enrollments_marks_attendance(conn):
    cur = conn.cursor()
    cur.execute("SELECT offering_id, capacity FROM course_offerings")
    offerings = cur.fetchall()
    
    enrollment_data = []
    marks_data = []
    attendance_data = []
    
    enrollment_id = 1
    total_enrollments = 0
    
    for offering_id, capacity in offerings:
        # Realistic enrollment count (between 5 and capacity)
        enrolled_count = random.randint(5, capacity)
        # Sample students
        enrolled_students = random.sample(range(1, NUM_STUDENTS + 1), enrolled_count)
        
        for student_id in enrolled_students:
            status = random.choices(["Enrolled", "Completed", "Dropped"], weights=[10, 85, 5])[0]
            enrollment_date = f"2023-08-{random.randint(1, 30):02d}"
            enrollment_data.append((student_id, offering_id, enrollment_date, status))
            
            # If not dropped, generate marks and attendance
            if status != "Dropped":
                # Attendance
                att_pct = min(100.0, max(0.0, random.normalvariate(85, 15)))
                attendance_data.append((enrollment_id, round(att_pct, 2), "2024-05-01"))
                
                # Marks
                # Midterm and Final
                midterm_score = min(100.0, max(0.0, random.normalvariate(75, 15)))
                final_score = min(100.0, max(0.0, random.normalvariate(75, 15)))
                
                marks_data.append((enrollment_id, "Midterm", round(midterm_score, 2)))
                marks_data.append((enrollment_id, "Final", round(final_score, 2)))
                
            enrollment_id += 1
            total_enrollments += 1

    conn.executemany(
        "INSERT INTO enrollments (student_id, offering_id, enrollment_date, status) VALUES (?, ?, ?, ?)",
        enrollment_data
    )
    conn.executemany(
        "INSERT INTO attendance (enrollment_id, attendance_percentage, last_updated) VALUES (?, ?, ?)",
        attendance_data
    )
    conn.executemany(
        "INSERT INTO marks (enrollment_id, assessment_name, score) VALUES (?, ?, ?)",
        marks_data
    )
    print(f"Inserted {total_enrollments} enrollments, plus corresponding marks and attendance.")

def generate_scholarships(conn):
    # About 10% of students get scholarships
    scholarship_students = random.sample(range(1, NUM_STUDENTS + 1), int(NUM_STUDENTS * 0.10))
    names = ["Merit Scholarship", "Need-based Grant", "Athletic Scholarship", "Dean's Excellence Award", "STEM Fellowship"]
    
    data = []
    for student_id in scholarship_students:
        name = random.choice(names)
        amount = random.choices([1000.0, 5000.0, 10000.0, 25000.0], weights=[50, 30, 15, 5])[0]
        awarded_year = random.randint(2020, 2024)
        data.append((student_id, name, amount, awarded_year))
        
    conn.executemany(
        "INSERT INTO scholarships (student_id, scholarship_name, amount, awarded_year) VALUES (?, ?, ?, ?)",
        data
    )
    print(f"Inserted {len(data)} scholarships.")

def main():
    print(f"Seeding database at {DB_PATH}")
    conn = get_connection()
    
    with conn:
        generate_departments(conn)
        generate_instructors(conn)
        generate_courses(conn)
        generate_course_offerings(conn)
        generate_students(conn)
        generate_enrollments_marks_attendance(conn)
        generate_scholarships(conn)
        
    conn.close()
    print("Database seeding completed.")

if __name__ == "__main__":
    main()

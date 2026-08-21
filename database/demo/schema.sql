-- knowUrDB Phase 2 Demo Database Schema
-- Domain: University / Campus Analytics

-- Enforce foreign key constraints
PRAGMA foreign_keys = ON;

-- 1. departments
CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    established_year INTEGER NOT NULL
);
-- Index for department name lookups
CREATE INDEX idx_departments_name ON departments(name);

-- 2. students
CREATE TABLE students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth DATE NOT NULL,
    enrollment_year INTEGER NOT NULL,
    department_id INTEGER NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE RESTRICT
);
-- Index for foreign key and common filters
CREATE INDEX idx_students_department ON students(department_id);
CREATE INDEX idx_students_enrollment_year ON students(enrollment_year);

-- 3. student_profiles (1-to-1 with students)
CREATE TABLE student_profiles (
    student_id INTEGER PRIMARY KEY,
    address TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone_number TEXT,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

-- 4. instructors
CREATE TABLE instructors (
    instructor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    title TEXT NOT NULL, -- e.g., 'Professor', 'Associate Professor', 'Lecturer'
    department_id INTEGER NOT NULL,
    hire_year INTEGER NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE RESTRICT
);
CREATE INDEX idx_instructors_department ON instructors(department_id);

-- 5. courses
CREATE TABLE courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL UNIQUE, -- e.g., 'CS101'
    name TEXT NOT NULL,
    credits INTEGER NOT NULL CHECK (credits > 0),
    department_id INTEGER NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE RESTRICT
);
CREATE INDEX idx_courses_department ON courses(department_id);

-- 6. course_offerings
CREATE TABLE course_offerings (
    offering_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    instructor_id INTEGER NOT NULL,
    semester TEXT NOT NULL, -- e.g., 'Fall', 'Spring'
    academic_year INTEGER NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE RESTRICT,
    FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id) ON DELETE RESTRICT
);
CREATE INDEX idx_course_offerings_course ON course_offerings(course_id);
CREATE INDEX idx_course_offerings_instructor ON course_offerings(instructor_id);
CREATE INDEX idx_course_offerings_term ON course_offerings(academic_year, semester);

-- 7. enrollments
CREATE TABLE enrollments (
    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    offering_id INTEGER NOT NULL,
    enrollment_date DATE NOT NULL,
    status TEXT NOT NULL, -- 'Enrolled', 'Dropped', 'Completed'
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (offering_id) REFERENCES course_offerings(offering_id) ON DELETE RESTRICT,
    UNIQUE (student_id, offering_id) -- A student can only enroll in a specific offering once
);
CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_enrollments_offering ON enrollments(offering_id);

-- 8. marks
CREATE TABLE marks (
    mark_id INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id INTEGER NOT NULL,
    assessment_name TEXT NOT NULL, -- e.g., 'Midterm', 'Final', 'Assignment 1'
    score REAL NOT NULL CHECK (score >= 0 AND score <= 100),
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id) ON DELETE CASCADE
);
CREATE INDEX idx_marks_enrollment ON marks(enrollment_id);

-- 9. attendance
CREATE TABLE attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id INTEGER NOT NULL UNIQUE, -- 1-to-1 with enrollment for this aggregate model
    attendance_percentage REAL NOT NULL CHECK (attendance_percentage >= 0 AND attendance_percentage <= 100),
    last_updated DATE NOT NULL,
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id) ON DELETE CASCADE
);

-- 10. scholarships
CREATE TABLE scholarships (
    scholarship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    scholarship_name TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount >= 0),
    awarded_year INTEGER NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);
CREATE INDEX idx_scholarships_student ON scholarships(student_id);
CREATE INDEX idx_scholarships_awarded_year ON scholarships(awarded_year);

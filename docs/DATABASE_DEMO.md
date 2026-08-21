# Phase 2 Demo Database
## Domain: University / Campus Analytics

This document describes the structure and validation of the knowUrDB Demo Database used for evaluation.

## Purpose
The demo database serves as a completely deterministic, realistic, SQLite-based benchmark for evaluating the knowUrDB Text-to-SQL engine. It simulates an academic environment with complex relationships, realistic constraints, and meaningful data volume.

## Schema Architecture
The database consists of 10 tables:

1. **departments**: Academic departments (e.g., Computer Science, Mathematics).
2. **students**: Core student records, linked to departments.
3. **student_profiles**: Detailed student information (1-to-1 with students).
4. **instructors**: Faculty members linked to departments.
5. **courses**: Course catalog entries.
6. **course_offerings**: Instances of courses taught in specific semesters by instructors.
7. **enrollments**: Students enrolled in course offerings.
8. **marks**: Assessment scores for enrolled students.
9. **attendance**: Aggregate attendance percentage for enrollments.
10. **scholarships**: Financial awards given to students.

### Relationship Highlights
- `department_id` is the core organizational link for students, instructors, and courses.
- A `course_offering` maps a `course` to an `instructor` for a specific semester/year.
- An `enrollment` maps a `student` to a `course_offering`.
- `marks` and `attendance` are dependent on `enrollments`.

### Constraints & Integrity
- All tables use `INTEGER PRIMARY KEY AUTOINCREMENT` (except `student_profiles`, which shares the PK with `students`).
- Foreign keys are explicitly defined and `PRAGMA foreign_keys = ON;` is enforced.
- Value constraints (e.g., `score >= 0 AND score <= 100`, `credits > 0`) guarantee valid analytic outputs.

## Deterministic Data Generation
- **Script**: `database/scripts/seed_demo_db.py`
- **Seed**: `42`
- **Scale**:
  - Departments: 12
  - Students & Profiles: 4,000
  - Instructors: 200
  - Courses: 150
  - Course Offerings: 600
  - Enrollments: ~24,000
  - Marks: ~48,000
  - Attendance: ~24,000
  - Scholarships: ~400
- **Characteristics**: Realistic distribution (e.g., only 10% of students get scholarships; varying course capacities; normal distributions for grades).

## Validation Scripts
- `database/scripts/validate_demo_db.py` performs assertions on foreign key integrity, table existence, row counts, data ranges, and absence of orphans.

## Benchmark Dataset
- `tests/evaluation/benchmark_questions.json` contains 50 ground-truth Text-to-SQL questions, validated against this demo database schema.
- **Difficulty Distribution**: Easy (15), Medium (15), Hard (15), Expert (5).
- **Validation**: `tests/evaluation/validate_benchmark.py` ensures all queries execute successfully.

## Security Note
This database contains **entirely synthetic data**. No real personal data, credentials, API keys, or production connections are used or stored.

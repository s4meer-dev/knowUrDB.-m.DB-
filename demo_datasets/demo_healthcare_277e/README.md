# Healthcare Intelligence (`demo_healthcare_277e`)

> **Domain**: `healthcare` | **Source Type**: `MongoDB` | **Total Documents**: `585` | **Collections**: `5`

Synthetic hospital operations dataset containing patients, doctors, appointments, prescriptions, and laboratory results.

## MongoDB Runtime & Filesystem Snapshot

- **MongoDB Database**: `demo_healthcare_277e` (`mongodb://127.0.0.1:27017/demo_healthcare_277e`)
- **Filesystem Snapshot Path**: `demo_datasets/demo_healthcare_277e`
- **Content Hash**: `sha256:18df5651052a948600ff3b86`
- **Generated At**: `2026-09-25T07:32:15.662388+00:00`

## Collections & JSONL Snapshots

| Collection | Documents | Snapshot File | Key Indexed Fields |
| :--- | ---: | :--- | :--- |
| `patients` | 105 | `collections/patients.jsonl` | `_id`, `patient_id`, `name`, `age`, `gender`, `blood_group` |
| `doctors` | 29 | `collections/doctors.jsonl` | `_id`, `doctor_id`, `name`, `specialty`, `department`, `city` |
| `appointments` | 158 | `collections/appointments.jsonl` | `_id`, `appointment_id`, `patient_id`, `patient_name`, `doctor_id`, `doctor_name` |
| `prescriptions` | 168 | `collections/prescriptions.jsonl` | `_id`, `prescription_id`, `patient_id`, `doctor_id`, `medication`, `dosage_mg` |
| `lab_results` | 125 | `collections/lab_results.jsonl` | `_id`, `lab_id`, `patient_id`, `patient_name`, `test_name`, `result_value` |

## Directory Structure

```text
demo_healthcare_277e/
├── manifest.json
├── metadata.json
├── schema.json
├── README.md
└── collections/
    ├── patients.jsonl
    ├── doctors.jsonl
    ├── appointments.jsonl
    ├── prescriptions.jsonl
    └── lab_results.jsonl
```

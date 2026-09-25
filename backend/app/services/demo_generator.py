import datetime
import json
import logging
import random
import secrets
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from bson import ObjectId

from app.core.mongodb import MongoDBManager
from app.models.source import SourceMetadata, SourceStatus
from app.services.dataset_exporter import MongoDatasetExporter, resolve_dataset_root

logger = logging.getLogger("knowurdb.demo_generator")

_generation_lock = threading.Lock()

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Diya", "Ananya", "Rohan", "Sneha", "Kabir",
    "Meera", "Vikram", "Priya", "Karan", "Ishaan", "Neha", "Siddharth", "Tanvi",
    "Arjun", "Kavya", "Dev", "Riya", "Nikhil", "Pooja", "Rahul", "Sanya",
]

LAST_NAMES = [
    "Sharma", "Patel", "Verma", "Iyer", "Reddy", "Nair", "Kapoor", "Malhotra",
    "Joshi", "Gupta", "Mehta", "Rao", "Chatterjee", "Deshmukh", "Kulkarni", "Bhatia",
]

CITIES = [
    ("Bengaluru", "Karnataka"),
    ("Mumbai", "Maharashtra"),
    ("Delhi", "NCR"),
    ("Hyderabad", "Telangana"),
    ("Pune", "Maharashtra"),
    ("Chennai", "Tamil Nadu"),
    ("Ahmedabad", "Gujarat"),
    ("Kolkata", "West Bengal"),
]

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August"]


DOMAIN_CATALOG: dict[str, dict[str, Any]] = {
    "healthcare": {
        "display_names": [
            "Healthcare Intelligence",
            "Healthcare Clinical Network",
            "Healthcare Diagnostics Hub",
        ],
        "description": "Synthetic hospital operations dataset containing patients, doctors, appointments, diagnoses, and medications.",
        "collections": ["patients", "doctors", "appointments", "diagnoses", "medications"],
    },
    "finance": {
        "display_names": [
            "Financial Operations",
            "Capital & Wealth Analytics",
            "Treasury & Ledger Intelligence",
        ],
        "description": "Synthetic financial operations dataset containing customers, accounts, transactions, investments, and branches.",
        "collections": ["customers", "accounts", "transactions", "investments", "branches"],
    },
    "logistics": {
        "display_names": [
            "Logistics Network",
            "Supply Chain & Fleet Intelligence",
            "Global Freight Analytics",
        ],
        "description": "Synthetic logistics and freight dataset containing shipments, vehicles, drivers, warehouses, and deliveries.",
        "collections": ["shipments", "vehicles", "drivers", "warehouses", "deliveries"],
    },
    "education": {
        "display_names": [
            "Education Analytics",
            "University Academic Intelligence",
            "Campus Learning Operations",
        ],
        "description": "Synthetic academic dataset containing students, courses, instructors, enrollments, and exams.",
        "collections": ["students", "courses", "instructors", "enrollments", "exams"],
    },
    "ecommerce": {
        "display_names": [
            "E-Commerce Marketplace",
            "Digital Commerce Analytics",
            "Direct-to-Consumer Storefront",
        ],
        "description": "Synthetic e-commerce marketplace dataset containing shoppers, catalog_items, carts, orders, and reviews.",
        "collections": ["shoppers", "catalog_items", "carts", "orders", "reviews"],
    },
    "enterprise": {
        "display_names": [
            "Enterprise Operations",
            "Corporate Resource Intelligence",
            "B2B Commercial Suite",
        ],
        "description": "Synthetic enterprise dataset containing customers, products, orders, employees, and departments.",
        "collections": ["customers", "products", "orders", "employees", "departments"],
    },
    "travel": {
        "display_names": [
            "Global Travel & Aviation",
            "Airline Operations Intelligence",
            "Passenger Mobility Analytics",
        ],
        "description": "Synthetic aviation and travel dataset containing passengers, flights, bookings, airports, and loyalty_accounts.",
        "collections": ["passengers", "flights", "bookings", "airports", "loyalty_accounts"],
    },
    "hospitality": {
        "display_names": [
            "Hospitality & Resort Management",
            "Luxury Hotel Group Analytics",
            "Guest Experience Intelligence",
        ],
        "description": "Synthetic hospitality dataset containing guests, hotels, rooms, reservations, and concierge_services.",
        "collections": ["guests", "hotels", "rooms", "reservations", "concierge_services"],
    },
    "manufacturing": {
        "display_names": [
            "Smart Manufacturing & IoT",
            "Industrial Production Intelligence",
            "Factory Automation Analytics",
        ],
        "description": "Synthetic manufacturing dataset containing factories, production_lines, work_orders, quality_inspections, and inventory_parts.",
        "collections": ["factories", "production_lines", "work_orders", "quality_inspections", "inventory_parts"],
    },
    "telecom": {
        "display_names": [
            "Telecommunications Network",
            "5G Carrier Intelligence",
            "Subscriber & Spectrum Analytics",
        ],
        "description": "Synthetic telecom network dataset containing subscribers, cell_towers, data_plans, call_records, and network_incidents.",
        "collections": ["subscribers", "cell_towers", "data_plans", "call_records", "network_incidents"],
    },
    "realestate": {
        "display_names": [
            "Real Estate Portfolio",
            "Commercial Property Intelligence",
            "Urban Housing & Lease Analytics",
        ],
        "description": "Synthetic real estate dataset containing properties, agents, buyers, leases, and maintenance_requests.",
        "collections": ["properties", "agents", "buyers", "leases", "maintenance_requests"],
    },
    "sports": {
        "display_names": [
            "Sports League Analytics",
            "Pro Athlete Performance Hub",
            "Championship Tournament Data",
        ],
        "description": "Synthetic sports analytics dataset containing athletes, teams, matches, training_sessions, and sponsorships.",
        "collections": ["athletes", "teams", "matches", "training_sessions", "sponsorships"],
    },
    "fooddelivery": {
        "display_names": [
            "Hyperlocal Food Delivery",
            "Cloud Kitchen & Courier Hub",
            "Quick-Commerce Meal Network",
        ],
        "description": "Synthetic food delivery dataset containing restaurants, couriers, menu_items, delivery_orders, and ratings.",
        "collections": ["restaurants", "couriers", "menu_items", "delivery_orders", "ratings"],
    },
    "automotive": {
        "display_names": [
            "Connected Fleet & EV Telemetry",
            "Autonomous Mobility Analytics",
            "EV Charging & Service Network",
        ],
        "description": "Synthetic automotive and EV dataset containing vehicles, charging_stations, service_records, dealers, and telemetry_logs.",
        "collections": ["vehicles", "charging_stations", "service_records", "dealers", "telemetry_logs"],
    },
    "energy": {
        "display_names": [
            "Renewable Energy Grid",
            "Smart Utility & Solar Analytics",
            "Power Grid Telemetry Hub",
        ],
        "description": "Synthetic energy grid dataset containing power_plants, smart_meters, grid_substations, energy_readings, and outage_events.",
        "collections": ["power_plants", "smart_meters", "grid_substations", "energy_readings", "outage_events"],
    },
    "hr": {
        "display_names": [
            "Workforce & Talent Intelligence",
            "People Operations Analytics",
            "Global Talent & Payroll Hub",
        ],
        "description": "Synthetic HR and talent dataset containing employees, candidates, job_requisitions, performance_reviews, and payroll_runs.",
        "collections": ["employees", "candidates", "job_requisitions", "performance_reviews", "payroll_runs"],
    },
    "social": {
        "display_names": [
            "Creator & Social Platform",
            "Social Graph & Engagement Hub",
            "Digital Community Intelligence",
        ],
        "description": "Synthetic social platform dataset containing creators, posts, communities, engagements, and ad_campaigns.",
        "collections": ["creators", "posts", "communities", "engagements", "ad_campaigns"],
    },
    "media": {
        "display_names": [
            "Media & Streaming Analytics",
            "OTT Content & Audience Hub",
            "Cinema & Subscription Intelligence",
        ],
        "description": "Synthetic streaming media dataset containing titles, viewers, watch_sessions, subscriptions, and royalties.",
        "collections": ["titles", "viewers", "watch_sessions", "subscriptions", "royalties"],
    },
    "banking": {
        "display_names": [
            "Commercial Banking Hub",
            "Retail Credit & Loan Analytics",
            "Core Banking & Wire Intelligence",
        ],
        "description": "Synthetic banking dataset containing clients, loan_accounts, credit_cards, wire_transfers, and risk_assessments.",
        "collections": ["clients", "loan_accounts", "credit_cards", "wire_transfers", "risk_assessments"],
    },
    "retail": {
        "display_names": [
            "Omnichannel Retail Operations",
            "Storefront & POS Intelligence",
            "Retail Inventory & Loyalty Hub",
        ],
        "description": "Synthetic retail store dataset containing stores, skus, pos_transactions, suppliers, and loyalty_members.",
        "collections": ["stores", "skus", "pos_transactions", "suppliers", "loyalty_members"],
    },
}


class RandomDatasetEngine:
    """
    Production-grade synthetic MongoDB dataset factory capable of creating unlimited
    independent, domain-specific, relationally consistent MongoDB databases.
    """

    GENERATOR_VERSION = "2.0.0"
    TEMPLATE_VERSION = "1.0"

    def __init__(self, manifest_root: Path | None = None):
        abs_root, _rel_root = resolve_dataset_root(manifest_root)
        self.manifest_root = abs_root

    def select_domain(self, preferred_domain: str | None = None) -> tuple[str, str, dict[str, Any]]:
        """
        Selects a domain from the 20-domain catalog, avoiding recently generated domains
        so repeated clicks always produce diverse domains and display names.
        """
        sys_db = MongoDBManager.get_db()
        existing_sources = list(
            sys_db[MongoDBManager.SYS_SOURCES].find(
                {"source_category": "mongodb"},
                {"domain": 1, "display_name": 1, "name": 1, "uploaded_at": 1},
            )
        )
        used_domains = [s.get("domain") for s in existing_sources if s.get("domain")]
        used_names = {s.get("display_name") or s.get("name") for s in existing_sources}

        all_domains = list(DOMAIN_CATALOG.keys())
        sys_rng = random.SystemRandom()

        if preferred_domain and preferred_domain in DOMAIN_CATALOG:
            chosen_domain = preferred_domain
        else:
            # Prefer domains not yet used, or not used in the last 8 generations
            recent_domains = set(used_domains[-8:])
            unused = [d for d in all_domains if d not in used_domains]
            non_recent = [d for d in all_domains if d not in recent_domains]
            if unused:
                chosen_domain = sys_rng.choice(unused)
            elif non_recent:
                chosen_domain = sys_rng.choice(non_recent)
            else:
                chosen_domain = sys_rng.choice(all_domains)

        spec = DOMAIN_CATALOG[chosen_domain]
        candidate_titles = spec["display_names"]
        chosen_title = next((t for t in candidate_titles if t not in used_names), None)
        if not chosen_title:
            suffix_code = secrets.token_hex(2).upper()
            chosen_title = f"{candidate_titles[0]} #{suffix_code}"

        return chosen_domain, chosen_title, spec

    def allocate_unique_database_name(self, domain: str) -> str:
        """
        Generates a unique MongoDB database name `demo_<domain>_<short_unique_id>`
        with collision protection against existing MongoDB databases, `_sys_sources`, and manifests.
        """
        client = MongoDBManager.get_client()
        sys_db = MongoDBManager.get_db()
        try:
            existing_dbs = set(client.list_database_names())
        except Exception:
            existing_dbs = set()

        existing_src_dbs = {
            s.get("database_name")
            for s in sys_db[MongoDBManager.SYS_SOURCES].find({}, {"database_name": 1})
            if s.get("database_name")
        }

        clean_domain = "".join(ch for ch in domain.lower() if ch.isalnum())[:14]
        for _ in range(50):
            short_id = secrets.token_hex(2)  # 4 hex chars, e.g. 'a81f'
            candidate = f"demo_{clean_domain}_{short_id}"
            manifest_dir = self.manifest_root / candidate
            if (
                candidate not in existing_dbs
                and candidate not in existing_src_dbs
                and not manifest_dir.exists()
            ):
                return candidate

        return f"demo_{clean_domain}_{secrets.token_hex(4)}"

    def generate_domain_collections(
        self, domain: str, seed_int: int
    ) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, str]], dict[str, list[str]]]:
        """
        Generates 5 relationally consistent collections with rich BSON types (ObjectId, Date,
        Double, Int64, Boolean, embedded Objects, and Arrays) for any of the 20 domains.
        """
        rng = random.Random(seed_int)
        now = datetime.datetime.now(datetime.UTC)

        def rand_person() -> tuple[str, str, str]:
            fn = rng.choice(FIRST_NAMES)
            ln = rng.choice(LAST_NAMES)
            return fn, ln, f"{fn} {ln}"

        def rand_date(days_back: int = 365) -> datetime.datetime:
            delta = datetime.timedelta(
                days=rng.randint(1, days_back),
                hours=rng.randint(0, 23),
                minutes=rng.randint(0, 59),
            )
            return now - delta

        if domain == "healthcare":
            n_docs = rng.randint(25, 40)
            n_pats = rng.randint(90, 160)
            n_appts = rng.randint(140, 240)
            n_rx = rng.randint(110, 180)
            n_labs = rng.randint(100, 170)

            specialties = ["Cardiology", "Neurology", "Oncology", "Orthopedics", "Pediatrics", "Dermatology", "General Medicine"]
            diagnoses = ["Hypertension", "Type 2 Diabetes", "Migraine Syndrome", "Seasonal Influenza", "Osteoarthritis", "Bronchitis", "Arrhythmia"]
            medications = ["Atorvastatin 20mg", "Metformin 500mg", "Lisinopril 10mg", "Amoxicillin 500mg", "Azithromycin 250mg", "Omeprazole 40mg"]
            blood_groups = ["O+", "A+", "B+", "AB+", "O-", "A-", "B-"]
            lab_tests = ["Complete Blood Count", "Lipid Panel", "HbA1c Assay", "Thyroid Panel", "Liver Function Test", "Electrolyte Panel"]

            doctors = []
            for i in range(1, n_docs + 1):
                _, _, full = rand_person()
                city, state = rng.choice(CITIES)
                spec = rng.choice(specialties)
                doctors.append({
                    "_id": ObjectId(),
                    "doctor_id": f"DOC-{i:03d}",
                    "name": f"Dr. {full}",
                    "specialty": spec,
                    "department": spec,
                    "city": city,
                    "consultation_fee": round(rng.uniform(600.0, 2800.0), 2),
                    "experience_years": rng.randint(3, 28),
                    "rating": round(rng.uniform(4.1, 5.0), 2),
                    "available": rng.choice([True, True, True, False]),
                    "joined_at": rand_date(1500),
                })

            patients = []
            for i in range(1, n_pats + 1):
                fn, ln, full = rand_person()
                city, state = rng.choice(CITIES)
                patients.append({
                    "_id": ObjectId(),
                    "patient_id": f"PAT-{i:04d}",
                    "name": full,
                    "age": rng.randint(18, 84),
                    "gender": rng.choice(["Female", "Male"]),
                    "blood_group": rng.choice(blood_groups),
                    "city": city,
                    "primary_diagnosis": rng.choice(diagnoses),
                    "total_billed": round(rng.uniform(3500.0, 185000.0), 2),
                    "address": {"city": city, "state": state, "country": "India"},
                    "contact": {"email": f"{fn.lower()}.{ln.lower()}{i}@healthdemo.org"},
                    "vitals": {
                        "systolic_bp": rng.randint(110, 155),
                        "heart_rate": rng.randint(62, 98),
                        "spo2": rng.randint(95, 100),
                    },
                    "allergies": rng.sample(["Penicillin", "Pollen", "Sulfa", "Latex", "None"], k=rng.randint(1, 2)),
                    "registered_at": rand_date(720),
                })

            appointments = []
            for i in range(1, n_appts + 1):
                pat = rng.choice(patients)
                doc = rng.choice(doctors)
                dt = rand_date(180)
                appointments.append({
                    "_id": ObjectId(),
                    "appointment_id": f"APT-{i:04d}",
                    "patient_id": pat["patient_id"],
                    "patient_name": pat["name"],
                    "doctor_id": doc["doctor_id"],
                    "doctor_name": doc["name"],
                    "department": doc["specialty"],
                    "diagnosis": pat["primary_diagnosis"],
                    "status": rng.choice(["completed", "completed", "scheduled", "cancelled"]),
                    "fee": doc["consultation_fee"],
                    "month": MONTHS[dt.month % len(MONTHS)],
                    "appointment_date": dt,
                })

            prescriptions = []
            for i in range(1, n_rx + 1):
                pat = rng.choice(patients)
                doc = rng.choice(doctors)
                med = rng.choice(medications)
                prescriptions.append({
                    "_id": ObjectId(),
                    "prescription_id": f"RX-{i:04d}",
                    "patient_id": pat["patient_id"],
                    "doctor_id": doc["doctor_id"],
                    "medication": med,
                    "dosage_mg": rng.choice([10, 20, 40, 250, 500]),
                    "duration_days": rng.choice([5, 7, 14, 30, 60]),
                    "cost": round(rng.uniform(180.0, 4200.0), 2),
                    "refills_allowed": rng.randint(0, 3),
                    "prescribed_at": rand_date(180),
                })

            lab_results = []
            for i in range(1, n_labs + 1):
                pat = rng.choice(patients)
                tname = rng.choice(lab_tests)
                lab_results.append({
                    "_id": ObjectId(),
                    "lab_id": f"LAB-{i:04d}",
                    "patient_id": pat["patient_id"],
                    "patient_name": pat["name"],
                    "test_name": tname,
                    "result_value": round(rng.uniform(4.2, 195.0), 2),
                    "status": rng.choice(["normal", "normal", "elevated", "critical"]),
                    "lab_charge": round(rng.uniform(450.0, 5500.0), 2),
                    "tested_at": rand_date(180),
                })

            cols = {
                "patients": patients,
                "doctors": doctors,
                "appointments": appointments,
                "diagnoses": lab_results,
                "medications": prescriptions,
            }
            rels = [
                {"from": "appointments.patient_id", "to": "patients.patient_id"},
                {"from": "appointments.doctor_id", "to": "doctors.doctor_id"},
                {"from": "diagnoses.patient_id", "to": "patients.patient_id"},
                {"from": "medications.patient_id", "to": "patients.patient_id"},
            ]
            idxs = {
                "patients": ["patient_id", "city", "primary_diagnosis"],
                "doctors": ["doctor_id", "specialty"],
                "appointments": ["appointment_id", "patient_id", "doctor_id", "status"],
                "diagnoses": ["lab_id", "patient_id", "status"],
                "medications": ["prescription_id", "patient_id", "doctor_id"],
            }
            return cols, rels, idxs

        if domain == "finance":
            n_branches = rng.randint(18, 28)
            n_cust = rng.randint(85, 140)
            n_acct = rng.randint(120, 190)
            n_tx = rng.randint(180, 280)
            n_inv = rng.randint(75, 125)

            branches = []
            for i in range(1, n_branches + 1):
                city, state = rng.choice(CITIES)
                branches.append({
                    "_id": ObjectId(),
                    "branch_id": f"BRN-{i:03d}",
                    "name": f"{city} Financial Center #{i}",
                    "city": city,
                    "state": state,
                    "assets_under_management": round(rng.uniform(25_000_000.0, 450_000_000.0), 2),
                    "staff_count": rng.randint(15, 95),
                })

            customers = []
            for i in range(1, n_cust + 1):
                fn, ln, full = rand_person()
                city, state = rng.choice(CITIES)
                br = rng.choice(branches)
                customers.append({
                    "_id": ObjectId(),
                    "customer_id": f"FIN-CUST-{i:04d}",
                    "name": full,
                    "segment": rng.choice(["Private Wealth", "Corporate", "Premier", "Retail"]),
                    "credit_score": rng.randint(640, 845),
                    "city": city,
                    "branch_id": br["branch_id"],
                    "net_worth": round(rng.uniform(150000.0, 12500000.0), 2),
                    "contact": {"email": f"{fn.lower()}.{ln.lower()}{i}@financedemo.com"},
                    "onboarded_at": rand_date(900),
                })

            accounts = []
            for i in range(1, n_acct + 1):
                cust = rng.choice(customers)
                accounts.append({
                    "_id": ObjectId(),
                    "account_number": f"ACCT-{100000 + i}",
                    "customer_id": cust["customer_id"],
                    "customer_name": cust["name"],
                    "branch_id": cust["branch_id"],
                    "account_type": rng.choice(["Savings", "Checking", "Money Market", "Treasury"]),
                    "balance": round(rng.uniform(12000.0, 2450000.0), 2),
                    "currency": "INR",
                    "status": rng.choice(["active", "active", "active", "frozen"]),
                    "opened_at": rand_date(800),
                })

            transactions = []
            for i in range(1, n_tx + 1):
                acct = rng.choice(accounts)
                dt = rand_date(180)
                transactions.append({
                    "_id": ObjectId(),
                    "transaction_id": f"TXN-{i:05d}",
                    "account_number": acct["account_number"],
                    "customer_id": acct["customer_id"],
                    "branch_id": acct["branch_id"],
                    "transaction_type": rng.choice(["credit", "debit", "wire_transfer", "dividend"]),
                    "category": rng.choice(["Payroll", "Equities", "Vendor Settlement", "Advisory Fee", "Treasury Yield"]),
                    "amount": round(rng.uniform(1500.0, 385000.0), 2),
                    "status": rng.choice(["settled", "settled", "pending", "flagged"]),
                    "month": MONTHS[dt.month % len(MONTHS)],
                    "timestamp": dt,
                })

            investments = []
            for i in range(1, n_inv + 1):
                cust = rng.choice(customers)
                investments.append({
                    "_id": ObjectId(),
                    "investment_id": f"INV-{i:04d}",
                    "customer_id": cust["customer_id"],
                    "customer_name": cust["name"],
                    "asset_class": rng.choice(["Index ETF", "Sovereign Bond", "Bluechip Equity", "Private Credit", "REIT"]),
                    "principal": round(rng.uniform(50000.0, 1500000.0), 2),
                    "current_value": round(rng.uniform(58000.0, 1850000.0), 2),
                    "annual_return_pct": round(rng.uniform(5.5, 21.8), 2),
                    "maturity_date": rand_date(365),
                })

            cols = {
                "customers": customers,
                "accounts": accounts,
                "transactions": transactions,
                "investments": investments,
                "branches": branches,
            }
            rels = [
                {"from": "accounts.customer_id", "to": "customers.customer_id"},
                {"from": "transactions.customer_id", "to": "customers.customer_id"},
                {"from": "investments.customer_id", "to": "customers.customer_id"},
                {"from": "customers.branch_id", "to": "branches.branch_id"},
            ]
            idxs = {
                "customers": ["customer_id", "segment", "city"],
                "accounts": ["account_number", "customer_id", "account_type"],
                "transactions": ["transaction_id", "account_number", "customer_id", "transaction_type"],
                "investments": ["investment_id", "customer_id", "asset_class"],
                "branches": ["branch_id", "city"],
            }
            return cols, rels, idxs

        if domain == "logistics":
            n_wh = rng.randint(16, 26)
            n_veh = rng.randint(35, 60)
            n_drv = rng.randint(45, 75)
            n_ship = rng.randint(130, 210)
            n_del = rng.randint(120, 195)

            warehouses = []
            for i in range(1, n_wh + 1):
                city, state = rng.choice(CITIES)
                warehouses.append({
                    "_id": ObjectId(),
                    "warehouse_id": f"WH-{i:03d}",
                    "name": f"{city} Fulfillment Hub #{i}",
                    "city": city,
                    "state": state,
                    "capacity_pallets": rng.randint(2500, 18000),
                    "utilization_pct": round(rng.uniform(58.0, 96.5), 1),
                })

            vehicles = []
            for i in range(1, n_veh + 1):
                wh = rng.choice(warehouses)
                vehicles.append({
                    "_id": ObjectId(),
                    "vehicle_id": f"VEH-{i:03d}",
                    "registration": f"KA-{rng.randint(10, 99)}-LG-{1000 + i}",
                    "vehicle_type": rng.choice(["Heavy Freight Truck", "Refrigerated Van", "Electric Cargo Van", "Container Trailer"]),
                    "warehouse_id": wh["warehouse_id"],
                    "payload_capacity_kg": rng.choice([2500, 5000, 12000, 24000]),
                    "status": rng.choice(["in_transit", "available", "maintenance"]),
                })

            drivers = []
            for i in range(1, n_drv + 1):
                _, _, full = rand_person()
                veh = rng.choice(vehicles)
                drivers.append({
                    "_id": ObjectId(),
                    "driver_id": f"DRV-{i:03d}",
                    "name": full,
                    "vehicle_id": veh["vehicle_id"],
                    "warehouse_id": veh["warehouse_id"],
                    "safety_score": round(rng.uniform(86.0, 99.9), 1),
                    "completed_trips": rng.randint(40, 620),
                })

            shipments = []
            for i in range(1, n_ship + 1):
                wh = rng.choice(warehouses)
                drv = rng.choice(drivers)
                dest_city, _ = rng.choice(CITIES)
                shipments.append({
                    "_id": ObjectId(),
                    "shipment_id": f"SHP-{i:05d}",
                    "tracking_code": f"TRK-{secrets.token_hex(3).upper()}",
                    "warehouse_id": wh["warehouse_id"],
                    "driver_id": drv["driver_id"],
                    "origin_city": wh["city"],
                    "destination_city": dest_city,
                    "weight_kg": round(rng.uniform(25.0, 4800.0), 1),
                    "shipping_cost": round(rng.uniform(1200.0, 68000.0), 2),
                    "status": rng.choice(["delivered", "in_transit", "customs_clearance", "delayed"]),
                    "dispatched_at": rand_date(150),
                })

            deliveries = []
            for i in range(1, n_del + 1):
                shp = rng.choice(shipments)
                deliveries.append({
                    "_id": ObjectId(),
                    "delivery_id": f"DEL-{i:05d}",
                    "shipment_id": shp["shipment_id"],
                    "driver_id": shp["driver_id"],
                    "destination_city": shp["destination_city"],
                    "delivery_time_hours": round(rng.uniform(4.5, 72.0), 1),
                    "on_time": rng.choice([True, True, True, False]),
                    "recipient_rating": round(rng.uniform(3.8, 5.0), 1),
                    "delivered_at": rand_date(120),
                })

            cols = {
                "shipments": shipments,
                "vehicles": vehicles,
                "drivers": drivers,
                "warehouses": warehouses,
                "deliveries": deliveries,
            }
            rels = [
                {"from": "shipments.warehouse_id", "to": "warehouses.warehouse_id"},
                {"from": "shipments.driver_id", "to": "drivers.driver_id"},
                {"from": "deliveries.shipment_id", "to": "shipments.shipment_id"},
            ]
            idxs = {
                "shipments": ["shipment_id", "warehouse_id", "driver_id", "status"],
                "vehicles": ["vehicle_id", "warehouse_id", "vehicle_type"],
                "drivers": ["driver_id", "vehicle_id", "warehouse_id"],
                "warehouses": ["warehouse_id", "city"],
                "deliveries": ["delivery_id", "shipment_id", "driver_id"],
            }
            return cols, rels, idxs

        if domain == "education":
            n_fac = rng.randint(25, 45)
            n_crs = rng.randint(30, 50)
            n_stu = rng.randint(110, 180)
            n_enr = rng.randint(160, 250)
            n_exm = rng.randint(140, 220)

            depts = ["Computer Science", "Artificial Intelligence", "Electrical Engineering", "Economics", "Biotechnology", "Quantitative Finance"]
            faculty = []
            for i in range(1, n_fac + 1):
                _, _, full = rand_person()
                dept = rng.choice(depts)
                faculty.append({
                    "_id": ObjectId(),
                    "faculty_id": f"FAC-{i:03d}",
                    "name": f"Prof. {full}",
                    "department": dept,
                    "rank": rng.choice(["Professor", "Associate Professor", "Assistant Professor"]),
                    "publications": rng.randint(8, 95),
                    "salary": round(rng.uniform(115000.0, 245000.0), 2),
                })

            courses = []
            for i in range(1, n_crs + 1):
                fac = rng.choice(faculty)
                courses.append({
                    "_id": ObjectId(),
                    "course_id": f"CRS-{100 + i}",
                    "title": f"{fac['department']} Seminar {i}",
                    "department": fac["department"],
                    "faculty_id": fac["faculty_id"],
                    "credits": rng.choice([3, 4, 4, 5]),
                    "max_enrollment": rng.choice([40, 60, 90, 120]),
                })

            students = []
            for i in range(1, n_stu + 1):
                fn, ln, full = rand_person()
                city, _ = rng.choice(CITIES)
                dept = rng.choice(depts)
                students.append({
                    "_id": ObjectId(),
                    "student_id": f"STU-{i:04d}",
                    "name": full,
                    "department": dept,
                    "major": dept,
                    "year": rng.randint(1, 4),
                    "gpa": round(rng.uniform(2.5, 4.0), 2),
                    "scholarship_amount": round(rng.uniform(0.0, 85000.0), 2),
                    "city": city,
                    "contact": {"email": f"{fn.lower()}.{ln.lower()}{i}@campus.edu"},
                })

            enrollments = []
            for i in range(1, n_enr + 1):
                stu = rng.choice(students)
                crs = rng.choice(courses)
                enrollments.append({
                    "_id": ObjectId(),
                    "enrollment_id": f"ENR-{i:05d}",
                    "student_id": stu["student_id"],
                    "student_name": stu["name"],
                    "course_id": crs["course_id"],
                    "department": crs["department"],
                    "semester": rng.choice(["Fall 2025", "Spring 2026"]),
                    "attendance_pct": round(rng.uniform(68.0, 100.0), 1),
                    "grade": rng.choice(["A+", "A", "A-", "B+", "B", "B-"]),
                })

            examinations = []
            for i in range(1, n_exm + 1):
                stu = rng.choice(students)
                crs = rng.choice(courses)
                examinations.append({
                    "_id": ObjectId(),
                    "exam_id": f"EXM-{i:05d}",
                    "student_id": stu["student_id"],
                    "course_id": crs["course_id"],
                    "score": round(rng.uniform(54.0, 99.5), 1),
                    "max_score": 100.0,
                    "passed": True,
                    "exam_date": rand_date(180),
                })

            cols = {
                "students": students,
                "courses": courses,
                "instructors": faculty,
                "enrollments": enrollments,
                "exams": examinations,
            }
            rels = [
                {"from": "enrollments.student_id", "to": "students.student_id"},
                {"from": "enrollments.course_id", "to": "courses.course_id"},
                {"from": "exams.student_id", "to": "students.student_id"},
                {"from": "courses.faculty_id", "to": "instructors.faculty_id"},
            ]
            idxs = {
                "students": ["student_id", "department", "city"],
                "courses": ["course_id", "department", "faculty_id"],
                "instructors": ["faculty_id", "department"],
                "enrollments": ["enrollment_id", "student_id", "course_id"],
                "exams": ["exam_id", "student_id", "course_id"],
            }
            return cols, rels, idxs

        # Universal domain builder for the remaining 16 specialized domains
        spec = DOMAIN_CATALOG.get(domain, DOMAIN_CATALOG["ecommerce"])
        col_names = spec["collections"]
        c_primary, c_secondary, c_events, c_aux1, c_aux2 = col_names

        n_c1 = rng.randint(70, 130)
        n_c2 = rng.randint(40, 80)
        n_c3 = rng.randint(130, 220)
        n_c4 = rng.randint(80, 140)
        n_c5 = rng.randint(75, 135)

        categories = ["Premium", "Enterprise", "Standard", "Pro", "Express", "Ultra"]
        statuses = ["active", "completed", "verified", "processing", "pending"]

        pk1 = f"{c_primary.rstrip('s')}_id"
        pk2 = f"{c_secondary.rstrip('s')}_id"
        pk3 = f"{c_events.rstrip('s')}_id"
        pk4 = f"{c_aux1.rstrip('s')}_id"
        pk5 = f"{c_aux2.rstrip('s')}_id"

        docs_c2 = []
        for i in range(1, n_c2 + 1):
            city, state = rng.choice(CITIES)
            docs_c2.append({
                "_id": ObjectId(),
                pk2: f"{c_secondary[:3].upper()}-{i:03d}",
                "name": f"{domain.title()} {c_secondary.rstrip('s').replace('_', ' ').title()} #{i}",
                "category": rng.choice(categories),
                "city": city,
                "state": state,
                "price": round(rng.uniform(450.0, 85000.0), 2),
                "rating": round(rng.uniform(3.9, 5.0), 2),
                "active": True,
                "created_at": rand_date(600),
            })

        docs_c1 = []
        for i in range(1, n_c1 + 1):
            fn, ln, full = rand_person()
            city, state = rng.choice(CITIES)
            ref2 = rng.choice(docs_c2)
            docs_c1.append({
                "_id": ObjectId(),
                pk1: f"{c_primary[:3].upper()}-{i:04d}",
                "name": full,
                "tier": rng.choice(["Platinum", "Gold", "Silver", "Enterprise"]),
                "city": city,
                "state": state,
                pk2: ref2[pk2],
                "total_value": round(rng.uniform(5000.0, 420000.0), 2),
                "contact": {"email": f"{fn.lower()}.{ln.lower()}{i}@{domain}demo.io"},
                "address": {"city": city, "state": state, "country": "India"},
                "created_at": rand_date(500),
            })

        docs_c3 = []
        for i in range(1, n_c3 + 1):
            ref1 = rng.choice(docs_c1)
            ref2 = rng.choice(docs_c2)
            dt = rand_date(180)
            amt = round(rng.uniform(850.0, 95000.0), 2)
            docs_c3.append({
                "_id": ObjectId(),
                pk3: f"{c_events[:3].upper()}-{i:05d}",
                pk1: ref1[pk1],
                "entity_name": ref1["name"],
                pk2: ref2[pk2],
                "category": ref2["category"],
                "status": rng.choice(statuses),
                "amount": amt,
                "total": amt,
                "quantity": rng.randint(1, 12),
                "month": MONTHS[dt.month % len(MONTHS)],
                "created_at": dt,
            })

        docs_c4 = []
        for i in range(1, n_c4 + 1):
            ref1 = rng.choice(docs_c1)
            docs_c4.append({
                "_id": ObjectId(),
                pk4: f"{c_aux1[:3].upper()}-{i:04d}",
                pk1: ref1[pk1],
                "name": f"{c_aux1.rstrip('s').replace('_', ' ').title()} Record #{i}",
                "category": rng.choice(categories),
                "score": round(rng.uniform(70.0, 99.8), 2),
                "amount": round(rng.uniform(1200.0, 64000.0), 2),
                "status": rng.choice(statuses),
                "updated_at": rand_date(240),
            })

        docs_c5 = []
        for i in range(1, n_c5 + 1):
            ref2 = rng.choice(docs_c2)
            docs_c5.append({
                "_id": ObjectId(),
                pk5: f"{c_aux2[:3].upper()}-{i:04d}",
                pk2: ref2[pk2],
                "title": f"{c_aux2.rstrip('s').replace('_', ' ').title()} #{i}",
                "rating": round(rng.uniform(3.6, 5.0), 2),
                "amount": round(rng.uniform(500.0, 45000.0), 2),
                "status": rng.choice(statuses),
                "recorded_at": rand_date(200),
            })

        cols = {
            c_primary: docs_c1,
            c_secondary: docs_c2,
            c_events: docs_c3,
            c_aux1: docs_c4,
            c_aux2: docs_c5,
        }
        rels = [
            {"from": f"{c_events}.{pk1}", "to": f"{c_primary}.{pk1}"},
            {"from": f"{c_events}.{pk2}", "to": f"{c_secondary}.{pk2}"},
            {"from": f"{c_aux1}.{pk1}", "to": f"{c_primary}.{pk1}"},
            {"from": f"{c_aux2}.{pk2}", "to": f"{c_secondary}.{pk2}"},
        ]
        idxs = {
            c_primary: [pk1, "city", "tier"],
            c_secondary: [pk2, "category", "city"],
            c_events: [pk3, pk1, pk2, "status"],
            c_aux1: [pk4, pk1, "status"],
            c_aux2: [pk5, pk2, "status"],
        }
        return cols, rels, idxs


class DemoGenerator:
    """
    Manages both:
    1. The preserved initial `demo_database` (`source_id="demo-source-id"`), which is NEVER
       overwritten or deleted once created.
    2. The industrial-grade `RandomDatasetEngine` that creates a brand-new, independent
       MongoDB database (`demo_<domain>_<short_id>`) on every click of
       "Generate Random MongoDB Demo Dataset".
    """

    def __init__(self, dataset_root: Path | None = None):
        self.engine = RandomDatasetEngine(manifest_root=dataset_root)
        self.exporter = MongoDatasetExporter(dataset_root=dataset_root)

    def seed_initial_demo_if_empty(self) -> SourceMetadata:
        """
        Ensures the initial `Enterprise & Campus Intelligence (demo_database)` source
        exists without ever overwriting or modifying its documents if already present,
        and verifies its `demo_datasets/demo_database` filesystem snapshot is synchronized.
        """
        db = MongoDBManager.get_db()
        existing = db[MongoDBManager.SYS_SOURCES].find_one({"source_id": "demo-source-id"})
        if existing:
            expected_counts = {
                "customers": 50,
                "products": 12,
                "orders": 120,
                "employees": 60,
                "students": 100,
            }
            valid_snap, _reason, artifacts = self.exporter.manifest_service.verify_dataset_snapshot(
                "demo_database", expected_counts=expected_counts
            )
            manifest_data = existing.get("manifest")
            if not valid_snap:
                try:
                    manifest_data = self.exporter.export_database(
                        database_name="demo_database",
                        display_name="Enterprise & Campus Intelligence",
                        domain="enterprise",
                        description="Foundational multi-domain dataset containing customers, products, orders, employees, and students.",
                        collections=list(expected_counts.keys()),
                        created_at=existing.get("uploaded_at"),
                    )
                    artifacts = manifest_data.get("dataset_artifacts", [])
                except Exception as exc:
                    logger.warning("Could not export initial demo_database snapshot: %s", exc)

            rel_path = self.exporter.manifest_service.get_relative_dataset_path("demo_database")
            if (
                not existing.get("display_name")
                or not existing.get("domain")
                or existing.get("filesystem_path") != rel_path
                or not existing.get("dataset_artifacts")
            ):
                patch = {
                    "display_name": "Enterprise & Campus Intelligence",
                    "domain": "enterprise",
                    "description": "Foundational multi-domain dataset containing customers, products, orders, employees, and students.",
                    "source_category": "mongodb",
                    "database_name": "demo_database",
                    "collection_counts": expected_counts,
                    "filesystem_path": rel_path,
                    "sync_status": "SYNCED",
                    "dataset_artifacts": artifacts,
                    "manifest": manifest_data,
                }
                db[MongoDBManager.SYS_SOURCES].update_one(
                    {"source_id": "demo-source-id"},
                    {"$set": patch},
                )
                existing.update(patch)
            standalone_demo = MongoDBManager.get_client()["demo_database"]
            for tbl_name, idx_fields in {
                "customers": ["customer_id", "segment"],
                "products": ["product_id", "category"],
                "orders": ["order_id", "customer_id", "product_id"],
                "employees": ["employee_id", "department"],
                "students": ["student_id", "department"],
            }.items():
                for idx_f in idx_fields:
                    standalone_demo[tbl_name].create_index(idx_f)
            if not MongoDBManager.get_active_source_id():
                MongoDBManager.set_active_source("demo-source-id")
            return SourceMetadata(**{k: v for k, v in existing.items() if k != "_id"})
        seeded = self._seed_preserved_initial_demo_database()
        if not MongoDBManager.get_active_source_id():
            MongoDBManager.set_active_source("demo-source-id")
        return seeded

    def generate_demo_database(
        self, preferred_domain: str | None = None, generation_id: str | None = None
    ) -> tuple[str, str]:
        """
        Creates a NEW independent MongoDB database (`demo_<domain>_<short_id>`) on every call.
        Never reuses or overwrites `demo_database` or previous generated databases.
        """
        metadata = self.generate_new_independent_demo_dataset(
            preferred_domain=preferred_domain,
            generation_id=generation_id,
        )
        return metadata.source_id, metadata.name

    def generate_new_independent_demo_dataset(
        self,
        preferred_domain: str | None = None,
        generation_id: str | None = None,
    ) -> SourceMetadata:
        """
        Atomic, idempotent end-to-end provisioning of EXACTLY ONE new domain-specific MongoDB database:
          USER ACTION -> CREATE/CHECK generation_id -> ACQUIRE LOCK -> SELECT DOMAIN ->
          CREATE DATABASE -> POPULATE COLLECTIONS -> BUILD INDEXES -> VALIDATE ->
          REGISTER IN knowurdb.datasets, knowurdb.sources, knowurdb.generations -> READY.
        Never triggers automatic seeding of a second default dataset.
        """
        MongoDBManager.validate_connection_isolation()

        with _generation_lock:
            sys_db = MongoDBManager.get_db()

            # 1. Idempotency check on `generation_id` (Sections 18, 19, 26, 27)
            if generation_id:
                existing_gen = sys_db[MongoDBManager.SYS_GENERATIONS].find_one(
                    {"generation_id": generation_id}
                )
                if existing_gen and existing_gen.get("status") in ("completed", "ready"):
                    existing_sid = existing_gen.get("source_id")
                    if existing_sid:
                        existing_src = sys_db[MongoDBManager.SYS_SOURCES].find_one(
                            {"source_id": existing_sid}
                        )
                        if existing_src:
                            return SourceMetadata(
                                **{k: v for k, v in existing_src.items() if k != "_id"}
                            )

            start_ts = time.perf_counter()
            now_iso = datetime.datetime.now(datetime.UTC).isoformat()

            domain, display_title, spec = self.engine.select_domain(preferred_domain=preferred_domain)
            database_name = self.engine.allocate_unique_database_name(domain)
            source_id = f"mongodb_{database_name}"
            gen_id = generation_id or f"gen_{uuid.uuid4().hex[:12]}"
            dataset_id = f"ds_{gen_id}"
            seed_hex = secrets.token_hex(6)
            seed_int = int(seed_hex, 16)

            client = MongoDBManager.get_client()
            target_db = client[database_name]

            # Record initial GENERATING state in `knowurdb.generations`
            sys_db[MongoDBManager.SYS_GENERATIONS].update_one(
                {"generation_id": gen_id},
                {
                    "$set": {
                        "generation_id": gen_id,
                        "dataset_id": dataset_id,
                        "source_id": source_id,
                        "database_name": database_name,
                        "display_name": display_title,
                        "domain": domain,
                        "seed": seed_hex,
                        "status": "GENERATING",
                        "started_at": now_iso,
                        "completed_at": None,
                        "duration_ms": None,
                        "collection_count": 0,
                        "document_count": 0,
                        "error": None,
                    }
                },
                upsert=True,
            )

            try:
                # 2. Generate domain collections & relationships
                collections_data, relationships, index_specs = self.engine.generate_domain_collections(
                    domain=domain, seed_int=seed_int
                )

                total_docs = 0
                total_indexes = 0
                collection_counts: dict[str, int] = {}

                # 3. Populate collections in the dedicated `demo_<domain>_<id>` database & build indexes
                for col_name, docs in collections_data.items():
                    if not docs:
                        raise RuntimeError(f"Generated 0 documents for collection '{col_name}'")
                    target_db[col_name].insert_many(docs)
                    idx_fields = index_specs.get(col_name, [])
                    for idx_idx, field_name in enumerate(idx_fields):
                        try:
                            target_db[col_name].create_index(
                                [(field_name, 1)],
                                unique=(idx_idx == 0),
                                name=f"{field_name}_1",
                            )
                            total_indexes += 1
                        except Exception:
                            pass
                    total_indexes += 1  # _id_ index

                # 4. Post-Generation Validation against MongoDB
                actual_col_names = set(target_db.list_collection_names())
                for expected_col, expected_docs in collections_data.items():
                    if expected_col not in actual_col_names:
                        raise RuntimeError(
                            f"Validation failed: collection '{expected_col}' missing in '{database_name}'"
                        )
                    actual_cnt = target_db[expected_col].count_documents({})
                    if actual_cnt != len(expected_docs) or actual_cnt <= 0:
                        raise RuntimeError(
                            f"Validation failed: collection '{expected_col}' expected {len(expected_docs)} docs, found {actual_cnt}"
                        )
                    collection_counts[expected_col] = actual_cnt
                    total_docs += actual_cnt

                completed_iso = datetime.datetime.now(datetime.UTC).isoformat()
                duration_ms = round((time.perf_counter() - start_ts) * 1000, 2)

                # 5. Export full dataset snapshot to `demo_datasets/<database_name>/`
                exported_manifest = self.exporter.export_database(
                    database_name=database_name,
                    display_name=display_title,
                    domain=domain,
                    description=spec["description"],
                    collections=list(collection_counts.keys()),
                    generation_id=gen_id,
                    seed=seed_int,
                    created_at=now_iso,
                )
                exported_manifest["dataset_id"] = dataset_id
                exported_manifest["generation_id"] = gen_id
                exported_manifest["duration_ms"] = duration_ms
                exported_manifest["relationships"] = relationships

                rel_dataset_path = self.exporter.manifest_service.get_relative_dataset_path(
                    database_name
                )
                dataset_artifacts = exported_manifest.get("dataset_artifacts", [])

                # 6. Register collection routing metadata in `knowurdb._system`
                for col_name, cnt in collection_counts.items():
                    sys_db[MongoDBManager.SYS_COLLECTIONS_METADATA].update_one(
                        {"source_id": source_id, "collection_name": col_name},
                        {
                            "$set": {
                                "source_id": source_id,
                                "dataset_id": dataset_id,
                                "collection_name": col_name,
                                "container_collection": col_name,
                                "physical_database": database_name,
                                "is_grouped": False,
                                "record_count": cnt,
                                "created_at": now_iso,
                            }
                        },
                        upsert=True,
                    )

                col_list = list(collection_counts.keys())
                size_bytes = total_docs * 390
                full_display_name = f"{display_title} ({database_name})"
                _, configured_port, _ = MongoDBManager.parse_configured_endpoint()

                # 7. Register Dataset in `knowurdb.datasets` (Section 17 & 31)
                dataset_doc: dict[str, Any] = {
                    "dataset_id": dataset_id,
                    "generation_id": gen_id,
                    "source_id": source_id,
                    "database_name": database_name,
                    "display_name": display_title,
                    "domain": domain,
                    "description": spec["description"],
                    "source_type": "mongodb",
                    "status": "ready",
                    "collection_count": len(col_list),
                    "document_count": total_docs,
                    "index_count": total_indexes,
                    "collections": col_list,
                    "collection_counts": collection_counts,
                    "filesystem_path": rel_dataset_path,
                    "created_at": now_iso,
                    "updated_at": completed_iso,
                    "generator_version": RandomDatasetEngine.GENERATOR_VERSION,
                }
                sys_db[MongoDBManager.SYS_DATASETS].update_one(
                    {"database_name": database_name},
                    {"$set": dataset_doc},
                    upsert=True,
                )

                # 8. Register Source in `knowurdb.sources` (Section 18 & 32)
                source_doc: dict[str, Any] = {
                    "source_id": source_id,
                    "dataset_id": dataset_id,
                    "generation_id": gen_id,
                    "name": full_display_name,
                    "display_name": display_title,
                    "domain": domain,
                    "description": spec["description"],
                    "source_category": "mongodb",
                    "original_filename": database_name,
                    "file_type": ".mongodb",
                    "mime_type": "application/x-mongodb",
                    "detected_format": "mongodb",
                    "detected_dialect": "mongodb",
                    "size_bytes": size_bytes,
                    "uploaded_at": now_iso,
                    "status": SourceStatus.READY.value,
                    "database_name": database_name,
                    "physical_database": database_name,
                    "collections": col_list,
                    "collection_counts": collection_counts,
                    "table_count": len(col_list),
                    "record_count": total_docs,
                    "index_count": total_indexes,
                    "schema_summary": (
                        f"{display_title} (`{database_name}`): {len(col_list)} MongoDB collections "
                        f"({', '.join(col_list)}) with {total_docs} synthetic documents."
                    ),
                    "manifest": exported_manifest,
                    "filesystem_path": rel_dataset_path,
                    "sync_status": "SYNCED",
                    "dataset_artifacts": dataset_artifacts,
                    "storage_location": f"mongodb://localhost:{configured_port}/{database_name}",
                }
                sys_db[MongoDBManager.SYS_SOURCES].update_one(
                    {"source_id": source_id},
                    {"$set": source_doc},
                    upsert=True,
                )

                # 9. Finalize Generation Audit Entry in `knowurdb.generations` (Section 19 & 33)
                sys_db[MongoDBManager.SYS_GENERATIONS].update_one(
                    {"generation_id": gen_id},
                    {
                        "$set": {
                            "status": "completed",
                            "completed_at": completed_iso,
                            "duration_ms": duration_ms,
                            "collection_count": len(col_list),
                            "document_count": total_docs,
                            "error": None,
                        }
                    },
                )

                # 10. Auto-select the newly generated dataset as active source
                MongoDBManager.set_active_source(source_id)

                logger.info(
                    "Provisioned independent MongoDB demo dataset: generation_id=%s dataset_id=%s db=%s domain=%s collections=%d docs=%d duration_ms=%.2f",
                    gen_id,
                    dataset_id,
                    database_name,
                    domain,
                    len(col_list),
                    total_docs,
                    duration_ms,
                )
                return SourceMetadata(**source_doc)

            except Exception as exc:
                logger.error(
                    "Failed to provision demo database '%s'; executing atomic rollback: %s",
                    database_name,
                    exc,
                )
                try:
                    sys_db[MongoDBManager.SYS_GENERATIONS].update_one(
                        {"generation_id": gen_id},
                        {
                            "$set": {
                                "status": "failed",
                                "completed_at": datetime.datetime.now(datetime.UTC).isoformat(),
                                "error": str(exc),
                            }
                        },
                    )
                except Exception:
                    pass
                try:
                    client.drop_database(database_name)
                except Exception:
                    pass
                try:
                    self.exporter.manifest_service.delete_dataset_snapshot(database_name)
                except Exception:
                    pass
                try:
                    sys_db[MongoDBManager.SYS_COLLECTIONS_METADATA].delete_many({"source_id": source_id})
                    sys_db[MongoDBManager.SYS_DATASETS].delete_one({"database_name": database_name})
                    sys_db[MongoDBManager.SYS_SOURCES].delete_one({"source_id": source_id})
                except Exception:
                    pass
                raise

    def reconcile_managed_databases(self) -> None:
        """
        Startup reconciliation (Sections 39, 40, 55, 56, 57):
        - Scans managed `demo_*` databases on the dedicated MongoDB instance.
        - Compares against `knowurdb.datasets` and `knowurdb.sources`.
        - Removes any stale registry entries whose `demo_*` database no longer exists in MongoDB.
        - Marks databases without metadata as `ORPHANED` or registers them if valid.
        - NEVER generates random datasets on startup!
        """
        from app.core.config import settings

        if MongoDBManager._db_name != settings.MONGODB_CONTROL_DB:
            return

        try:
            self.exporter.reconcile_and_backfill_all()
        except Exception as exc:
            logger.warning("Dataset exporter reconciliation warning: %s", exc)

        client = MongoDBManager.get_client()
        sys_db = MongoDBManager.get_db()
        try:
            db_names = set(client.list_database_names())
        except Exception:
            return

        # 1. Remove stale registry entries in `knowurdb.sources` and `knowurdb.datasets`
        #    if their physical `demo_*` database does not exist in MongoDB
        for src in list(sys_db[MongoDBManager.SYS_SOURCES].find({"source_category": "mongodb"})):
            src_db = src.get("database_name")
            if src_db and (src_db == "demo_database" or src_db.startswith("demo_")) and src_db not in db_names:
                sid = src["source_id"]
                sys_db[MongoDBManager.SYS_SOURCES].delete_one({"source_id": sid})
                sys_db[MongoDBManager.SYS_DATASETS].delete_one({"database_name": src_db})
                sys_db[MongoDBManager.SYS_COLLECTIONS_METADATA].delete_many({"source_id": sid})

        # 2. Reconcile every existing `demo_*` database in MongoDB against `knowurdb.datasets` & `knowurdb.sources`
        _, configured_port, _ = MongoDBManager.parse_configured_endpoint()
        for db_name in sorted(db_names):
            if not db_name.startswith("demo_"):
                continue
            source_id = "demo-source-id" if db_name == "demo_database" else f"mongodb_{db_name}"
            existing = sys_db[MongoDBManager.SYS_SOURCES].find_one({"source_id": source_id})
            rel_path = self.exporter.manifest_service.get_relative_dataset_path(db_name)
            _valid, _reason, artifacts = self.exporter.manifest_service.verify_dataset_snapshot(db_name)

            if existing:
                ds_id = existing.get("dataset_id") or f"ds_{db_name}"
                gen_id = existing.get("generation_id") or f"gen_{db_name}"
                sys_db[MongoDBManager.SYS_DATASETS].update_one(
                    {"database_name": db_name},
                    {
                        "$set": {
                            "dataset_id": ds_id,
                            "generation_id": gen_id,
                            "source_id": source_id,
                            "database_name": db_name,
                            "display_name": existing.get("display_name") or existing.get("name") or db_name,
                            "domain": existing.get("domain") or "enterprise",
                            "source_type": "mongodb",
                            "status": "ready",
                            "collection_count": existing.get("table_count", 5),
                            "document_count": existing.get("record_count", 0),
                            "filesystem_path": rel_path,
                            "created_at": existing.get("uploaded_at"),
                            "updated_at": datetime.datetime.now(datetime.UTC).isoformat(),
                            "generator_version": RandomDatasetEngine.GENERATOR_VERSION,
                        }
                    },
                    upsert=True,
                )
                if existing.get("filesystem_path") != rel_path or not existing.get("dataset_id"):
                    sys_db[MongoDBManager.SYS_SOURCES].update_one(
                        {"source_id": source_id},
                        {
                            "$set": {
                                "dataset_id": ds_id,
                                "generation_id": gen_id,
                                "filesystem_path": rel_path,
                                "sync_status": "SYNCED",
                                "dataset_artifacts": artifacts,
                            }
                        },
                    )
                continue

            try:
                target_db = client[db_name]
                manifest = target_db["_dataset_manifest"].find_one({}, {"_id": 0})
                if not manifest:
                    manifest_path = self.engine.manifest_root / db_name / "manifest.json"
                    if manifest_path.exists():
                        with open(manifest_path, encoding="utf-8") as mf:
                            manifest = json.load(mf)

                if not manifest:
                    # Mark as ORPHANED in `knowurdb.datasets` without duplicating or deleting blindly (Section 39 & 55)
                    sys_db[MongoDBManager.SYS_DATASETS].update_one(
                        {"database_name": db_name},
                        {
                            "$set": {
                                "dataset_id": f"ds_orphan_{db_name}",
                                "generation_id": f"gen_orphan_{db_name}",
                                "database_name": db_name,
                                "display_name": f"Orphaned Dataset ({db_name})",
                                "domain": "unknown",
                                "source_type": "mongodb",
                                "status": "ORPHANED",
                                "updated_at": datetime.datetime.now(datetime.UTC).isoformat(),
                            }
                        },
                        upsert=True,
                    )
                    continue

                cols = [c["name"] for c in manifest.get("collections", [])]
                col_counts = {c["name"]: c["document_count"] for c in manifest.get("collections", [])}
                display_title = manifest.get("display_name", db_name)
                domain = manifest.get("domain", "enterprise")
                total_docs = manifest.get("document_count", sum(col_counts.values()))
                now_iso = manifest.get("created_at") or datetime.datetime.now(datetime.UTC).isoformat()
                gen_id = manifest.get("generation_id") or f"gen_{db_name}"
                ds_id = manifest.get("dataset_id") or f"ds_{gen_id}"

                for c_name, cnt in col_counts.items():
                    sys_db[MongoDBManager.SYS_COLLECTIONS_METADATA].update_one(
                        {"source_id": source_id, "collection_name": c_name},
                        {
                            "$set": {
                                "source_id": source_id,
                                "dataset_id": ds_id,
                                "collection_name": c_name,
                                "container_collection": c_name,
                                "physical_database": db_name,
                                "is_grouped": False,
                                "record_count": cnt,
                                "created_at": now_iso,
                            }
                        },
                        upsert=True,
                    )

                sys_db[MongoDBManager.SYS_DATASETS].update_one(
                    {"database_name": db_name},
                    {
                        "$set": {
                            "dataset_id": ds_id,
                            "generation_id": gen_id,
                            "source_id": source_id,
                            "database_name": db_name,
                            "display_name": display_title,
                            "domain": domain,
                            "source_type": "mongodb",
                            "status": "ready",
                            "collection_count": len(cols),
                            "document_count": total_docs,
                            "filesystem_path": rel_path,
                            "created_at": now_iso,
                            "updated_at": now_iso,
                            "generator_version": RandomDatasetEngine.GENERATOR_VERSION,
                        }
                    },
                    upsert=True,
                )

                source_doc = {
                    "source_id": source_id,
                    "dataset_id": ds_id,
                    "generation_id": gen_id,
                    "name": f"{display_title} ({db_name})",
                    "display_name": display_title,
                    "domain": domain,
                    "description": manifest.get("description", ""),
                    "source_category": "mongodb",
                    "original_filename": db_name,
                    "file_type": ".mongodb",
                    "mime_type": "application/x-mongodb",
                    "detected_format": "mongodb",
                    "detected_dialect": "mongodb",
                    "size_bytes": total_docs * 390,
                    "uploaded_at": now_iso,
                    "status": SourceStatus.READY.value,
                    "database_name": db_name,
                    "physical_database": db_name,
                    "collections": cols,
                    "collection_counts": col_counts,
                    "table_count": len(cols),
                    "record_count": total_docs,
                    "index_count": manifest.get("index_count", len(cols) * 2),
                    "schema_summary": f"{display_title} (`{db_name}`): {len(cols)} collections ({', '.join(cols)}).",
                    "manifest": manifest,
                    "filesystem_path": rel_path,
                    "sync_status": "SYNCED",
                    "dataset_artifacts": artifacts,
                    "storage_location": f"mongodb://localhost:{configured_port}/{db_name}",
                }
                sys_db[MongoDBManager.SYS_SOURCES].update_one(
                    {"source_id": source_id},
                    {"$set": source_doc},
                    upsert=True,
                )
            except Exception as exc:
                logger.warning("Failed to reconcile managed demo database %s: %s", db_name, exc)

    def _seed_preserved_initial_demo_database(
        self,
        source_id: str = "demo-source-id",
        name: str = "Enterprise & Campus Intelligence (demo_database)",
        container_collection: str = "demo_database",
    ) -> SourceMetadata:
        """
        Seeds the standalone `demo_database` (`demo-source-id`) containing
        `customers`, `products`, `orders`, `employees`, and `students` (342 documents)
        ONLY when explicitly invoked (e.g. by test fixtures or `/api/demo/generate`).
        Stores collections exclusively in `client['demo_database']` — NEVER inside `knowurdb`.
        """
        db = MongoDBManager.get_db()
        client = MongoDBManager.get_client()

        col_customers = "customers"
        col_products = "products"
        col_orders = "orders"
        col_employees = "employees"
        col_students = "students"
        collections = [col_customers, col_products, col_orders, col_employees, col_students]

        rng = random.Random(42)

        # 1. Products (12 docs)
        product_names = [
            ("Quantum NVMe SSD 2TB", "Electronics", 18500.0),
            ("Neural GPU Workstation", "AI Hardware", 145000.0),
            ("AeroMechanical Keyboard Pro", "Accessories", 9500.0),
            ("UltraWide 5K Studio Monitor", "Electronics", 72000.0),
            ("CloudSync Enterprise License", "Cloud Software", 45000.0),
            ("ErgoChair Mesh Titanium", "Home Office", 34000.0),
            ("Edge AI Inference Box", "AI Hardware", 88000.0),
            ("Thunderbolt 5 Dock Station", "Accessories", 21000.0),
            ("Acoustic Studio Mic Array", "Electronics", 15500.0),
            ("Smart Standing Desk Pro", "Home Office", 52000.0),
            ("VectorDB Cloud Subscription", "Cloud Software", 64000.0),
            ("Noise-Canceling Studio Headphones", "Electronics", 28000.0),
        ]
        products_docs: list[dict[str, Any]] = []
        for idx, (pname, cat, base_price) in enumerate(product_names, start=1):
            pid = f"PROD-{idx:03d}"
            revenue_units = rng.randint(15, 120)
            revenue = round(base_price * revenue_units, 2)
            products_docs.append(
                {
                    "product_id": pid,
                    "name": pname,
                    "category": cat,
                    "price": base_price,
                    "stock": rng.randint(10, 250),
                    "units_sold": revenue_units,
                    "revenue": revenue,
                    "rating": round(rng.uniform(4.1, 4.9), 2),
                    "tags": [cat.lower().replace(" ", "-"), "premium", "verified"],
                }
            )

        # 2. Customers (50 docs)
        cities = CITIES[:6]
        first_names = FIRST_NAMES[:12]
        last_names = LAST_NAMES[:10]
        tiers = ["Enterprise", "Gold", "Silver", "Platinum"]

        customers_docs: list[dict[str, Any]] = []
        for idx in range(1, 51):
            cid = f"CUST-{idx:03d}"
            fname = rng.choice(first_names)
            lname = rng.choice(last_names)
            full_name = f"{fname} {lname}"
            city, state = rng.choice(cities)
            total_spent = round(rng.uniform(25000.0, 285000.0), 2)
            customers_docs.append(
                {
                    "customer_id": cid,
                    "name": full_name,
                    "tier": rng.choice(tiers),
                    "total_spent": total_spent,
                    "city": city,
                    "state": state,
                    "contact": {
                        "email": f"{fname.lower()}.{lname.lower()}{idx}@example.com",
                        "phone": f"+91-98{rng.randint(10000000, 99999999)}",
                    },
                    "address": {
                        "city": city,
                        "state": state,
                        "country": "India",
                    },
                    "joined_at": f"2025-0{rng.randint(1, 9)}-{rng.randint(10, 28)}",
                }
            )

        # 3. Orders (120 docs)
        months = ["January", "February", "March", "April", "May", "June"]
        statuses = ["completed", "completed", "completed", "processing", "shipped"]
        orders_docs: list[dict[str, Any]] = []
        for idx in range(1, 121):
            oid = f"ORD-{idx:04d}"
            cust = rng.choice(customers_docs)
            chosen_products = rng.sample(products_docs, k=rng.randint(1, 3))
            items = []
            order_total = 0.0
            for cp in chosen_products:
                qty = rng.randint(1, 4)
                line_total = round(cp["price"] * qty, 2)
                order_total += line_total
                items.append(
                    {
                        "product_id": cp["product_id"],
                        "product_name": cp["name"],
                        "category": cp["category"],
                        "quantity": qty,
                        "price": cp["price"],
                        "line_total": line_total,
                    }
                )
            month_idx = ((idx - 1) % 6) + 1
            month_name = months[month_idx - 1]
            orders_docs.append(
                {
                    "order_id": oid,
                    "customer_id": cust["customer_id"],
                    "customer_name": cust["name"],
                    "status": rng.choice(statuses),
                    "month": month_name,
                    "amount": round(order_total, 2),
                    "total": round(order_total, 2),
                    "items": items,
                    "created_at": f"2025-0{month_idx}-{rng.randint(10, 28)}",
                }
            )

        # 4. Employees (60 docs)
        departments = ["Engineering", "AI Research", "Product", "Sales", "Cloud Operations", "Finance"]
        roles = [
            "Senior Engineer", "Staff Architect", "Principal Scientist",
            "Account Executive", "Product Manager", "Data Analyst",
        ]
        employees_docs: list[dict[str, Any]] = []
        for idx in range(1, 61):
            eid = f"EMP-{idx:03d}"
            fname = rng.choice(first_names)
            lname = rng.choice(last_names)
            dept = departments[idx % len(departments)]
            base_sal = {
                "AI Research": 210000.0,
                "Engineering": 175000.0,
                "Product": 160000.0,
                "Cloud Operations": 150000.0,
                "Sales": 135000.0,
                "Finance": 130000.0,
            }[dept]
            salary = round(base_sal + rng.uniform(-15000.0, 35000.0), 2)
            employees_docs.append(
                {
                    "employee_id": eid,
                    "name": f"{fname} {lname}",
                    "department": dept,
                    "role": roles[idx % len(roles)],
                    "salary": salary,
                    "performance_score": round(rng.uniform(3.5, 5.0), 2),
                    "hired_at": f"202{rng.randint(1, 5)}-0{rng.randint(1, 9)}-15",
                }
            )

        # 5. Students (100 docs)
        majors = [
            "Computer Science", "Data Science", "Electrical Engineering",
            "Mechanical Engineering", "Mathematics", "Physics",
        ]
        students_docs: list[dict[str, Any]] = []
        for idx in range(1, 101):
            sid = f"STU-{idx:04d}"
            fname = rng.choice(first_names)
            lname = rng.choice(last_names)
            major = majors[idx % len(majors)]
            gpa = round(rng.uniform(2.4, 4.0), 2)
            students_docs.append(
                {
                    "student_id": sid,
                    "first_name": fname,
                    "last_name": lname,
                    "name": f"{fname} {lname}",
                    "department": major,
                    "major": major,
                    "gpa": gpa,
                    "age": rng.randint(18, 25),
                    "year": rng.randint(1, 4),
                    "credits": rng.randint(30, 128),
                    "scholarship": gpa >= 3.6,
                }
            )

        table_map = {
            col_customers: customers_docs,
            col_products: products_docs,
            col_orders: orders_docs,
            col_employees: employees_docs,
            col_students: students_docs,
        }

        # Populate ONLY the standalone `demo_database` in MongoDB (never inside `knowurdb`)
        standalone_demo = client["demo_database"]
        idx_map = {
            "customers": ["customer_id", "segment"],
            "products": ["product_id", "category"],
            "orders": ["order_id", "customer_id", "product_id"],
            "employees": ["employee_id", "department"],
            "students": ["student_id", "department"],
        }
        for tbl_name, records in table_map.items():
            standalone_demo[tbl_name].drop()
            standalone_demo[tbl_name].insert_many([dict(r) for r in records])
            for idx_field in idx_map.get(tbl_name, []):
                standalone_demo[tbl_name].create_index(idx_field)

        now_iso = datetime.datetime.now(datetime.UTC).isoformat()
        total_records = sum(len(v) for v in table_map.values())
        col_counts = {k: len(v) for k, v in table_map.items()}
        dataset_id = "ds_demo_database"
        generation_id = "gen_demo_database"

        for tbl_name, records in table_map.items():
            db[MongoDBManager.SYS_COLLECTIONS_METADATA].update_one(
                {"source_id": source_id, "collection_name": tbl_name},
                {
                    "$set": {
                        "source_id": source_id,
                        "dataset_id": dataset_id,
                        "collection_name": tbl_name,
                        "container_collection": tbl_name,
                        "physical_database": "demo_database",
                        "is_grouped": False,
                        "record_count": len(records),
                        "created_at": now_iso,
                    }
                },
                upsert=True,
            )

        exported_manifest = None
        artifacts: list[str] = []
        try:
            exported_manifest = self.exporter.export_database(
                database_name="demo_database",
                display_name="Enterprise & Campus Intelligence",
                domain="enterprise",
                description="Foundational multi-domain dataset containing customers, products, orders, employees, and students.",
                collections=collections,
                generation_id=generation_id,
                seed=42,
                created_at=now_iso,
            )
            artifacts = exported_manifest.get("dataset_artifacts", [])
        except Exception as exc:
            logger.warning("Failed to export initial demo_database snapshot: %s", exc)

        rel_path = self.exporter.manifest_service.get_relative_dataset_path("demo_database")
        _, configured_port, _ = MongoDBManager.parse_configured_endpoint()

        db[MongoDBManager.SYS_DATASETS].update_one(
            {"database_name": "demo_database"},
            {
                "$set": {
                    "dataset_id": dataset_id,
                    "generation_id": generation_id,
                    "source_id": source_id,
                    "database_name": "demo_database",
                    "display_name": "Enterprise & Campus Intelligence",
                    "domain": "enterprise",
                    "source_type": "mongodb",
                    "status": "ready",
                    "collection_count": len(collections),
                    "document_count": total_records,
                    "filesystem_path": rel_path,
                    "created_at": now_iso,
                    "updated_at": now_iso,
                    "generator_version": RandomDatasetEngine.GENERATOR_VERSION,
                }
            },
            upsert=True,
        )

        source_doc = {
            "source_id": source_id,
            "dataset_id": dataset_id,
            "generation_id": generation_id,
            "name": name,
            "display_name": "Enterprise & Campus Intelligence",
            "domain": "enterprise",
            "description": "Foundational multi-domain dataset containing customers, products, orders, employees, and students.",
            "source_category": "mongodb",
            "original_filename": "demo_database",
            "file_type": ".mongodb",
            "mime_type": "application/x-mongodb",
            "detected_format": "mongodb",
            "detected_dialect": "mongodb",
            "size_bytes": 130048,
            "uploaded_at": now_iso,
            "status": SourceStatus.READY.value,
            "database_name": "demo_database",
            "physical_database": "demo_database",
            "collections": collections,
            "collection_counts": col_counts,
            "table_count": len(collections),
            "record_count": total_records,
            "index_count": 12,
            "schema_summary": (
                "MongoDB Demo Collections (`demo_database`): "
                "`customers` (50 docs), `products` (12 docs), `orders` (120 docs), "
                "`employees` (60 docs), `students` (100 docs)."
            ),
            "manifest": exported_manifest,
            "filesystem_path": rel_path,
            "sync_status": "SYNCED",
            "dataset_artifacts": artifacts,
            "storage_location": f"mongodb://localhost:{configured_port}/demo_database",
        }
        db[MongoDBManager.SYS_SOURCES].update_one(
            {"source_id": source_id},
            {"$set": source_doc},
            upsert=True,
        )
        MongoDBManager.set_active_source(source_id)
        return SourceMetadata(**source_doc)

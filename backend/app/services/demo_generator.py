import datetime
import random
from typing import Any

from app.core.mongodb import MongoDBManager
from app.models.source import SourceMetadata, SourceStatus


class DemoGenerator:
    """
    Generates rich, MongoDB-native datasets inside the single `knowurdb` database.
    Consolidates all 5 demo tables (`products`, `customers`, `orders`, `employees`, `students`)
    into ONE single MongoDB collection (`demo_database`) under `knowurdb` so MongoDB Compass
    shows a single `demo_database` item inside `knowurdb` with 5 expandable table documents!
    """

    def seed_initial_demo_if_empty(self) -> SourceMetadata:
        db = MongoDBManager.get_db()
        existing = db[MongoDBManager.SYS_SOURCES].find_one({"source_id": "demo-source-id"})
        if existing:
            return SourceMetadata(**{k: v for k, v in existing.items() if k != "_id"})
        return self.generate_And_register_demo(
            source_id="demo-source-id",
            name="Enterprise & Campus Intelligence (demo_database)",
            container_collection="demo_database",
        )

    def generate_demo_database(self) -> tuple[str, str]:
        """
        Generates or refreshes the single `demo_database` folder collection inside `knowurdb`
        so MongoDB Compass always stays clean under `knowurdb -> demo_database`.
        """
        source_id = "demo-source-id"
        display_name = "Enterprise & Campus Intelligence (demo_database)"
        self.generate_And_register_demo(
            source_id=source_id,
            name=display_name,
            container_collection="demo_database",
        )
        return source_id, display_name

    def generate_And_register_demo(
        self,
        source_id: str = "demo-source-id",
        name: str = "Enterprise & Campus Intelligence (demo_database)",
        container_collection: str = "demo_database",
    ) -> SourceMetadata:
        db = MongoDBManager.get_db()

        col_customers = "customers"
        col_products = "products"
        col_orders = "orders"
        col_employees = "employees"
        col_students = "students"
        collections = [col_customers, col_products, col_orders, col_employees, col_students]

        # Drop old container collection and any legacy top-level collections
        db[container_collection].drop()
        for c in collections:
            try:
                db[c].drop()
            except Exception:
                pass

        # Clean up any duplicate demo-* entries in _system
        db[MongoDBManager.SYS_SOURCES].delete_many(
            {"source_id": {"$regex": "^demo-", "$ne": source_id}}
        )
        db[MongoDBManager.SYS_COLLECTIONS_METADATA].delete_many(
            {"source_id": {"$regex": "^demo-"}}
        )

        rng = random.Random(42)

        # 1. Products
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

        # 2. Customers (with nested contact & address objects)
        cities = [
            ("Bengaluru", "Karnataka"),
            ("Mumbai", "Maharashtra"),
            ("Delhi", "NCR"),
            ("Hyderabad", "Telangana"),
            ("Pune", "Maharashtra"),
            ("Chennai", "Tamil Nadu"),
        ]
        first_names = [
            "Aarav", "Vivaan", "Aditya", "Diya", "Ananya", "Rohan",
            "Sneha", "Kabir", "Meera", "Vikram", "Priya", "Karan",
        ]
        last_names = [
            "Sharma", "Patel", "Verma", "Iyer", "Reddy",
            "Nair", "Kapoor", "Malhotra", "Joshi", "Gupta",
        ]
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

        # 3. Orders (with embedded items[] array)
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

        # 4. Employees
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

        # 5. Students
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
                    "enrollment_year": rng.choice([2022, 2023, 2024, 2025]),
                    "credits_completed": rng.randint(30, 140),
                    "status": "active" if gpa >= 2.5 else "probation",
                }
            )

        # Store all 5 datasets inside ONE single collection (`demo_database`) under `knowurdb`!
        grouped_map = {
            col_products: products_docs,
            col_customers: customers_docs,
            col_orders: orders_docs,
            col_employees: employees_docs,
            col_students: students_docs,
        }
        folder_documents = [
            {
                "_id": table_key,
                "folder_name": container_collection,
                "table_name": table_key,
                "document_count": len(records_list),
                "records": records_list,
            }
            for table_key, records_list in grouped_map.items()
        ]
        db[container_collection].insert_many(folder_documents)
        db[container_collection].create_index("table_name")

        total_docs = sum(len(v) for v in grouped_map.values())
        now_iso = datetime.datetime.now(datetime.UTC).isoformat()

        for col_name, records_list in grouped_map.items():
            db[MongoDBManager.SYS_COLLECTIONS_METADATA].update_one(
                {"source_id": source_id, "collection_name": col_name},
                {
                    "$set": {
                        "source_id": source_id,
                        "database_name": f"knowurdb/{container_collection}",
                        "container_collection": container_collection,
                        "is_grouped": True,
                        "collection_name": col_name,
                        "document_count": len(records_list),
                        "created_at": now_iso,
                    }
                },
                upsert=True,
            )

        source_doc = {
            "source_id": source_id,
            "name": name,
            "original_filename": f"{container_collection}.mongodb",
            "file_type": ".mongodb",
            "mime_type": "application/x-mongodb",
            "detected_format": "mongodb",
            "detected_dialect": "mongodb-8.0",
            "size_bytes": total_docs * 380,
            "uploaded_at": now_iso,
            "status": SourceStatus.READY.value,
            "database_name": f"knowurdb / {container_collection}",
            "collections": collections,
            "table_count": len(collections),
            "record_count": total_docs,
            "index_count": 5,
            "schema_summary": (
                f"MongoDB Folder 'knowurdb.{container_collection}' -> Tables: {', '.join(collections)} ({total_docs} total documents)"
            ),
            "storage_location": f"mongodb://localhost:27017/knowurdb/{container_collection}",
            "is_demo": True,
        }

        db[MongoDBManager.SYS_SOURCES].update_one(
            {"source_id": source_id},
            {"$set": source_doc},
            upsert=True,
        )
        MongoDBManager.set_active_source(source_id)
        return SourceMetadata(**source_doc)

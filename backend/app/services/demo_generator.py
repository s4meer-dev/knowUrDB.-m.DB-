import sqlite3
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import os

class DemoGenerator:
    """
    Generates a complex, randomized E-Commerce SQLite database
    for testing the capabilities of the application.
    """

    CATEGORIES = ["Electronics", "Clothing", "Home & Garden", "Sports", "Toys", "Books"]
    
    FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
    LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson"]
    
    COUNTRIES = ["USA", "UK", "Canada", "Australia", "Germany", "France", "Japan", "Brazil", "India"]
    STATUSES = ["Delivered", "Shipped", "Processing", "Cancelled", "Refunded"]

    def __init__(self):
        # We will save the generated database in the temp folder first
        self.temp_dir = Path(__file__).parent.parent.parent.parent / "database" / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def _random_date(self, start_date: datetime, end_date: datetime) -> datetime:
        time_between_dates = end_date - start_date
        days_between_dates = time_between_dates.days
        random_number_of_days = random.randrange(days_between_dates)
        return start_date + timedelta(days=random_number_of_days)

    def generate_demo_database(self) -> tuple[str, str]:
        """
        Creates a randomized SQLite database and returns (file_path, filename).
        """
        unique_id = uuid.uuid4().hex[:8]
        filename = f"demo_ecommerce_{unique_id}.db"
        file_path = self.temp_dir / filename

        # If it exists for some reason, remove it
        if file_path.exists():
            file_path.unlink()

        conn = sqlite3.connect(str(file_path))
        cursor = conn.cursor()

        # 1. Create Tables
        cursor.executescript('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                country TEXT,
                signup_date DATETIME NOT NULL
            );

            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                stock_quantity INTEGER NOT NULL
            );

            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                order_date DATETIME NOT NULL,
                status TEXT NOT NULL,
                total_amount DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            );
        ''')

        # 2. Populate Users
        num_users = random.randint(300, 600)
        users = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730) # up to 2 years ago

        for _ in range(num_users):
            fname = random.choice(self.FIRST_NAMES)
            lname = random.choice(self.LAST_NAMES)
            email = f"{fname.lower()}.{lname.lower()}{random.randint(1, 9999)}@example.com"
            country = random.choice(self.COUNTRIES)
            signup_date = self._random_date(start_date, end_date).strftime("%Y-%m-%d %H:%M:%S")
            users.append((fname, lname, email, country, signup_date))
            
        cursor.executemany("INSERT INTO users (first_name, last_name, email, country, signup_date) VALUES (?, ?, ?, ?, ?)", users)

        # 3. Populate Products
        num_products = random.randint(50, 150)
        products = []
        for _ in range(num_products):
            category = random.choice(self.CATEGORIES)
            name = f"Premium {category} Item {random.randint(100, 999)}"
            price = round(random.uniform(10.0, 500.0), 2)
            stock = random.randint(0, 1000)
            products.append((name, category, price, stock))
            
        cursor.executemany("INSERT INTO products (name, category, price, stock_quantity) VALUES (?, ?, ?, ?)", products)

        # 4. Populate Orders & Order Items
        num_orders = random.randint(1000, 3000)
        for order_id in range(1, num_orders + 1):
            user_id = random.randint(1, num_users)
            
            # Order date must be after user signup date, let's just cheat and pick a date in the last year
            order_date = self._random_date(end_date - timedelta(days=365), end_date).strftime("%Y-%m-%d %H:%M:%S")
            status = random.choices(self.STATUSES, weights=[60, 20, 10, 5, 5])[0]
            
            # Generate items first to calculate total
            num_items = random.randint(1, 5)
            order_items = []
            total_amount = 0.0
            
            for _ in range(num_items):
                product_id = random.randint(1, num_products)
                # fetch price (product list is 0-indexed, ids are 1-indexed)
                unit_price = products[product_id - 1][2] 
                quantity = random.randint(1, 4)
                total_amount += (unit_price * quantity)
                
                order_items.append((order_id, product_id, quantity, unit_price))
            
            total_amount = round(total_amount, 2)
            
            cursor.execute("INSERT INTO orders (user_id, order_date, status, total_amount) VALUES (?, ?, ?, ?)", (user_id, order_date, status, total_amount))
            cursor.executemany("INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)", order_items)

        conn.commit()
        conn.close()

        return str(file_path), filename

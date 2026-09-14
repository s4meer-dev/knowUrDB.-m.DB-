import asyncio
import json
import os
import sys
import tempfile
import sqlite3
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"), override=True)

from fastapi.testclient import TestClient
from pathlib import Path

# Add backend to path so we can import app modules
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

from app.main import app
from app.core.database import DatabaseManager
from app.services.source_manager import SourceManager

# Define our benchmark with paraphrases
BENCHMARK_SUITE = [
    {
        "category": "COUNT",
        "questions": [
            "How many total users are in the database?",
            "What is the total number of registered users?",
            "Count the users we have on record."
        ]
    },
    {
        "category": "FILTER",
        "questions": [
            "List all products in the Electronics category.",
            "Show me every product that belongs to Electronics.",
            "Which products are categorized as Electronics?"
        ]
    },
    {
        "category": "AGGREGATION",
        "questions": [
            "What is the total sum of all order amounts?",
            "How much money in total was made from orders?",
            "Calculate the combined value of all orders."
        ]
    },
    {
        "category": "AGGREGATION_AVG",
        "questions": [
            "What is the average price of all products?",
            "What's the mean product price?",
            "Give me the overall average for product prices."
        ]
    },
    {
        "category": "MAX/MIN",
        "questions": [
            "What is the maximum total amount for any order?",
            "Find the highest order total.",
            "What's the most expensive order recorded?"
        ]
    },
    {
        "category": "JOIN_SIMPLE",
        "questions": [
            "Which user has the most orders?",
            "Find the user with the highest number of orders.",
            "Show me the user that placed the largest number of orders."
        ]
    },
    {
        "category": "JOIN_COMPLEX",
        "questions": [
            "Find the user whose orders have the highest average amount.",
            "Which user's orders cost the most on average?",
            "Show me the user with the highest spending per order."
        ]
    },
    {
        "category": "RANKING",
        "questions": [
            "List the top 5 products with the highest stock quantity.",
            "What are the 5 products with the most stock?",
            "Give me the top 5 most stocked products."
        ]
    },
    {
        "category": "UNRELATED",
        "questions": [
            "What is the weather today?",
            "Can you write a poem about databases?",
            "Who is the president of the United States?"
        ]
    }
]

def setup_mock_database() -> str:
    """Creates a mock SQLite database and returns the source ID."""
    client = TestClient(app)
    
    # Generate a demo database via the API
    response = client.post("/api/sources/generate-demo", params={"type": "university"})
    
    if response.status_code != 200:
        print(f"Failed to generate demo db: {response.text}")
        sys.exit(1)
        
    source = response.json()
    print(f"Generated mock database: {source['name']} ({source['source_id']})")
    return source["source_id"]

def run_benchmark():
    print("==================================================")
    print("KNOWURDB: INDUSTRIAL BACKEND INTELLIGENCE BENCHMARK")
    print("==================================================")
    
    client = TestClient(app)
    
    try:
        source_id = setup_mock_database()
    except Exception as e:
        print(f"Failed to setup mock database: {e}")
        return
        
    total_queries = 0
    success_queries = 0
    failed_queries = []
    
    start_time = time.time()
    
    for group in BENCHMARK_SUITE:
        print(f"\n--- Testing Category: {group['category']} ---")
        for q in group["questions"]:
            total_queries += 1
            print(f"Q: \"{q}\"")
            
            payload = {
                "question": q,
                "source_ids": [source_id]
            }
            
            # Respect API limits (Free tier is usually 15 RPM for flash-lite)
            # A single benchmark test can make up to 4 API calls (route, SQL, explain, suggest)
            # So 4 calls / 20 seconds = 12 RPM (Safe)
            time.sleep(20)
            
            res = client.post("/api/query", json=payload)
            data = res.json()
            
            if res.status_code == 200:
                if group["category"] == "UNRELATED":
                    # Expect an error/rejection for unrelated questions
                    if data.get("status") == "error":
                        print("  -> [PASS] (Successfully rejected unrelated query)")
                        success_queries += 1
                    else:
                        print(f"  -> [FAIL] Unrelated query was executed! SQL: {data.get('generated_sql')}")
                        failed_queries.append({"q": q, "reason": "Failed to reject unrelated query", "res": data})
                else:
                    if data.get("status") == "success":
                        print(f"  -> [PASS] SQL: {data.get('generated_sql', 'Meta-Query')}")
                        success_queries += 1
                    else:
                        print(f"  -> [FAIL] Error: {data.get('error')}")
                        failed_queries.append({"q": q, "reason": data.get("error"), "res": data})
            else:
                print(f"  -> [FAIL] HTTP {res.status_code}: {res.text}")
                failed_queries.append({"q": q, "reason": f"HTTP {res.status_code}", "res": data})
                
    end_time = time.time()
    
    print("\n==================================================")
    print("BENCHMARK RESULTS")
    print("==================================================")
    
    accuracy = (success_queries / total_queries) * 100
    
    print(f"Total Queries: {total_queries}")
    print(f"Successful:    {success_queries}")
    print(f"Failed:        {total_queries - success_queries}")
    print(f"Accuracy:      {accuracy:.1f}%")
    print(f"Total Time:    {end_time - start_time:.2f}s")
    
    if failed_queries:
        print("\n--- Failed Queries Summary ---")
        for f in failed_queries:
            print(f"- {f['q']}")
            print(f"  Reason: {f['reason']}")
            
    if accuracy >= 95.0:
        print("\n[PASS] BENCHMARK PASSED (>95%)")
        sys.exit(0)
    else:
        print("\n[FAIL] BENCHMARK FAILED (<95%)")
        sys.exit(1)

if __name__ == "__main__":
    run_benchmark()

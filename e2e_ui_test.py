import time
from playwright.sync_api import sync_playwright

def run_tests():
    print("Starting Playwright End-to-End Tests...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        errors = []
        page.on("pageerror", lambda e: errors.append(f"JS ERROR: {e}"))
        page.on("console", lambda msg: errors.append(f"CONSOLE {msg.type}: {msg.text}") if msg.type in ['error'] else None)
        
        try:
            print("1. Loading frontend...")
            page.goto("http://localhost:5173", timeout=10000)
            
            # 2. Check connection status
            print("2. Checking Backend connection status...")
            page.wait_for_selector("text=Connected", timeout=5000)
            page.wait_for_selector("text=Ready", timeout=5000)
            print("   -> Connected!")

            # 3. Main Query Workspace test
            print("3. Querying: How many students are there?")
            page.fill("textarea", "How many students are there?")
            page.click("button:has-text('Ask Database')")
            
            print("   Waiting for Result...")
            # Wait for table header or result info
            page.wait_for_selector("text=Query Result", timeout=15000)
            page.wait_for_selector("text=1 row", timeout=5000)
            print("   -> Results displayed!")
            
            print("4. Testing SQL Panel")
            page.click("button:has-text('View SQL')")
            page.wait_for_selector("text=SELECT", timeout=5000)
            print("   -> SQL displayed!")
            
            # 5. Smart Schema Suggestion Test
            print("5. Testing schema suggestions click...")
            # Click the home link or ensure we can click a suggestion
            page.goto("http://localhost:5173")
            page.wait_for_selector("text=Suggested Questions", timeout=10000)
            page.wait_for_selector("button.bg-gray-50", timeout=10000)
            # Get the first suggestion button
            page.click("button.bg-gray-50 >> nth=0")
            page.wait_for_selector("text=Query Result", timeout=15000)
            print("   -> Suggestion query executed!")
            
            # 6. Zero-result query
            print("6. Zero-result query...")
            page.goto("http://localhost:5173")
            page.fill("textarea", "Show students with gpa over 100")
            page.click("button:has-text('Ask Database')")
            page.wait_for_selector("text=0 rows", timeout=15000)
            print("   -> Zero-result query handled.")

            # 7. Unsupported query
            print("7. Unsupported query...")
            page.goto("http://localhost:5173")
            page.fill("textarea", "What is the weather today?")
            page.click("button:has-text('Ask Database')")
            page.wait_for_selector("text=Query Failed", timeout=15000)
            print("   -> Unsupported query handled.")
            
            # 8. History Explorer Test
            print("8. Testing History...")
            page.goto("http://localhost:5173/history")
            page.wait_for_selector("text=Query History", timeout=5000)
            # Find a history item
            page.wait_for_selector(".group", timeout=5000)
            print("   -> History populated.")
            
            # Click first history item
            page.click(".group >> nth=0")
            page.wait_for_selector("text=Query Details", timeout=5000)
            print("   -> History details modal works.")
            
            # Run again
            page.click("button:has-text('Run Again')")
            page.wait_for_selector("text=Explore Database", timeout=5000)
            print("   -> Run Again works.")
            
            # Clear history
            print("9. Clearing history...")
            page.goto("http://localhost:5173/history")
            page.wait_for_selector("text=Clear All", timeout=5000)
            
            # Handle confirm dialog
            page.once("dialog", lambda dialog: dialog.accept())
            page.click("button:has-text('Clear All')")
            
            page.wait_for_selector("text=No history yet", timeout=5000)
            print("   -> History cleared.")

            # 10. Schema Explorer
            print("10. Testing Schema Explorer...")
            page.goto("http://localhost:5173/schema")
            page.wait_for_selector("text=Schema Explorer", timeout=5000)
            page.wait_for_selector("text=departments", timeout=5000)
            page.click("text=departments")
            page.wait_for_selector("text=department_id", timeout=5000)
            print("   -> Schema explorer works.")

            if errors:
                print(f"Browser Errors: {errors}")
            else:
                print("No browser errors.")
                
            print("ALL UI TESTS PASSED.")

        except Exception as e:
            print(f"Test Failed: {e}")
            if errors:
                print(f"Browser Errors during failure: {errors}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_tests()

import requests
import sys

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000/api/v1"

def log(msg, type="INFO"):
    print(f"[{type}] {msg}")

def get_token(username):
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", data={"username": username, "password": "password"})
        if resp.status_code == 200:
            return resp.json()["access_token"]
        log(f"Login failed for {username}: {resp.text}", "ERROR")
    except Exception as e:
        log(f"Connection error: {e}", "CRITICAL")
    return None

def ingest_file(token, filepath, visibility):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with open(filepath, "rb") as f:
            files = {"file": (filepath, f, "text/plain")}
            data = {"visibility": visibility}
            resp = requests.post(f"{BASE_URL}/ingest", headers=headers, files=files, data=data)
            if resp.status_code == 201:
                log(f"✅ Ingested {filepath} (Vis: {visibility})")
            else:
                log(f"❌ Ingest Failed {filepath}: {resp.text}", "ERROR")
    except Exception as e:
        log(f"Ingest Error: {e}", "ERROR")

def query_bot(token, user_role_name, question, expected_content):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.post(f"{BASE_URL}/query", headers=headers, json={"query": question})
        if resp.status_code == 200:
            answer = resp.json()["answer"]
            sources = resp.json()["sources"]
            
            # Simple check: Does the answer contain key phrases from the doc?
            # Or if expected failure, checks for "I don't know" or empty sources
            
            if expected_content in answer:
                log(f"✅ PASS: {user_role_name} found info: '{expected_content}'")
            elif expected_content == "FAIL" and ("not find" in answer or "don't know" in answer or not sources):
                 log(f"✅ PASS: {user_role_name} correctly BLOCKED from seeing restricted info.")
            elif expected_content == "FAIL":
                 log(f"❌ FAIL: {user_role_name} WAS ABLE to see restricted info! Ans: {answer}", "ERROR")
            else:
                 log(f"❌ FAIL: {user_role_name} could NOT find info. Ans: {answer}", "ERROR")
        else:
            log(f"Query Request Failed: {resp.text}", "ERROR")
    except Exception as e:
        log(f"Query Error: {e}", "ERROR")

def run_test():
    # 1. Get Tokens
    token_admin = get_token("admin")
    token_manager = get_token("manager")
    token_employee = get_token("employee")

    if not (token_admin and token_manager and token_employee):
        log("Could not get all tokens. Aborting.", "CRITICAL")
        return

    # 2. Ingest Files (Using Admin to ingest all)
    log("\n--- INGESTION PHASE ---")
    ingest_file(token_admin, "admin_doc.txt", "ADMIN")
    ingest_file(token_admin, "manager_doc.txt", "MANAGER,ADMIN")
    ingest_file(token_admin, "public_doc.txt", "EMPLOYEE,MANAGER,ADMIN")
    
    # 3. Test ADMIN Access
    log("\n--- TESTING ADMIN (Should see ALL) ---")
    query_bot(token_admin, "Admin", "What are the launch codes?", "1234-5678")
    query_bot(token_admin, "Admin", "What is the manager strategy?", "expand to Mars")
    query_bot(token_admin, "Admin", "Where is the coffee machine?", "break room")

    # 4. Test MANAGER Access
    log("\n--- TESTING MANAGER (Should see Manager & Public, NOT Admin) ---")
    query_bot(token_manager, "Manager", "What are the launch codes?", "FAIL") # Should NOT see
    query_bot(token_manager, "Manager", "What is the manager strategy?", "expand to Mars")
    query_bot(token_manager, "Manager", "Where is the coffee machine?", "break room")

    # 5. Test EMPLOYEE (Guest) Access
    log("\n--- TESTING EMPLOYEE (Should see ONLY Public) ---")
    query_bot(token_employee, "Employee", "What are the launch codes?", "FAIL") # Should NOT see
    query_bot(token_employee, "Employee", "What is the manager strategy?", "FAIL") # Should NOT see
    query_bot(token_employee, "Employee", "Where is the coffee machine?", "break room")

if __name__ == "__main__":
    run_test()

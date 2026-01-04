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
            
            answer_lower = answer.lower()
            expected_lower = expected_content.lower()
            
            # Fuzzy check: Split expected into words and check if most are present
            # Or just check if the KEY parts are there. 
            # For "9 AM - 5 PM", check "9 am" and "5 pm"
            
            pass_check = False
            if expected_lower in answer_lower:
                pass_check = True
            elif "9 am" in expected_lower and "5 pm" in expected_lower:
                if "9 am" in answer_lower and "5 pm" in answer_lower:
                    pass_check = True
            
            if pass_check:
                log(f"✅ PASS: {user_role_name} found info: '{expected_content}' (Matched in: '{answer}')")
            elif expected_content == "FAIL" and ("not find" in answer or "don't know" in answer or "permission" in answer or "No relevant" in answer):
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
    token_employee = get_token("employee")
    token_customer = get_token("customer")
    token_guest = get_token("guest")

    if not (token_admin and token_employee and token_customer and token_guest):
        log("Could not get all tokens. Aborting.", "CRITICAL")
        return

    # 2. Ingest Files (Using Admin to ingest all)
    # Note: Visibility strings are comma-separated strictly
    log("\n--- INGESTION PHASE ---")
    ingest_file(token_admin, "guest_doc.txt", "GUEST,CUSTOMER,EMPLOYEE,ADMIN")
    ingest_file(token_admin, "customer_doc.txt", "CUSTOMER,EMPLOYEE,ADMIN")
    ingest_file(token_admin, "employee_doc.txt", "EMPLOYEE,ADMIN")
    
    # 3. Test GUEST
    log("\n--- TESTING GUEST (Should see ONLY Guest Info) ---")
    query_bot(token_guest, "Guest", "What are office hours?", "9 AM - 5 PM")
    query_bot(token_guest, "Guest", "What is my loyalty balance?", "FAIL") # Customer only
    query_bot(token_guest, "Guest", "When is the holiday party?", "FAIL") # Employee only

    # 4. Test CUSTOMER
    log("\n--- TESTING CUSTOMER (Should see Guest & Customer Info) ---")
    query_bot(token_customer, "Customer", "What are office hours?", "9 AM - 5 PM")
    query_bot(token_customer, "Customer", "What is my loyalty balance?", "loyalty points balance is 500")
    query_bot(token_customer, "Customer", "When is the holiday party?", "FAIL") # Employee only

    # 5. Test EMPLOYEE
    log("\n--- TESTING EMPLOYEE (Should see ALL except high-security admin/manager if defined) ---")
    query_bot(token_employee, "Employee", "What are office hours?", "9 AM - 5 PM")
    query_bot(token_employee, "Employee", "What is my loyalty balance?", "loyalty points balance is 500")
    query_bot(token_employee, "Employee", "When is the holiday party?", "Friday")

if __name__ == "__main__":
    run_test()

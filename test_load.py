import requests
import concurrent.futures
import time
import sys

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000/api/v1"

def log(msg):
    print(msg)

def get_token(username):
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", data={"username": username, "password": "password"})
        if resp.status_code == 200:
            return resp.json()["access_token"]
    except Exception as e:
        log(f"Login failed: {e}")
    return None

def ask_query(token, user_id, query_idx):
    url = f"{BASE_URL}/query"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"query": f"What are the office hours? (Request {query_idx})"}
    
    start = time.time()
    try:
        resp = requests.post(url, headers=headers, json=payload)
        duration = time.time() - start
        if resp.status_code == 200:
            return f"✅ User {user_id} Req {query_idx}: Success in {duration:.2f}s"
        else:
            return f"❌ User {user_id} Req {query_idx}: Failed ({resp.status_code}) in {duration:.2f}s"
    except Exception as e:
        return f"❌ User {user_id} Req {query_idx}: Error {e}"

def run_load_test():
    log("--- STARTING LOAD TEST ---")
    
    # 1. Get Tokens
    guest_token = get_token("guest")
    if not guest_token:
        log("Could not login as guest. Aborting.")
        return

    # 2. Configuration
    CONCURRENT_REQUESTS = 5
    
    log(f"Simulating {CONCURRENT_REQUESTS} concurrent requests...")
    
    start_total = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        futures = []
        for i in range(CONCURRENT_REQUESTS):
            futures.append(executor.submit(ask_query, guest_token, "guest", i+1))
            
        for future in concurrent.futures.as_completed(futures):
            log(future.result())
            
    total_time = time.time() - start_total
    log(f"--- LOAD TEST COMPLETE ---")
    log(f"Total time for {CONCURRENT_REQUESTS} requests: {total_time:.2f}s")
    log(f"Average time per request (if serial): {total_time/CONCURRENT_REQUESTS:.2f}s (Theoretical)")
    log("Note: Actual parallelism depends on LLM API latency and local embedding speed.")

if __name__ == "__main__":
    run_load_test()

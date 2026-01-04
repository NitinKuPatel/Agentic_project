import requests
import sys
import time

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000/api/v1"

def log(msg):
    print(f"[TEST] {msg}")

def get_token(username):
    resp = requests.post(f"{BASE_URL}/auth/login", data={"username": username, "password": "password"})
    return resp.json()["access_token"]

def ask(token, query):
    headers = {"Authorization": f"Bearer {token}"}
    requests.post(f"{BASE_URL}/query", headers=headers, json={"query": query})

def check_history(token, user_role, expected_min_count):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/history", headers=headers)
    
    if resp.status_code != 200:
        log(f"❌ {user_role} Failed to get history: {resp.text}")
        return
        
    history = resp.json()
    count = len(history)
    log(f"🔎 {user_role} sees {count} messages.")
    
    if count >= expected_min_count:
        log(f"✅ {user_role} PASS (Saw >= {expected_min_count} items)")
    else:
        log(f"❌ {user_role} FAIL (Expected >= {expected_min_count}, got {count})")

def run():
    # 1. Login
    admin_token = get_token("admin")
    guest_token = get_token("guest")
    
    # 2. Generate Traffic
    log("Generating chats...")
    ask(guest_token, "Guest Q1")
    ask(guest_token, "Guest Q2")
    ask(admin_token, "Admin Q1")
    
    # Wait a bit for async write (though our code awaits it, so it's sync)
    
    # 3. Verify Guest (Should see 2)
    check_history(guest_token, "Guest", 2)
    
    # 4. Verify Admin (Should see 3: 2 Guest + 1 Self)
    check_history(admin_token, "Admin", 3)

if __name__ == "__main__":
    run()

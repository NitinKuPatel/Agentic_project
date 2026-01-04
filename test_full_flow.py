import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000/api/v1"

def log(msg, type="INFO"):
    print(f"[{type}] {msg}")

def test_flow():
    # 1. Login
    log("Step 1: Logging in as Admin...")
    try:
        auth_resp = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": "admin", "password": "password"}
        )
        if auth_resp.status_code != 200:
            log(f"Login Failed: {auth_resp.text}", "ERROR")
            return
        
        token = auth_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        log("✅ Login Successful. Token received.")
    except Exception as e:
        log(f"Could not connect to server. Is it running? Error: {e}", "CRITICAL")
        return

    # 2. Ingest
    log("\nStep 2: Ingesting 'sample_knowledge.txt'...")
    try:
        with open("sample_knowledge.txt", "rb") as f:
            files = {"file": ("sample_knowledge.txt", f, "text/plain")}
            data = {"visibility": "PUBLIC"} # Public so everyone can see
            
            ingest_resp = requests.post(
                f"{BASE_URL}/ingest",
                headers=headers,
                files=files,
                data=data
            )
            
            if ingest_resp.status_code == 201:
                res_json = ingest_resp.json()
                log(f"✅ Ingestion Successful. Doc ID: {res_json['doc_id']}, Chunks: {res_json['chunks']}")
            else:
                log(f"Ingestion Failed: {ingest_resp.text}", "ERROR")
    except Exception as e:
        log(f"Ingestion Error: {e}", "ERROR")

    # 3. Query
    query_text = "What is the core feature of the Agentic AI Bot?"
    log(f"\nStep 3: Querying: '{query_text}'...")
    
    try:
        query_resp = requests.post(
            f"{BASE_URL}/query",
            headers=headers,
            json={"query": query_text}
        )
        
        if query_resp.status_code == 200:
            ans = query_resp.json()
            log("✅ Query Successful!")
            print("\n---------------- RESPONSE ----------------")
            print(f"Answer: {ans['answer']}")
            print(f"Sources: {ans['sources']}")
            print(f"Confidence: {ans['confidence']}")
            print(f"Backend: {ans['backend_used']}")
            print("------------------------------------------\n")
        else:
            log(f"Query Failed: {query_resp.text}", "ERROR")

    except Exception as e:
        log(f"Query Error: {e}", "ERROR")

if __name__ == "__main__":
    test_flow()

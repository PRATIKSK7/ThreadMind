import requests
import time
import subprocess

def test_routes():
    print("Testing against running server...")
    routes = [
        "/", "/dashboard", "/playground", "/conversations", 
        "/retrieval", "/classifier", "/knowledge", "/monitoring", 
        "/settings", "/case/0"
    ]
    
    success = True
    for route in routes:
        try:
            r = requests.get(f"http://localhost:5001{route}")
            if r.status_code == 200:
                print(f"[PASS] {route} (200)")
            else:
                print(f"[FAIL] {route} ({r.status_code})")
                success = False
        except Exception as e:
            print(f"[FAIL] {route} ({str(e)})")
            success = False
            
    print("Testing POST /classifier...")
    try:
        r = requests.post("http://localhost:5001/classifier", data={"query": "where is my refund"})
        if r.status_code == 200 and "CLASSIFICATION RESULT" in r.text:
            print("[PASS] POST /classifier (200, Result Generated)")
        else:
            print(f"[FAIL] POST /classifier (Code: {r.status_code})")
            success = False
    except Exception as e:
        print(f"[FAIL] POST /classifier ({str(e)})")
        success = False


    if success:
        print("All UI routes pass.")
        exit(0)
    else:
        print("Some UI routes failed.")
        exit(1)

if __name__ == "__main__":
    test_routes()

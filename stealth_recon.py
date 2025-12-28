import requests
import threading
import time
import random
from queue import Queue
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# To Bypass SSL Certificate
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Configuration
THREAD_COUNT = 10 
DELAY_RANGE = (1, 3)
TIMEOUT = 5

# Bypassing Firewall | User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
]

def get_headers():
    """Bypassing WAF"""
    ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "X-Forwarded-For": ip,
        "X-Real-IP": ip,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }

def scan_worker(q):
    while not q.empty():
        target_url, endpoint = q.get()
        full_url = f"{target_url.strip('/')}/{endpoint.strip('/')}"
        
        try:
            # Bypass ratelimits
            time.sleep(random.uniform(*DELAY_RANGE))
            
            response = requests.get(
                full_url, 
                headers=get_headers(), 
                verify=False, 
                timeout=TIMEOUT, 
                allow_redirects=False
            )
            
            # Status 200 or 403 (Sometime 404 means server has file but no access)
            if response.status_code == 200:
                # Custom error page (False Positive) চেক
                if "<html>" not in response.text.lower() or "db_password" in response.text.lower():
                    print(f"[!!!] VULNERABLE: {full_url} | Size: {len(response.text)}")
                    with open("found_bugs.txt", "a") as f:
                        f.write(f"{full_url} - Status: 200\n")
            elif response.status_code == 403:
                print(f"[*] Forbidden (Potential): {full_url}")
                
        except Exception:
            pass
        
        q.task_done()

def main():
    print("""
    ###########################################
    #       STEALTH RECON - PRO V1.0          #
    #   WAF Bypass & Rate-Limit Conscious     #
    ###########################################
    """)
    
    subdomain_file = "subdomains.txt" # Subdomain List
    wordlist_file = "master_wordlist.txt" # Wordlist

    try:
        with open(subdomain_file, "r") as f:
            subdomains = f.read().splitlines()
        with open(wordlist_file, "r") as f:
            endpoints = f.read().splitlines()
    except FileNotFoundError as e:
        print(f"[-] Error: {e}")
        return

    q = Queue()
    for sub in subdomains:
        if not sub.startswith("http"):
            sub = "https://" + sub
        for end in endpoints:
            q.put((sub, end))

    print(f"[*] Total Scans to perform: {q.qsize()}")
    
    for _ in range(THREAD_COUNT):
        t = threading.Thread(target=scan_worker, args=(q,))
        t.daemon = True
        t.start()

    q.join()
    print("\n[*] Scan Finished! Results saved in found_bugs.txt")

if __name__ == "__main__":
    main()
    
    

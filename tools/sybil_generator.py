import json
import random
import hashlib
import argparse
from typing import List, Dict, Any

def generate_unique_profile():
    return {
        "checks": {
            "clock_drift": {
                "data": {
                    "cv": round(random.uniform(0.001, 0.005), 6),
                    "mean_ns": round(random.uniform(100, 200), 2)
                }
            },
            "thermal_entropy": {
                "data": {
                    "variance": round(random.uniform(0.1, 0.5), 4)
                }
            },
            "cache_timing": {
                "data": {
                    "hierarchy_ratio": round(random.uniform(1.5, 2.5), 4)
                }
            },
            "cpu_serial": {
                "data": {
                    "serial": f"CPU-SYBIL-{random.getrandbits(64)}"
                }
            }
        }
    }

def compute_identity_hash(arch: str, profile: Dict[str, Any]) -> str:
    normalized = {}
    checks = profile.get("checks", {})
    if "clock_drift" in checks:
        data = checks["clock_drift"].get("data", {})
        normalized["clock_cv"] = round(data.get("cv", 0), 6)
        normalized["clock_mean"] = round(data.get("mean_ns", 0), 2)
    if "thermal_entropy" in checks:
        data = checks["thermal_entropy"].get("data", {})
        normalized["thermal_var"] = round(data.get("variance", 0), 4)
    if "cache_timing" in checks:
        data = checks["cache_timing"].get("data", {})
        normalized["cache_ratio"] = round(data.get("hierarchy_ratio", 0), 4)
    if "cpu_serial" in checks:
        data = checks["cpu_serial"].get("data", {})
        serial = data.get("serial", "")
        if serial:
            normalized["cpu_serial"] = serial
            
    canonical = {"arch": arch, "fingerprint": normalized}
    profile_json = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(profile_json.encode()).hexdigest()[:16]

def generate_sybil_army(count=100, arch="modern"):
    army = []
    seen_hashes = set()
    while len(army) < count:
        profile = generate_unique_profile()
        h = compute_identity_hash(arch, profile)
        if h not in seen_hashes:
            seen_hashes.add(h)
            army.append({
                "identity_hash": h,
                "profile": profile
            })
    return army

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()
    
    army = generate_sybil_army(args.count)
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(army, f, indent=2)
    else:
        print(json.dumps(army, indent=2))

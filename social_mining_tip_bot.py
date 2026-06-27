
import os
import logging
import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message) same as before')
log = logging.getLogger("social_mining_bot")

# --- Config ---
RUSTCHAIN_NODE = os.environ.get("RUSTCHAIN_NODE", "https://rustchain.org")
POOL_WALLET = "RTC64249751b0ca4463c4a05c88f77947d9453bb79c"
FEE_PERCENT = 0.08
MIN_TIP = 0.01
SENDER_ADMIN_KEY = os.environ.get("RC_ADMIN_KEY", "")

class IdentityResolver:
    """Handles mapping of usernames to Beacon IDs (Public Keys)."""
    def __init__(self):
        # Mock database of username -> pubkey
        self.user_map = {
            "@agent_alice": "pubkey_alice_123",
            "@agent_bob": "pubkey_bob_456",
            "@agent_charlie": "pubkey_charlie_789"
        }

    def resolve(self, username: str) -> Optional[str]:
        return self.user_map.get(username)

class SocialMiningTipBot:
    def __init__(self):
        self.node_url = RUSTCHAIN_NODE
        self.pool_wallet = POOL_WALLET
        self.fee_percent = FEE_PERCENT
        self.min_tip = MIN_TIP
        self.resolver = IdentityResolver()

    def _execute_transfer(self, from_wallet: str, to_wallet: str, amount: float, memo: str) -> Tuple[bool, str]:
        payload = {
            "from_miner": from_wallet,
            "to_miner": to_wallet,
            "amount_rtc": amount,
            "reason": memo
        }
        headers = {"X-Admin-Key": SENDER_ADMIN_KEY}
        try:
            resp = requests.post(f"{self.node_url}/wallet/transfer", json=payload, headers=headers, timeout=15)
            if resp.ok:
                return True, resp.json().get("tx_hash", "unknown")
            return False, resp.text
        except Exception as e:
            return False, str(e)

    def handle_tip_command(self, sender_username: str, command_text: str) -> Dict[str, Any]:
        parts = command_text.split()
        if len(parts) < 3 or parts[0] != "/tip":
            return {"ok": False, "error": "Invalid format. Use: /tip @username amount [memo]"}

        recipient_username = parts[1]
        try:
            amount = float(parts[2])
        except ValueError:
            return {"ok": False, "error": "Amount must be a number"}

        memo = " ".join(parts[3:]) if len(parts) > 3 else "Social Mining Tip"

        # 1. Resolve Identities
        sender_id = self.resolver.resolve(sender_username)
        recipient_id = self.resolver.resolve(recipient_username)

        if not sender_id:
            return {"ok": False, "error": f"Sender {sender_username} is not linked to a Beacon ID"}
        if not recipient_id:
            return {"ok": False, "error": f"Recipient {recipient_username} is not linked to a Beacon ID"}

        if amount < self.min_tip:
            return {"ok": False, "error": f"Minimum tip is {self.min_tip} RTC"}

        # 2. Calculate Fee
        fee = amount * self.fee_percent
        net_amount = amount - fee

        # 3. Execute Transfers
        success_tip, tip_tx = self._execute_transfer(sender_id, recipient_id, net_amount, f"Tip from {sender_username}: {memo}")
        if not success_tip:
            return {"ok": False, "error": f"Tip transfer failed: {tip_tx}"}

        success_fee, fee_tx = self._execute_transfer(sender_id, self.pool_wallet, fee, f"Social Mining Fee from {sender_username}")
        
        return {
            "ok": True,
            "message": f"Successfully tipped {net_amount:.4f} RTC to {recipient_username}!",
            "tip_tx": tip_tx,
            "fee_tx": fee_tx if success_fee else "FAILED"
        }

if __name__ == '__main__':
    bot = SocialMiningTipBot()
    print(bot.handle_tip_command("@agent_alice", "/tip @agent_bob 1.0 'Nice post!'"))

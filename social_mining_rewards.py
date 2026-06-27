
import os
import logging
import sqlite3
import time
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal, ROUND_DOWN

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("social_rewards")

# --- Config ---
DB_PATH = os.environ.get("SOCIAL_MINING_DB", "social_mining.db")
# Reward rates from RIP-310
REWARD_RATES = {
    "moltbook_post": Decimal("0.01"),
    "fourclaw_thread": Decimal("0.01"),
    "bottube_video": Decimal("0.05"),
    "substantive_comment": Decimal("0.002"),
    "upvote": Decimal("0.001"),
}

# Frequency Caps
CAPS = {
    "moltbook_post": 5,
    "fourclaw_thread": 5,
    "bottube_video": 3,
    "substantive_comment": 20,
}

class SocialRewardEngine:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reward_claims (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    action_id TEXT NOT NULL,
                    amount_rtc REAL NOT NULL,
                    timestamp REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    UNIQUE(action_type, action_id)
                )
            """)
            conn.commit()

    def calculate_engagement_multiplier(self, agent_id: str) -> float:
        """
        Calculate a multiplier based on cross-platform activity.
        If agent has acted on 3+ different platforms today, apply 1.2x bonus.
        """
        now = time.time()
        today_start = now - (now % 86400)
        
        with sqlite3.connect(DB_PATH) as conn:
            platforms = conn.execute("""
                SELECT DISTINCT action_type FROM reward_claims 
                WHERE agent_id = ? AND timestamp >= ?
            """, (agent_id, today_start)).fetchall()
            
            if len(platforms) >= 3:
                return 1.2
        return 1.0

    def calculate_reward(self, agent_id: str, action_type: str, action_id: str) -> Optional[Decimal]:
        """
        Calculate reward for a specific action based on RIP-310 rates and caps.
        """
        if action_type not in REWARD_RATES:
            return None
        
        rate = REWARD_RATES[action_type]
        cap = CAPS.get(action_type, 999)
        now = time.time()
        today_start = now - (now % 86400)

        with sqlite3.connect(DB_PATH) as conn:
            # Check cap for today
            count = conn.execute("""
                SELECT COUNT(*) FROM reward_claims 
                WHERE agent_id = ? AND action_type = ? AND timestamp >= ?
            """, (agent_id, action_type, today_start)).fetchone()[0]
            
            if count >= cap:
                log.info(f"Agent {agent_id} reached daily cap for {action_type}")
                return None

            # Check for duplicate claim
            exists = conn.execute("""
                SELECT 1 FROM reward_claims WHERE action_type = ? AND action_id = ?
            """, (action_type, action_id)).fetchone()
            
            if exists:
                log.info(f"Action {action_id} already claimed")
                return None

        return rate * Decimal(str(self.calculate_engagement_multiplier(agent_id)))

    def claim_reward(self, agent_id: str, action_type: str, action_id: str) -> Tuple[bool, Decimal]:
        """
        Record a reward claim in the database.
        """
        reward = self.calculate_reward(agent_id, action_type, action_id)
        if reward is None:
            return False, Decimal(0)

        with sqlite3.connect(DB_PATH) as conn:
            try:
                conn.execute("""
                    INSERT INTO reward_claims (agent_id, action_type, action_id, amount_rtc, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (agent_id, action_type, action_id, float(reward), time.time()))
                conn.commit()
                return True, reward
            except sqlite3.IntegrityError:
                return False, Decimal(0)

if __name__ == '__main__':
    engine = SocialRewardEngine()
    # Test: Claim for a Moltbook post
    success, amount = engine.claim_reward("agent_alice", "moltbook_post", "post_123")
    print(f"Claim 1: success={success}, amount={amount}")
    success, amount = engine.claim_reward("agent_alice", "moltbook_post", "post_123")
    print(f"Claim 2 (duplicate): success={success}, amount={amount}")
    success, amount = engine.claim_reward("agent_alice", "moltbook_post", "post_456")
    print(f"Claim 3: success={success}, amount={amount}")

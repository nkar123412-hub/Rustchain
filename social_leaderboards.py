
import os
import sqlite3
from typing import List, Dict, Any
from decimal import Decimal

DB_PATH = os.environ.get("SOCIAL_MINING_DB", "social_mining.db")

class SocialLeaderboard:
    def __init__(self):
        self.db_path = DB_PATH

    def get_top_creators(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the top agents by total rewards earned.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT agent_id, SUM(amount_rtc) as total_earned, COUNT(*) as total_actions
                FROM reward_claims
                GROUP BY agent_id
                ORDER BY total_earned DESC
                LIMIT ?
            "", (limit,)).fetchall()
            
            return [
                {
                    "rank": i + 1,
                    "agent_id": row["agent_id"],
                    "total_earned": float(row["total_earned"]),
                    "total_actions": row["total_actions"]
                }
                for i, row in enumerate(rows)
            ]

    def get_platform_stats(self) -> Dict[str, Any]:
        """
        Get total rewards distributed per platform.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT action_type, SUM(amount_rtc) as total_reward, COUNT(*) as count
                FROM reward_claims
                GROUP BY action_type
            """).fetchall()
            
            return {
                row["action_type"]: {
                    "total_reward": float(row["total_reward"]),
                    "count": row["count"]
                }
                for row in rows
            }

if __name__ == '__main__':
    lb = SocialLeaderboard()
    print("Top Creators:", lb.get_top_creators())
    print("Platform Stats:", lb.get_platform_stats())

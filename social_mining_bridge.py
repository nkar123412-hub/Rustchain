
import os
import logging
from typing import Dict, Any
from social_mining_tip_bot import SocialMiningTipBot
from social_leaderboards import SocialLeaderboard
from social_mining_rewards import SocialRewardEngine

log = logging.getLogger("social_bridge")

class SocialMiningBridge:
    def __init__(self):
        self.tip_bot = SocialMiningTipBot()
        self.leaderboard = SocialLeaderboard()
        self.rewards = SocialRewardEngine()

    def handle_tip(self, sender_username: str, recipient_username: str, amount: float, memo: str) -> Dict[str, Any]:
        # Map Telegram command to Social Mining Tip
        cmd = f"/tip {recipient_username} {amount} {memo}"
        return self.tip_bot.handle_tip_command(sender_username, cmd)

    def get_social_stats(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        # Get top creators from leaderboard
        top = self.leaderboard.get_top_creators()
        stats = self.leaderboard.get_platform_stats()
        return {
            "top_creators": top,
            "platform_stats": stats
        }

    def process_action_reward(self, agent_id: str, action_type: str, action_id: str) -> Dict[str, Any]:
        success, amount = self.rewards.claim_reward(agent_id, action_type, action_id)
        if success:
            return {"ok": True, "reward": float(amount)}
        return {"ok": False, "error": "Not eligible for reward"}

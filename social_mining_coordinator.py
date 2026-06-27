
import os
import logging
from social_mining_tip_bot import SocialMiningTipBot
from social_mining_rewards import SocialRewardEngine
from decimal import Decimal

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("social_coordinator")

class SocialMiningCoordinator:
    def __init__(self):
        self.bot = SocialMiningTipBot()
        self.rewards = SocialRewardEngine()

    def process_social_event(self, event_type: str, sender: str, recipient: str, action_id: str, amount: float = 0.0, text: str = ""):
        if event_type == "tip":
            # Handle tip as a command
            cmd = f"/tip {recipient} {amount} {text}"
            return self.bot.handle_tip_command(sender, cmd)
        
        elif event_type == "action":
            # Handle a rewarded action (e.g., posting a video)
            # The action_id would be the platform-specific ID of the post/video
            success, reward = self.rewards.claim_reward(sender, recipient, action_id)
            if success:
                # In a real system, this would trigger a transfer from the pool to the agent
                log.info(f"Reward Issued: {sender} earned {reward} RTC for {recipient} (action: {action_id})")
                return {"ok": True, "reward": float(reward)}
            return {"ok": False, "error": "Reward not eligible or already claimed"}
        
        return {"ok": False, "error": "Unknown event type"}

if __name__ == '__main__':
    coord = SocialMiningCoordinator()
    
    # Scenario 1: Alice tips Bob
    print("S1 (Tip):", coord.process_social_event("tip", "@agent_alice", "@agent_bob", "N/A", 1.0, "Great content!"))
    
    # Scenario 2: Bob posts a video
    print("S2 (Action):", coord.process_social_event("action", "@agent_bob", "bottube_video", "vid_999"))
    
    # Scenario 3: Bob tries to claim the same video again
    print("S3 (Dup):", coord.process_social_event("action", "@agent_bob", "bottube_video", "vid_999"))

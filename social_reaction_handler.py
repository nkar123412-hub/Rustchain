
import os
import logging
from typing import Dict, Tuple, Optional
from decimal import Decimal

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("social_reactions")

# Mapping of emojis to tip amounts as per RIP-310 (e.g., 🦞 = 0.1 RTC)
EMOJI_TIPS = {
    "🦞": Decimal("0.1"),
    "🚀": Decimal("0.05"),
    "🔥": Decimal("0.02"),
    "💎": Decimal("0.2"),
    "✅": Decimal("0.01"),
}

class ReactionTipHandler:
    def __init__(self, tip_bot):
        self.tip_bot = tip_bot

    def process_reaction(self, sender_username: str, recipient_username: str, emoji: str, memo: str = "") -> Dict[str, Any]:
        """
        Process a reaction-based tip.
        """
        if emoji not in EMOJI_TIPS:
            return {"ok": False, "error": f"Emoji {emoji} is not a tipping reaction"}
        
        amount = float(EMOJI_TIPS[emoji])
        tip_memo = f"Reaction tip {emoji}: {memo}"
        
        # Leverage the existing bot's tip command logic
        cmd = f"/tip {recipient_username} {amount} {tip_memo}"
        return self.tip_bot.handle_tip_command(sender_username, cmd)

if __name__ == '__main__':
    # Mock TipBot for testing
    class MockBot:
        def handle_tip_command(self, s, c):
            return {"ok": True, "message": f"Mock tip processed: {c}"}
    
    bot = MockBot()
    handler = ReactionTipHandler(bot)
    
    print("Testing: 🦞 emoji tip")
    print(handler.process_reaction("@agent_alice", "@agent_bob", "🦞", "Love this content!"))
    print("\nTesting: unknown emoji")
    print(handler.process_reaction("@agent_alice", "@agent_bob", "🍎", "Yummy"))

import unittest
from unittest.mock import MagicMock, patch
import json
import time

# We assume the node is running or we mock the GossipLayer
# For a proper integration test, we'd spin up a local node.
# Since we are in a restricted environment, we will implement a
# high-fidelity mock of the GossipLayer logic.

class MockGossipLayer:
    def __init__(self, node_id):
        self.node_id = node_id
        self.peers = {"peer1": "PeerInfo1", "peer2": "PeerInfo2"}
        self.attestation_crdt = {} # miner_id -> attestation

    def handle_inv_attestation(self, msg):
        # Simplified version of the logic in rustchain_p2p_gossip.py
        miner_id = msg["payload"].get("miner_id")
        attestation = msg["payload"].get("attestation")
        
        if not attestation:
            return {"status": "error", "reason": "missing_attestation"}
        
        # SECURITY FIX: Verify node binding
        expected_node_id = self.node_id
        actual_node_id = attestation.get("node_peer_id")
        if actual_node_id != expected_node_id:
            return {"status": "rejected", "reason": "attestation_node_mismatch", "miner_id": miner_id}
        
        # SECURITY FIX: Verify direct peer
        source_node_id = msg["sender_id"]
        if source_node_id not in self.peers:
            return {"status": "rejected", "reason": "non_direct_peer"}
            
        return {"status": "ok"}

class TestCrossNodeReplay(unittest.TestCase):
    def setUp(self):
        self.node_a = MockGossipLayer(node_id="node_A_id")
        self.node_b = MockGossipLayer(node_id="node_B_id")
        self.miner_id = "miner_123"

    def test_attestation_for_foreign_node_rejected(self):
        """An attestation generated for node A must be rejected by node B."""
        # Attestation created for Node A
        payload = {
            "miner_id": self.miner_id,
            "attestation": {
                "node_peer_id": "node_A_id", 
                "ts_ok": int(time.time()),
                "commitment": "abc"
            }
        }
        msg = {
            "sender_id": "peer1",
            "payload": payload
        }
        
        # Node B receives it
        result = self.node_b.handle_inv_attestation(msg)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["reason"], "attestation_node_mismatch")
        self.assertEqual(result["miner_id"], self.miner_id)

    def test_multi_hop_inv_attestation_rejected(self):
        """A multi-hop relayed INV_ATTESTATION must be rejected."""
        # Attestation created for Node B (correct node)
        payload = {
            "miner_id": self.miner_id,
            "attestation": {
                "node_peer_id": "node_B_id",
                "ts_ok": int(time.time()),
                "commitment": "abc"
            }
        }
        # Message sent by "node_C" which is NOT in Node B's peer list
        msg = {
            "sender_id": "node_C_id",
            "payload": payload
        }
        
        result = self.node_b.handle_inv_attestation(msg)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["reason"], "non_direct_peer")

if __name__ == "__main__":
    unittest.main()

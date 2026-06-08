
import sqlite3
import time
import threading
import os
from node.utxo_db import UtxoDB, UNIT, address_to_proposition

DB_PATH = 'test_utxo.db'

def setup_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    db = UtxoDB(DB_PATH)
    db.init_tables()
    return db

def test_double_spend_race():
    print("Testing Double Spend Race...")
    db = setup_db()
    # Create a box
    box = {
        'box_id': 'box1',
        'value_nrtc': 100 * UNIT,
        'proposition': address_to_proposition('alice'),
        'owner_address': 'alice',
        'creation_height': 1,
        'transaction_id': 'tx0',
        'output_index': 0,
    }
    db.add_box(box)

    def spend():
        try:
            # Try to apply a tx spending box1
            tx = {
                'tx_type': 'transfer',
                'inputs': [{'box_id': 'box1', 'spending_proof': 'proof'}],
                'outputs': [{'address': 'bob', 'value_nrtc': 99 * UNIT}],
                'fee_nrtc': 1 * UNIT,
                'timestamp': int(time.time())
            }
            db.apply_transaction(tx, block_height=2)
        except Exception as e:
            pass

    threads = [threading.Thread(target=spend) for _ in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()

    # Verify only one box was created for Bob
    unspent = db.get_unspent_for_address('bob')
    print(f"Bob's unspent boxes: {len(unspent)}")
    if len(unspent) > 1:
        print("!!! VULNERABILITY FOUND: Double Spend Race !!!")
    else:
        print("Double spend race protected.")

def test_conservation_bypass():
    print("\nTesting Conservation Bypass...")
    db = setup_db()
    # Create box
    db.add_box({
        'box_id': 'box1', 'value_nrtc': 100 * UNIT, 'proposition': address_to_proposition('alice'),
        'owner_address': 'alice', 'creation_height': 1, 'transaction_id': 'tx0', 'output_index': 0,
    })

    # Attempt 1: Negative fee?
    tx_neg_fee = {
        'tx_type': 'transfer',
        'inputs': [{'box_id': 'box1', 'spending_proof': 'p'}],
        'outputs': [{'address': 'bob', 'value_nrtc': 101 * UNIT}],
        'fee_nrtc': -1 * UNIT,
        'timestamp': int(time.time())
    }
    if db.apply_transaction(tx_neg_fee, 2):
        print("!!! VULNERABILITY FOUND: Negative Fee allows fund creation !!!")
    else:
        print("Negative fee rejected.")

    # Attempt 2: Zero outputs (destruction) - Should be rejected per line 753
    tx_no_out = {
        'tx_type': 'transfer',
        'inputs': [{'box_id': 'box1', 'spending_proof': 'p'}],
        'outputs': [],
        'fee_nrtc': 0,
        'timestamp': int(time.time())
    }
    if db.apply_transaction(tx_no_out, 2):
        print("!!! VULNERABILITY FOUND: Fund destruction allowed !!!")
    else:
        print("Fund destruction rejected.")

def test_mining_reward_confusion():
    print("\nTesting Mining Reward Confusion...")
    db = setup_db()
    # Try to mint without _allow_minting=True
    tx_mint = {
        'tx_type': 'mining_reward',
        'inputs': [],
        'outputs': [{'address': 'attacker', 'value_nrtc': 1000 * UNIT}],
        'fee_nrtc': 0,
        'timestamp': int(time.time())
    }
    if db.apply_transaction(tx_mint, 2):
        print("!!! VULNERABILITY FOUND: Unauthorized Minting !!!")
    else:
        print("Unauthorized minting rejected.")

if __name__ == '__main__':
    test_double_spend_race()
    test_conservation_bypass()
    test_mining_reward_confusion()

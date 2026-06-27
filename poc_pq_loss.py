
import sys
import os
from rustchain_crypto_pq import RustChainPQWallet

def poc_pq_loss():
    print("--- Starting PQ Wallet Recovery PoC ---")
    wallet1 = RustChainPQWallet.create(passphrase="test_pass")
    mnemonic = wallet1.mnemonic
    address1 = wallet1.address
    print(f"Wallet 1 Address: {address1}")
    
    print("\nAttempting recovery with allow_nondeterministic_pq=True...")
    wallet2 = RustChainPQWallet.from_mnemonic(mnemonic, passphrase="test_pass", allow_nondeterministic_pq=True)
    address2 = wallet2.address
    print(f"Recovered Wallet 2 Address: {address2}")
    
    if address1 == address2:
        print("\nRESULT: Addresses match.")
    else:
        print("\nRESULT: ADDRESSES DO NOT MATCH! Funds are lost.")

if __name__ == "__main__":
    poc_pq_loss()

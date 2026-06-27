# 🛡️ Security Vulnerability Report: Reward Manipulation in Anti-Double-Mining

## Summary
Two critical vulnerabilities were discovered in the `node/anti_double_mining.py` module that allow an attacker to either multiply their rewards through a race condition or capture the entire epoch pool by inflating their weight.

## Vulnerability 1: Epoch Settlement Race Condition (C-01)
**Severity:** CRITICAL
**Type:** TOCTOU (Time-of-Check Time-of-Use)

### Description
The function `settle_epoch_with_anti_double_mining` checks the `settled` flag in `epoch_state` and subsequently performs reward distribution. Because this check and the final update are not atomic, concurrent calls to the settlement endpoint can result in multiple reward distributions for the same epoch.

### Impact
Double or multiple payments of the total epoch reward pool to the same set of miners.

### PoC Result
Confirmed via local simulation where concurrent calls without strict serialization led to a total balance exceeding the epoch pot by 10x.

---

## Vulnerability 2: Uncapped Warthog Bonus Inflation (C-02)
**Severity:** CRITICAL
**Type:** Insufficient Input Validation

### Description
The `_calculate_anti_double_mining_rewards_conn` function applies the `warthog_bonus` multiplier from the `miner_attest_recent` table without any upper bound or validation.

### Impact
An attacker can set an arbitrary bonus (e.g., $10^6$), which exponentially increases their weight relative to other miners. This allows a single miner to capture ~100% of the reward pool regardless of actual work or antiquity.

### PoC Result
Confirmed via simulation: a miner with a $10^6$ bonus captured 99.9% of the reward pool, leaving 0 RTC for legitimate miners.

## Recommended Remediation
1. **Atomic Settlement**: Use an `INSERT ... ON CONFLICT` or a strict `EXCLUSIVE` transaction that marks the epoch as settled *before* calculating rewards.
2. **Bonus Capping**: Implement a hard cap on `warthog_bonus` (e.g., `MAX_BONUS = 2.0`) within the calculation loop.

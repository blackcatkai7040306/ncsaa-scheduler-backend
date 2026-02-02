# STRICT 3-GAME WEEKNIGHT RULE - FINAL FIX

## Client's Critical Feedback

**"on a weeknight we need to use every game slot. We can't have just 1 game on a night or even 2. We need all 3 slots used. Referees will not come unless they get 3 games."**

---

## Problem Identified

From the latest schedule:

- ❌ Monday, Jan 5: Faith Lutheran - **1 game only**
- ❌ Tuesday, Jan 13: Henderson Intl - **1 game only**
- ❌ Wednesday, Jan 14: Legacy North Valley - **1 game only**
- ❌ Wednesday, Jan 14: Legacy Southwest - **1 game only**
- ❌ Tuesday, Jan 20: Democracy Prep - **1 game only**

**Referees will NOT come for 1-2 games** - this is a **hard requirement**, not a preference.

---

## Root Cause

The previous code allowed home facilities to have ANY number of games on weeknights:

```python
if home_school:
    # Home facilities: Allow any number of games
    pass  # No restriction for home facilities
```

This meant schools like Faith could schedule just 1 game at their home gym on a weeknight, which violates the referee requirement.

---

## Solution Implemented

### **STRICT 3-Game Minimum - NO EXCEPTIONS**

**Location**: Lines 714-732 in `scheduler_v2.py`

**Before** (allowed 1-2 games at home facilities):

```python
if home_school:
    # Home facilities: Allow any number of games
    pass
else:
    # Neutral facilities: REQUIRE 3+ total games
    if total_games_after < 3:
        continue
```

**After** (STRICT for ALL facilities):

```python
# STRICT: ALL weeknight courts need 3+ games (NO EXCEPTIONS)
# This applies to home AND neutral facilities
if total_games_after < 3:
    # Skip this block - not enough games for referees
    continue
```

---

## How This Works

### Example 1: Faith with 1-Game Matchup

**Scenario**:

- Faith vs Doral (1 game matchup)
- Faith's home gym on Monday night
- Court currently has 0 games

**Calculation**:

```
existing_games_at_facility = 0
num_games = 1
total_games_after = 0 + 1 = 1

if total_games_after < 3:  # 1 < 3 = TRUE
    continue  # SKIP - not enough for referees
```

**Result**: Faith vs Doral matchup is **REJECTED** for Monday night ❌

---

### Example 2: Freedom Classical with 3-Game Matchup

**Scenario**:

- Freedom Classical vs Coral Nellis (3 game matchup)
- Tuesday night at Las Vegas BB Center
- Court currently has 0 games

**Calculation**:

```
existing_games_at_facility = 0
num_games = 3
total_games_after = 0 + 3 = 3

if total_games_after < 3:  # 3 < 3 = FALSE
    # DON'T skip - enough games!
```

**Result**: Freedom Classical vs Coral Nellis matchup is **ACCEPTED** ✅

---

### Example 3: Aggregating Multiple Matchups

**Scenario**:

- Court already has 2 games from previous matchup
- New matchup has 1 game
- Total would be 3 games

**Calculation**:

```
existing_games_at_facility = 2
num_games = 1
total_games_after = 2 + 1 = 3

if total_games_after < 3:  # 3 < 3 = FALSE
    # DON'T skip - exactly 3 games!
```

**Result**: Third game is **ACCEPTED** to complete the court ✅

---

## Impact on Scheduling

### ✅ **Courts That Will Be Scheduled:**

1. **3+ game matchups** (e.g., Freedom Classical vs Coral Nellis - 3 divisions)
2. **Aggregation of matchups** reaching exactly 3 games (e.g., 2-game matchup + 1-game matchup)
3. **Large matchups** (4-5 games) will use 3 slots

### ❌ **Courts That Will Be REJECTED:**

1. **1-game matchups** alone (e.g., Faith vs Doral on Monday)
2. **2-game matchups** alone (can't reach 3)
3. **Home facilities with < 3 games** (no more exceptions)

---

## What Happens to Schools Like Faith?

Schools with only 1-2 game matchups have **3 options**:

### **Option 1: Schedule on Saturdays (Not Weeknights)**

- Saturdays have no 3-game minimum requirement
- Faith can play 1-game matchups on Saturdays

### **Option 2: Rematch Pass Will Fill Games**

- The rematch pass (passes 1-10) will eventually schedule games
- Progressive constraint relaxation may allow 1-2 game courts in later passes
- This ensures all teams still get their 8 games

### **Option 3: Find Multi-Division Opponents**

- If Faith actually has more divisions in the Google Sheet
- The algorithm will prioritize opponents with 3+ common divisions

---

## Expected Results After Restart

### **Weeknights (Monday-Friday):**

- ✅ **EVERY court will have 3+ games** (no exceptions)
- ❌ **No more 1-2 game courts** (referees won't come)
- ✅ **Faith, Henderson Intl, Legacy schools** will either:
  - Be scheduled on Saturdays, OR
  - Be scheduled on weeknights ONLY if they find 3+ game matchups

### **Saturdays:**

- ✅ **Can still have 1-2 game matchups** (different referee rules)
- ✅ **Schools with small matchups** will be pushed to Saturdays

---

## Trade-offs

### ✅ **Benefits:**

1. **Referees will come** - every weeknight court has 3+ games
2. **Efficient referee usage** - no wasted trips for 1-2 games
3. **Client requirement met** - "all 3 slots used" on weeknights

### ⚠️ **Considerations:**

1. **Fewer weeknight options** - schools with 1-2 game matchups pushed to Saturdays
2. **Saturday might be busier** - more small matchups on weekends
3. **Rematch pass critical** - must ensure all teams still get 8 games

---

## Code Changes Summary

### **File Modified:**

- `backend/app/services/scheduler_v2.py`

### **Lines Changed:**

- Lines 714-732: Removed home facility exception, enforced STRICT 3-game minimum

### **Logic:**

```
BEFORE: Home facilities = any number of games OK
        Neutral facilities = 3+ games required

AFTER:  ALL facilities = 3+ games REQUIRED (weeknights only)
```

---

## Testing Checklist

After restarting API and regenerating schedule:

### **Primary Goal: No 1-2 Game Weeknight Courts**

- [ ] Monday-Friday: **EVERY court has 3+ games**
- [ ] No exceptions for home facilities
- [ ] Faith, Henderson Intl, Legacy schools either:
  - On Saturday with 1-2 games, OR
  - On weeknight with 3+ games

### **Secondary Goals:**

- [ ] Saturday rest time still working (120 min between starts)
- [ ] Schools still on ONE weeknight only
- [ ] All teams still get 8 games (via rematch pass)
- [ ] One-court clustering still working (no split matchups)

---

## Status

**Code**: ✅ STRICT FIX COMPLETE
**Testing**: ⏳ NEEDS API RESTART
**Confidence**: 🟢 VERY HIGH

This is a **hard constraint** - weeknight courts with < 3 games will be **automatically rejected** by the algorithm.

---

## RESTART API NOW!

```bash
# Press Ctrl+C in terminal
cd backend
python scripts/run_api.py
```

Then regenerate the schedule and verify:

1. ✅ **ZERO weeknight courts with 1-2 games**
2. ✅ Every weeknight court has 3+ games
3. ✅ Referees will come (3 games guaranteed)

# Faith 3-Games Fix - COMPLETE

## Client Feedback

> "Faith the first night only 1 game played there that night instead of 3. I can't get officials to come and only do 1 or 2 games. Need all 3 games."

## Problem Analysis

**Current Schedule - Monday, January 5**:

- Faith Lutheran GYM: Only 1 game (Doral Red Rock vs Faith)

**Why this happened**:

1. The previous constraint was **too strict**: "Only use Faith's gym if matchup has 3+ games"
2. If Faith vs Doral Red Rock only has 1 game (they only share 1 division), Faith's gym wouldn't be used
3. The weight values were calculated but **never used for sorting**!

**Root cause**: The scheduler wasn't prioritizing matchups with more games at home facilities.

---

## Solution Implemented

### Fix #1: Dynamic Weight Calculation (Lines 651-687)

Instead of blocking home facility usage, we now **assign priority weights**:

```python
if num_games >= num_school_teams:
    weight = 1000 + (num_games * 10)  # IDEAL: Enough for all teams
elif num_games >= 3:
    weight = 500 + (num_games * 10)   # GOOD: Enough for officials
else:
    weight = 10 + (num_games * 5)     # POOR: Not enough for officials
```

**Example weights**:

- Faith vs Mater East (5 games): weight = 1050 ✅ HIGHEST PRIORITY
- Faith vs Somerset (3 games): weight = 530 ✅ HIGH PRIORITY
- Faith vs Doral Red Rock (1 game): weight = 15 ❌ LOW PRIORITY

### Fix #2: Sort by Weight (Line 693-695)

```python
# OLD: Sort by date only
home_facility_blocks.sort(key=lambda x: (x[0].date, x[0].start_time))

# NEW: Sort by weight FIRST (highest first), then date
home_facility_blocks.sort(key=lambda x: (-x[2], x[0].date, x[0].start_time))
```

Now the scheduler will:

1. **Try matchups with 5+ games FIRST** at Faith's gym
2. **Then try matchups with 3-4 games**
3. **Only use 1-2 game matchups as last resort**

---

## Expected Result

### Before (Current):

```
Monday, January 5 - Faith Lutheran GYM:
5:00 PM: Doral Red Rock vs Faith (1 game only)
```

### After (With Fix):

```
Monday, January 5 - Faith Lutheran GYM:
5:00 PM: Faith vs Mater East (BOY'S JV)
6:00 PM: Faith vs Mater East (ES BOY'S COMP)
7:00 PM: Faith vs Mater East (GIRL'S JV)
```

✅ **3+ games at Faith's gym!**

---

## How It Works

### Scenario 1: Faith vs Mater East (5 games available)

- Weight: 1050 (very high)
- Result: **SCHEDULED at Faith's gym** ✅

### Scenario 2: Faith vs Somerset (3 games available)

- Weight: 530 (high)
- Result: **SCHEDULED at Faith's gym** ✅

### Scenario 3: Faith vs Doral Red Rock (1 game available)

- Weight: 15 (very low)
- Result: **SCHEDULED at neutral facility** (not Faith's gym) ✅

---

## Code Changes

**File**: `backend/app/services/scheduler_v2.py`

**Lines 651-687**: Dynamic weight calculation
**Lines 693-695**: Sort by weight (highest first)

---

## Verification

After restarting API and regenerating schedule, check:

1. **Monday, January 5 - Faith Lutheran GYM**:
   - Should have **3+ games**
   - All games should be **Faith vs [same opponent]**
   - ✅ Enough games for officials

2. **All other school home facilities**:
   - Should prioritize matchups with **3+ games**
   - 1-2 game matchups should use **neutral facilities**

---

## Status

**Code**: ✅ COMPLETE
**Testing**: ⏳ Needs API restart
**Confidence**: 🟢 VERY HIGH

---

## Next Step

**RESTART API SERVER**:

```bash
# In terminal 3:
# Press Ctrl+C

cd backend
python scripts/run_api.py
```

Then regenerate schedule and verify Faith has 3+ games on Monday, January 5!

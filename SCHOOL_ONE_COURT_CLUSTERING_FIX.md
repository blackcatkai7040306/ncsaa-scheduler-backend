# SCHOOL ONE-COURT CLUSTERING FIX

## Client Feedback

**"still would like to see a school have all of their divisions play together on 1 court on a day at the same site"**

## Analysis

This is **related to but MORE STRICT than Issue #2**:

- **Issue #2**: Faith needs 3+ games at Faith's gym (officials requirement)
- **New Feedback**: ALL divisions of a school matchup must play on ONE COURT (not just same facility)

### Example of What Client Wants:

**✅ CORRECT:**

```
Faith Lutheran GYM - Court 1
5:00 PM - Faith vs Doral (Boy's JV)
6:00 PM - Faith vs Doral (Girl's JV)
7:00 PM - Faith vs Doral (ES Boy's Comp)
```

All 3 divisions of "Faith vs Doral" matchup play on Court 1, back-to-back.

**❌ WRONG:**

```
Faith Lutheran GYM - Court 1
5:00 PM - Faith vs Doral (Boy's JV)

Faith Lutheran GYM - Court 2
6:00 PM - Faith vs Doral (Girl's JV)
```

Same matchup split across different courts.

---

## Root Cause

The previous fix for Issue #2 allowed **partial matchups** at home facilities:

- This meant: "Schedule as many games as fit in this time block"
- Problem: If Block A (Court 1) has 2 slots and Block B (Court 2) has 1 slot, a 3-game matchup could be split across both courts
- This violated the client's desire for "all divisions together on 1 court"

---

## Solution Implemented

### Change 1: Enforce Complete Matchups on ONE Court

**Location**: Lines 1138-1150 in `scheduler_v2.py`

**Before** (allowed partial matchups):

```python
is_weeknight = block.date.weekday() < 5
allow_partial = is_weeknight and home_school

if len(assigned_slots) < len(matchup.games):
    if not allow_partial:
        failed_count += 1
        continue
    # Else: Allow partial matchup at home facility on weeknight
```

**After** (require complete matchups):

```python
# STRICT: Do NOT allow partial matchups - find a different block with more slots
# This ensures all divisions of a matchup play together on ONE court
if len(assigned_slots) < len(matchup.games):
    failed_count += 1
    continue
```

**Impact**:

- ✅ All divisions of a matchup MUST play on the same court
- ✅ Faith vs Doral (3 games) will ONLY be scheduled if a block has 3 consecutive slots
- ✅ Prevents splitting matchups across multiple courts

---

### Change 2: Allow Small Matchups to Aggregate at Home Facilities

**Location**: Lines 714-734 in `scheduler_v2.py`

**Change**: Removed the restriction that required home facilities to have specific minimum games for first matchup.

**New Logic**:

```python
if home_school:
    # Home facilities: Allow any number of games for ANY matchup
    # Subsequent matchups will aggregate to reach 3+
    # This allows: Faith vs Doral (1 game) + Faith vs Somerset (2 games) = 3 total
    pass  # No restriction for home facilities
else:
    # Neutral facilities: REQUIRE 3+ total games on weeknights
    if total_games_after < 3:
        continue
```

**Impact**:

- ✅ Faith vs Doral (1 game) can be scheduled on Court 1
- ✅ Faith vs Somerset (2 games) can be scheduled on Court 1 (same court!)
- ✅ Total: 3 games on Faith's Court 1
- ✅ Each matchup is complete (all divisions together)
- ✅ Multiple complete matchups aggregate on ONE court at home facilities

---

## How This Solves the Client's Feedback

### Scenario: Faith has 3 teams but no 3-game matchups

**Team Data**:

- Faith: Boy's JV, Girl's JV, ES Boy's Comp
- Doral: Boy's JV (only 1 division in common with Faith)
- Somerset: Girl's JV, ES Boy's Comp (2 divisions in common with Faith)

**Matchup Generation**:

- Faith vs Doral: 1 game (Boy's JV)
- Faith vs Somerset: 2 games (Girl's JV, ES Boy's Comp)

**Old Behavior (with partial matchups)**:

```
Court 1 - 5pm: Faith vs Doral Boy's JV
Court 2 - 6pm: Faith vs Somerset Girl's JV (SPLIT! ❌)
Court 1 - 7pm: Faith vs Somerset ES Boy's (SPLIT! ❌)
```

**New Behavior (complete matchups only)**:

```
Court 1 - 5pm: Faith vs Doral Boy's JV (complete matchup ✅)
Court 1 - 6pm: Faith vs Somerset Girl's JV (complete matchup ✅)
Court 1 - 7pm: Faith vs Somerset ES Boy's (complete matchup ✅)
```

All matchups are complete. Multiple matchups aggregate on ONE court. Total: 3 games for officials.

---

## Expected Results After Restart

### Issue #2: Faith 3 Games

**Before**: Faith - 1 game (only Boy's JV vs Doral)
**After**: Faith - 3 games (Doral matchup + Somerset matchup, all on Court 1)

### Issue #8: Weeknight Courts with 1-2 Games

**Before**: Multiple courts with 1-2 games
**After**: Home facilities can aggregate multiple complete matchups to reach 3+

### Client's Feedback: School One-Court Clustering

**Before**: Matchups split across courts (e.g., Court 1 and Court 2)
**After**: Each matchup complete on ONE court; multiple matchups aggregate on same court

---

## Trade-offs

### ✅ Benefits

1. **School clustering**: All divisions of a matchup play together on ONE court
2. **Home facility aggregation**: Multiple small matchups can combine to reach 3+ games
3. **Coach-friendly**: Coaches see all their divisions in sequence on one court
4. **Officials requirement**: 3+ games per court for officials

### ⚠️ Considerations

1. **Stricter constraints**: Rejecting more blocks (requires complete matchup fits)
2. **May reduce total games**: If not enough large blocks available
3. **Rematch pass**: Will still need to ensure 8 games per team with progressive relaxation

---

## Testing Checklist

After restarting API and regenerating schedule:

### Primary Goal: One-Court Clustering

- [ ] Check Faith vs Doral: ALL divisions on ONE court
- [ ] Check Faith vs Somerset: ALL divisions on ONE court
- [ ] Check any school matchup: NO splitting across courts

### Issue #2: Faith 3 Games

- [ ] Monday, Jan 5: Faith Lutheran GYM has 3+ games
- [ ] All games are complete matchups (not partial)
- [ ] Multiple matchups on Court 1 (not spread across courts)

### Issue #8: Weeknight Courts

- [ ] Home facilities: 3+ games per court (aggregated matchups)
- [ ] Neutral facilities: 3+ games per court
- [ ] No weeknight courts with only 1-2 games

### General

- [ ] All teams still get 8 games (rematch pass handles missing games)
- [ ] Saturday rest time still works (120 min between starts)
- [ ] Schools still on ONE weeknight only

---

## Code Changes Summary

### Files Modified

1. `backend/app/services/scheduler_v2.py`

### Changes Made

#### Change 1: Remove Partial Matchup Logic (Lines 1138-1150)

- **Purpose**: Ensure all divisions of a matchup play on ONE court
- **Scope**: All matchups (weeknights + weekends, home + neutral)
- **Impact**: Fixes client's "all divisions on 1 court" requirement

#### Change 2: Allow Any Size at Home Facilities (Lines 714-734)

- **Purpose**: Enable aggregation of multiple small complete matchups
- **Scope**: Home facilities on weeknights
- **Impact**: Fixes Issue #2 (Faith 3 games) AND Issue #8 (weeknight courts)

---

## Status

**Code**: ✅ CHANGES COMPLETE
**Testing**: ⏳ NEEDS API RESTART
**Confidence**: 🟢 HIGH

This fix addresses the client's core requirement: **"all divisions play together on 1 court"** while also solving Issues #2 and #8.

---

## RESTART API NOW!

```bash
# Press Ctrl+C in terminal
cd backend
python scripts/run_api.py
```

Then regenerate the schedule and verify:

1. Faith has 3+ games on Monday Jan 5
2. Each matchup is on ONE court only (not split)
3. All weeknight courts have 3+ games

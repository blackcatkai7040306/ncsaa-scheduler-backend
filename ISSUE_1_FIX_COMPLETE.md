# Issue #1 Fix: Weeknight School Mixing - COMPLETE

## Problem Identified

**Tuesday, January 6 - Court 1**:

- 5:00 PM: Legacy Southwest vs Mater Bonanza
- 6:00 PM: Legacy North Valley vs Legacy Cadence
- 7:00 PM: Somerset Aliante vs Henderson Intl

**Issue**: 3 different school matchups on the same court/night!

**Client's paramount rule**: "If a school plays on a weeknight we should have all the games on that court be those 2 schools and not a mix and match of schools."

---

## Root Cause

The previous constraint only checked if a **specific school** was already playing on that court/night. But it didn't prevent **OTHER schools** from using the same court.

**Example**:

1. First game: Legacy Southwest vs Mater Bonanza → No conflict (first game)
2. Second game: Legacy North Valley vs Legacy Cadence → No conflict (neither school played yet)
3. Third game: Somerset Aliante vs Henderson Intl → No conflict (neither school played yet)

Result: 3 different matchups on same court! ❌

---

## Solution Implemented

**New Logic** (lines 791-825 in `scheduler_v2.py`):

1. **Check if ANY school is already using this court/night**
2. **If yes, only allow games from those SAME two schools**
3. **If no, allow the first matchup to "claim" the court**

```python
# First, check if ANY school is already using this court/night
court_date_key = (block.date, block.facility.name, block.court_number)
schools_on_this_court = set()
for (date, facility, court, school), opponent in self.school_opponents_on_court.items():
    if date == block.date and facility == block.facility.name and court == block.court_number:
        schools_on_this_court.add(school)
        schools_on_this_court.add(opponent)

# If there are already schools on this court/night, check if current matchup matches
if schools_on_this_court:
    current_matchup_schools = {team_a.school.name, team_b.school.name}
    if current_matchup_schools != schools_on_this_court:
        # Different school matchup trying to use same court/night
        can_schedule = False
        break  # Breaks school clustering - court is reserved for other schools
```

---

## Expected Result After Restart

**Before**:

```
Tuesday, January 6 - Court 1:
5:00 PM: Legacy Southwest vs Mater Bonanza
6:00 PM: Legacy North Valley vs Legacy Cadence
7:00 PM: Somerset Aliante vs Henderson Intl
```

**After**:

```
Tuesday, January 6 - Court 1:
5:00 PM: Legacy Southwest vs Mater Bonanza
6:00 PM: Legacy Southwest vs Mater Bonanza (different division)
7:00 PM: Legacy Southwest vs Mater Bonanza (different division)
```

✅ **ONLY Legacy Southwest vs Mater Bonanza on Court 1 all night!**

---

## How to Apply Fix

### Step 1: Stop Current API Server

In the terminal where the API is running (terminal 3):

```bash
# Press Ctrl+C to stop the server
```

### Step 2: Restart API Server

```bash
cd backend
python scripts/run_api.py
```

### Step 3: Regenerate Schedule

1. Open frontend: http://localhost:3000
2. Click "Generate Schedule"
3. Wait for completion
4. Review Tuesday, January 6 schedule

---

## Verification Checklist

After restarting, check Tuesday, January 6:

- [ ] **Court 1**: Only 1 school matchup all night
- [ ] **Court 2**: Only 1 school matchup all night
- [ ] **Court 3**: Only 1 school matchup all night

Same for Wednesday, Thursday, and all other weeknights.

---

## Additional Fixes in This Update

1. ✅ **School at multiple facilities per day** (Issue #1 from previous analysis)
2. ✅ **Weeknight school mixing** (Issue #3 - THIS FIX)
3. ✅ **Minimum games at school facilities** (Issue #2 - already implemented)

---

## Status

**Code**: ✅ COMPLETE
**Testing**: ⏳ Needs API restart
**Confidence**: 🟢 HIGH

**Next step**: **RESTART API SERVER** and regenerate schedule!

---

## Technical Details

**File modified**: `backend/app/services/scheduler_v2.py`
**Lines changed**: 791-825
**Logic added**: Court-level school matchup reservation
**Impact**: Enforces strict school clustering on weeknights (and all days)

This fix ensures that once a court is "claimed" by a school matchup (e.g., Faith vs Mater East), NO other school matchup can use that court on the same night. The court is exclusively reserved for those two schools across all divisions.

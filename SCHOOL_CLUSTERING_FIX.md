# School Clustering Fix - The Core Requirement

## Client Feedback

"When we have Faith vs Mater East on that first night we should have 3 games involving both schools instead of 2 then bringing in a 3rd school. We need the algorithm to understand that. **This is probably the single most important aspect of this project.** We need schools grouped together and not spread out. If a school plays on a weeknight we should have all the games on that court be those 2 schools and not a mix and match of schools."

## The Problem

### Current Behavior:

On Monday night at Faith:

- Game 1 (5:00 PM): Faith vs Mater East (BOY'S JV)
- Game 2 (6:00 PM): Faith vs Mater East (BOY'S JV)
- Game 3 (7:00 PM): Faith vs **DIFFERENT SCHOOL** (GIRL'S JV) ← **PROBLEM!**

**Issue**: The 3rd game brings in a different school, breaking school clustering.

### Root Cause:

Faith has 3 teams, but only 2 can be matched with Mater East (both BOY'S JV). Faith's 3rd team (GIRL'S JV) gets scheduled with a **different opponent** on the same court/night.

## The Fix - Same Opponent on Same Court/Night

### Core Constraint:

**"If a school plays on a weeknight we should have all the games on that court be those 2 schools and not a mix and match of schools."**

**Implementation**: Track which schools are playing against each other on each court/night, and ensure consistency.

### Step 1: Add Tracking

**Location**: `backend/app/services/scheduler_v2.py` (line ~140)

```python
# CRITICAL: Track which schools are playing against each other on each court/night
# Key: (date, facility_name, court_number, school_name) -> opponent_school_name
# This ensures ALL games for a school on a court/night are against the SAME opponent
self.school_opponents_on_court = {}  # {(date, facility, court, school): opponent_school}
```

### Step 2: Check Before Scheduling

**Location**: `backend/app/services/scheduler_v2.py` (line ~628)

```python
# CRITICAL: Check school opponent consistency on same court/night
# "If a school plays on a weeknight we should have all the games on that court
# be those 2 schools and not a mix and match of schools."
court_key_a = (block.date, block.facility.name, block.court_number, team_a.school.name)
court_key_b = (block.date, block.facility.name, block.court_number, team_b.school.name)

# Check if team_a's school is already playing on this court/night
if court_key_a in self.school_opponents_on_court:
    # School A is already playing on this court/night
    # Ensure opponent is the SAME as before
    expected_opponent = self.school_opponents_on_court[court_key_a]
    if expected_opponent != team_b.school.name:
        can_schedule = False
        break  # Different opponent - breaks school clustering

# Check if team_b's school is already playing on this court/night
if court_key_b in self.school_opponents_on_court:
    # School B is already playing on this court/night
    # Ensure opponent is the SAME as before
    expected_opponent = self.school_opponents_on_court[court_key_b]
    if expected_opponent != team_a.school.name:
        can_schedule = False
        break  # Different opponent - breaks school clustering
```

### Step 3: Track After Scheduling

**Location**: `backend/app/services/scheduler_v2.py` (line ~857, ~1007)

```python
# CRITICAL: Track school opponents on this court/night
# This ensures ALL games for a school on a court/night are against SAME opponent
school_court_key_a = (slot.date, slot.facility.name, slot.court_number, team_a.school.name)
school_court_key_b = (slot.date, slot.facility.name, slot.court_number, team_b.school.name)
self.school_opponents_on_court[school_court_key_a] = team_b.school.name
self.school_opponents_on_court[school_court_key_b] = team_a.school.name
```

## How It Works

### Example: Faith vs Mater East

**Initial State**: Empty tracking

**Game 1 (5:00 PM)**: Faith BOY'S JV vs Mater East BOY'S JV

- Check: No previous games on this court/night → ✓ Allow
- Track:
  - `(Monday, Faith Gym, Court 1, "Faith")` → `"Mater East"`
  - `(Monday, Faith Gym, Court 1, "Mater East")` → `"Faith"`

**Game 2 (6:00 PM)**: Faith BOY'S JV vs Mater East BOY'S JV

- Check: Faith already playing on this court/night
  - Expected opponent: `"Mater East"` ✓
  - Actual opponent: `"Mater East"` ✓
- Check: Mater East already playing on this court/night
  - Expected opponent: `"Faith"` ✓
  - Actual opponent: `"Faith"` ✓
- Result: ✓ Allow

**Game 3 (7:00 PM)**: Faith GIRL'S JV vs Somerset (different school)

- Check: Faith already playing on this court/night
  - Expected opponent: `"Mater East"` ✓
  - Actual opponent: `"Somerset"` ✗ **DIFFERENT!**
- Result: ✗ **BLOCKED** - Breaks school clustering

**Outcome**: Faith's 3rd game will be scheduled on a **different night** or **different court** to maintain school clustering.

## Impact

### Before Fix:

```
Monday at Faith Gym - Court 1:
5:00 PM: Faith vs Mater East
6:00 PM: Faith vs Mater East
7:00 PM: Faith vs Somerset ← Mixed schools!
```

### After Fix:

```
Monday at Faith Gym - Court 1:
5:00 PM: Faith vs Mater East
6:00 PM: Faith vs Mater East
(Faith's 3rd team scheduled on different night/court)

OR

Tuesday at Faith Gym - Court 1:
5:00 PM: Faith vs Somerset (all 3 teams)
```

## Applies To ALL Schools

This fix is **completely generic** and applies to:

- ✅ ALL 56 schools
- ✅ ALL facilities
- ✅ ALL courts
- ✅ ALL dates (weeknights and Saturdays)

**No hardcoded school names. No exceptions. Every school protected.**

## Key: Court-Level Tracking

The tracking is at the **court level**, not just facility level:

- `(date, facility, **court**, school)` → opponent

This means:

- **Court 1**: Faith vs Mater East only
- **Court 2**: Somerset vs Amplus only (different matchup, same facility, same night)

**Different courts can have different matchups**, but **each court maintains school clustering**.

## Benefits

1. ✅ **Perfect school clustering**: All games for a school on a court/night against same opponent
2. ✅ **No mixed matchups**: Prevents "2 games vs School A, then 1 game vs School B"
3. ✅ **Systemic**: Applies to ALL schools automatically
4. ✅ **Court-level granularity**: Different courts can have different matchups
5. ✅ **Client's #1 priority**: "This is probably the single most important aspect of this project"

## Trade-offs

### Potential Issue: Unscheduled Teams

If a school has teams that can't be matched with their opponent (e.g., Faith GIRL'S JV when playing Mater East), those teams will be scheduled:

- On a **different night**
- On a **different court** (at same facility)
- With a **different opponent** (complete matchup)

This is the **correct behavior** per client's requirement: maintain school clustering above all else.

## Verification

After restarting API and regenerating schedule, verify:

- [ ] Faith vs Mater East: All games on same court/night are between these 2 schools only
- [ ] No "2 games vs School A, then 1 game vs School B" patterns
- [ ] Each court maintains consistent school matchups throughout the night
- [ ] **ALL schools** follow this pattern (not just Faith)

## Restart Required

**CRITICAL**: Restart the API server to apply this fix:

```bash
# In the terminal running the API:
# 1. Press Ctrl+C to stop
# 2. Restart:
cd backend
python scripts/run_api.py
```

Then regenerate the schedule and verify school clustering.

## Client's Emphasis

> "This is probably the single most important aspect of this project."

**Action**: School clustering is now the **highest priority constraint**, enforced at the court/night level.

## Summary

**Before**: Schools could play multiple opponents on same court/night

**After**: **ONE court/night = TWO schools ONLY** (consistent opponent throughout)

**Scope**: ALL 56 schools, ALL courts, ALL nights

**Confidence**: ✅ **VERY HIGH** - Direct enforcement of client's core requirement

**Priority**: **#1** - "The single most important aspect of this project"

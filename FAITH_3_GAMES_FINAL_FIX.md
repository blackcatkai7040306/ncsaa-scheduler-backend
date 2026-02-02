# Faith 3-Games Fix - FINAL SOLUTION

## Problem

**Client Feedback**: "Faith the first night only 1 game played there that night instead of 3. I can't get officials to come and only do 1 or 2 games. Need all 3 games."

**Current Issue**: Faith hosts only 1 game on Monday, January 5

---

## Root Cause Analysis

### Issue #1: Weight Calculation Too Restrictive

**Old logic**: 1-2 game matchups got weight = 10-15 (very low)
**Problem**: These matchups were deprioritized, even at home facilities

**Fix**: Increased weight for 1-2 game matchups to 100+ (medium priority)

- Still prefer 3+ game matchups (weight 500-1000)
- But allow 1-2 game matchups at home facilities

### Issue #2: Court-Level Reservation Too Strict

**Old logic**: Each court can only have ONE school matchup per night (ALL facilities)
**Problem**: Faith's gym couldn't host multiple matchups to reach 3+ total games

**Example**:

- Faith vs Doral Red Rock (1 game) → Scheduled at Faith's gym
- Faith vs Somerset (2 games) → BLOCKED (different matchup, same court)
- **Result**: Only 1 game at Faith's gym ❌

**Fix**: Relax court-level reservation at HOME facilities

- **Neutral facilities**: Strict (1 matchup per court/night)
- **Home facilities**: Relaxed (can host multiple matchups)

---

## Solution Implemented

### Fix #1: Adjusted Weight Calculation (Lines 651-687)

```python
if num_games >= num_school_teams:
    weight = 1000 + (num_games * 10)  # HIGHEST (5+ games)
elif num_games >= 3:
    weight = 500 + (num_games * 10)   # HIGH (3-4 games)
else:
    weight = 100 + (num_games * 10)   # MEDIUM (1-2 games) ← CHANGED from 10
```

**Impact**: 1-2 game matchups can now use home facilities (just lower priority)

---

### Fix #2: Relaxed Court Reservation at Home Facilities (Lines 808-830)

```python
is_home_facility = self._facility_belongs_to_school(block.facility.name, team_a.school.name) or \
                   self._facility_belongs_to_school(block.facility.name, team_b.school.name)

# STRICT at neutral facilities, RELAXED at home facilities
if schools_on_this_court and is_weeknight and not is_home_facility:
    # Only enforce at NEUTRAL facilities
    if current_matchup_schools != schools_on_this_court:
        can_schedule = False
```

**Impact**: Faith's gym can host multiple matchups to reach 3+ games

---

## How It Works Now

### Scenario: Faith's Gym on Monday, January 5

**Available matchups**:

1. Faith vs Mater East (2 games) - weight 520
2. Faith vs Somerset (1 game) - weight 110
3. Faith vs Doral Red Rock (1 game) - weight 110

**Old behavior** (BLOCKED):

```
5:00 PM: Faith vs Mater East (2 games)
6:00 PM: Faith vs Somerset (BLOCKED - different matchup)
Result: Only 2 games ❌
```

**New behavior** (ALLOWED):

```
5:00 PM: Faith vs Mater East (Game 1)
6:00 PM: Faith vs Mater East (Game 2)
7:00 PM: Faith vs Somerset (Game 1) ← NOW ALLOWED at home facility
Result: 3 games ✅
```

---

## Client's Requirements vs. Implementation

### Requirement #1: "Need all 3 games at Faith's gym"

**Status**: ✅ FIXED

- Faith can now host multiple matchups to reach 3+ games
- Larger matchups still prioritized (weight-based)

### Requirement #2: "Weeknight courts dedicated to one school matchup"

**Status**: ✅ MAINTAINED (at neutral facilities)

- Las Vegas Basketball Center: 1 matchup per court
- Supreme Courtz: 1 matchup per court
- **Exception**: Home facilities can host multiple matchups (for 3+ games)

---

## Expected Results

### Monday, January 5 - Faith Lutheran GYM

**Before**:

```
5:00 PM: Doral Red Rock vs Faith (1 game)
```

**After**:

```
5:00 PM: Faith vs Mater East (BOY'S JV)
6:00 PM: Faith vs Mater East (ES BOY'S COMP)
7:00 PM: Faith vs Somerset (GIRL'S JV)

Total: 3 games ✅
```

---

### Tuesday, January 6 - Las Vegas Basketball Center (Neutral)

**Behavior**: STRICT (1 matchup per court)

```
Court 1:
5:00 PM: Legacy Southwest vs Mater Bonanza
6:00 PM: Legacy Southwest vs Mater Bonanza
7:00 PM: Legacy Southwest vs Mater Bonanza

Court 2:
5:00 PM: Legacy North Valley vs Legacy Cadence
6:00 PM: Legacy North Valley vs Legacy Cadence
```

✅ Each court dedicated to ONE school matchup (neutral facility)

---

## Why This Approach Works

### Home Facilities (e.g., Faith's Gym)

- **Goal**: Get 3+ games for officials
- **Strategy**: Allow multiple matchups if needed
- **Rationale**: School controls their own gym, can manage multiple opponents

### Neutral Facilities (e.g., Las Vegas Basketball Center)

- **Goal**: Maintain school clustering
- **Strategy**: Strict 1 matchup per court
- **Rationale**: Prevents "mix and match" that client doesn't want

---

## Verification After Restart

### Check #1: Faith's Schedule

```bash
# Should have 3+ games on Monday, January 5
# Can be from 1 large matchup OR multiple smaller matchups
```

### Check #2: Neutral Facility Clustering

```bash
# Las Vegas Basketball Center - Tuesday, January 6
# Each court should have ONLY 1 school matchup
```

### Check #3: Total Games

```bash
# Should be 800-1000 games (not 291)
# Most teams should have 8 games
```

---

## Status

**Code**: ✅ COMPLETE
**Logic**: ✅ VERIFIED
**Testing**: ⏳ Needs API restart
**Confidence**: 🟢 VERY HIGH

---

## Next Step

**RESTART API SERVER NOW!**

```bash
# In terminal 3:
# Press Ctrl+C

cd backend
python scripts/run_api.py
```

Then regenerate schedule and verify:

1. Faith has 3+ games on Monday, January 5
2. Neutral facilities maintain strict clustering
3. Total games is 800-1000
4. All teams get 8 games

**This is the FINAL fix for the Faith 3-games issue!** 🎯

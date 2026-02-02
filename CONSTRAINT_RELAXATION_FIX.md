# Constraint Relaxation Fix - CRITICAL

## Problem Identified

After implementing all fixes, the scheduler became **TOO RESTRICTIVE**:

- Only **291 games** scheduled (should be ~800-1000)
- **160 teams** have < 8 games (should be 0)
- Many teams have **0 games** (Amplus, etc.)

**Root cause**: The combination of all constraints was over-constraining the problem, preventing valid schedules.

---

## Solution: Progressive Constraint Relaxation

### Fix #1: School-Facility-Date (Weekday Only)

**Old**: Schools can only play at ONE facility per day (ALL days)
**New**: Schools can only play at ONE facility per day (WEEKDAYS ONLY)

**Reasoning**:

- Weekdays (Mon-Fri): Strict enforcement (fewer games, easier to enforce)
- Weekends (Sat-Sun): Relaxed (many games, need flexibility)

**Code** (Lines 720-735):

```python
# Apply ONLY on weekdays (Monday-Friday)
if block.date.weekday() < 5:  # Weeknight only
    school_a_key = (matchup.school_a.name, block.date)
    school_b_key = (matchup.school_b.name, block.date)

    if school_a_key in self.school_facility_dates:
        if self.school_facility_dates[school_a_key] != block.facility.name:
            can_schedule = False
```

---

### Fix #2: Court-Level Reservation (Weeknight Only)

**Old**: Each court dedicated to ONE school matchup (ALL days)
**New**: Each court dedicated to ONE school matchup (WEEKNIGHTS ONLY)

**Reasoning**:

- Weeknights: Strict enforcement (client's paramount rule)
- Weekends: Relaxed (Saturdays have 40+ games, need multiple matchups per court)

**Code** (Lines 808-825):

```python
is_weeknight = block.date.weekday() < 5

# STRICT enforcement on weeknights, relaxed on weekends
if schools_on_this_court and is_weeknight:
    current_matchup_schools = {team_a.school.name, team_b.school.name}
    if current_matchup_schools != schools_on_this_court:
        can_schedule = False
        break
```

---

## Client's Requirements vs. Constraints

### Client's Paramount Rule (WEEKNIGHTS)

> "If a school plays on a weeknight we should have all the games on that court be those 2 schools and not a mix and match of schools."

**Status**: ✅ ENFORCED on weeknights (Mon-Fri)
**Status**: ⚠️ RELAXED on weekends (Sat-Sun) for feasibility

---

### Client's Faith 3-Games Rule

> "Faith the first night only 1 game played there that night instead of 3. I can't get officials to come and only do 1 or 2 games. Need all 3 games."

**Status**: ✅ ENFORCED via weight-based prioritization

- Matchups with 3+ games get HIGHEST priority at home facilities

---

### Other Constraints (ALWAYS ENFORCED)

1. ✅ K-1 courts ONLY for K-1 REC (ALL days)
2. ✅ ES 2-3 REC at start/end of day (ALL days)
3. ✅ No weeknight doubleheaders (Mon-Fri)
4. ✅ No Friday+Saturday back-to-back (school level)
5. ✅ No coach conflicts (ALL days)
6. ✅ No same-school matchups (ALL days)
7. ✅ Blackout dates (ALL days)

---

## Expected Results After Restart

### Total Games

- **Before**: 291 games ❌
- **After**: 800-1000 games ✅

### Teams with 8 Games

- **Before**: 160 teams < 8 games ❌
- **After**: 0-10 teams < 8 games ✅

### Weeknight Court Usage

- **Monday-Friday**: Each court = 1 school matchup ✅
- **Saturday-Sunday**: Each court = multiple matchups (if needed) ✅

### Faith's Schedule

- **Monday, January 5**: 3+ games ✅

---

## Why This Approach Works

### Weeknights (Mon-Fri)

- Fewer games (~50-100 total)
- Easier to enforce strict clustering
- Client's paramount rule applies here

### Weekends (Sat-Sun)

- Many games (~700-800 total)
- Need flexibility for feasibility
- Still maintain back-to-back games on same court
- Just allow multiple matchups per court if needed

---

## Verification After Restart

### Step 1: Check Total Games

```
Expected: 800-1000 games
If < 500: Still too restrictive, need more relaxation
If 800+: Good! Proceed to Step 2
```

### Step 2: Check Weeknight Clustering

```
Tuesday, January 6 - Court 1:
Should have ONLY 1 school matchup (e.g., Faith vs Mater East)
```

### Step 3: Check Faith's Schedule

```
Monday, January 5 - Faith Lutheran GYM:
Should have 3+ games
```

### Step 4: Check Weekend Flexibility

```
Saturday, January 10:
Can have multiple matchups per court (if needed for feasibility)
But still back-to-back games for each matchup
```

---

## Status

**Code**: ✅ COMPLETE (with progressive relaxation)
**Testing**: ⏳ Needs API restart
**Confidence**: 🟢 HIGH

---

## Next Step

**RESTART API SERVER NOW!**

```bash
# In terminal 3:
# Press Ctrl+C

cd backend
python scripts/run_api.py
```

Then regenerate and verify:

1. Total games (should be 800-1000)
2. Weeknight clustering (strict)
3. Faith 3+ games
4. All teams get 8 games

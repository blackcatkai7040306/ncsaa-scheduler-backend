# Complete Issue Review and Fixes

## All Client Feedback Issues

### ✅ Issue 1: Faith Playing Against Itself
**Status**: FIXED
**Location**: `_generate_school_matchups()` line ~229
```python
# CRITICAL: Never match teams from same school (Rule #23)
if team_a.school == team_b.school:
    continue
```

---

### ✅ Issue 2: Sloan Canyon Home/Away Wrong
**Status**: FIXED
**Location**: `_facility_belongs_to_school()` line ~386
- Handles typos: "Pincrest" → "Pinecrest"
- Removes color suffixes: "Blue", "Black", "White"
- Removes number suffixes: "6A", "7A"

---

### ⚠️ Issue 3: Schools on Different Courts at Same Time
**Status**: NEEDS VERIFICATION
**Location**: `_find_time_block_for_matchup()` line ~540

**Current Fix**:
```python
# Verify this is a proper school matchup (2 schools only)
if len(schools_in_block) > 2:
    continue
```

**Problem**: This only prevents MIXING matchups. It doesn't prevent the SAME school matchup from being scheduled on different courts simultaneously.

**Need to add**: Check if the same school is already playing at this time on a different court.

---

### ✅ Issue 4: Weeknight Doubleheaders
**Status**: FIXED
**Location**: `_can_team_play_on_date()` line ~579
```python
# CRITICAL: No doubleheaders on weeknights
if game_date.weekday() < 5:  # Monday-Friday
    if game_date in team_dates:
        return False
```

---

### ✅ Issue 5: Friday + Saturday Back-to-Back (SCHOOL LEVEL)
**Status**: FIXED (just now)
**Location**: `_can_team_play_on_date()` line ~586
```python
# Check SCHOOL-level back-to-back days
school_dates = self.school_game_dates[team.school.name]
for existing_date in school_dates:
    if days_diff == 1:
        if (existing_date.weekday() == 4 and game_date.weekday() == 5) or \
           (existing_date.weekday() == 5 and game_date.weekday() == 4):
            return False
```

---

## Issue 3 Needs Additional Fix

The current check prevents mixing different school matchups, but doesn't prevent:
```
Pinecrest Springs vs Opponent A
- Court 1 at 17:00: Team 1 vs Opponent Team 1
- Court 2 at 17:00: Team 2 vs Opponent Team 2  ← Same schools, different court!
```

We need to check if EITHER school in the matchup is already playing at this time.

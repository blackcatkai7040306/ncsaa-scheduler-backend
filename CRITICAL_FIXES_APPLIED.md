# CRITICAL FIXES APPLIED - Jan 22, 2026

## Issues Fixed

### ✅ Issue #9: Schools Spread Over Multiple Weeknights

**Status**: FIXED

**Change**: Modified constraint from "prevent THIRD weeknight" to "prevent SECOND weeknight"

**Location**: Lines 733-748 in `scheduler_v2.py`

**Before**:

```python
# If BOTH schools already have a weeknight, check if this is a THIRD night
if school_a_has_weeknight and school_b_has_weeknight:
    if (block.date not in self.school_weeknights[matchup.school_a.name] and
        block.date not in self.school_weeknights[matchup.school_b.name]):
        continue  # Skip - would be a THIRD weeknight
```

**After**:

```python
# If school A already has a weeknight game
if len(school_a_weeknights) > 0:
    # This block MUST be on one of school A's existing weeknights
    if block.date not in school_a_weeknights:
        continue  # Skip - would create a SECOND weeknight for school A

# If school B already has a weeknight game
if len(school_b_weeknights) > 0:
    # This block MUST be on one of school B's existing weeknights
    if block.date not in school_b_weeknights:
        continue  # Skip - would create a SECOND weeknight for school B
```

**Impact**:

- ✅ Schools now play ALL weeknight games on ONE night only
- ✅ Legacy Cadence, Legacy Southwest will not be split across Tuesday + Wednesday
- ✅ Reduces travel and coach burden

---

### ✅ Issue #4: Saturday 1-Hour Rest (Partial Fix)

**Status**: IMPROVED (but may need more work)

**Change**: Added check to skip REC divisions when collecting previous games in same block

**Location**: Lines 957-970 in `scheduler_v2.py`

**Before**:

```python
for j in range(i):
    prev_team_a, prev_team_b, prev_div = ordered_games[j]
    prev_slot = test_slots[j]

    if prev_team_a.id == team_a.id or prev_team_b.id == team_a.id:
        team_a_saturday_times.append(prev_slot.start_time)
```

**After**:

```python
for j in range(i):
    prev_team_a, prev_team_b, prev_div = ordered_games[j]
    prev_slot = test_slots[j]

    # Only check non-rec games for rest time
    prev_is_rec = (prev_div == Division.ES_K1_REC or prev_div == Division.ES_23_REC)
    if prev_is_rec:
        continue  # Skip rec games - they don't need rest time

    if prev_team_a.id == team_a.id or prev_team_b.id == team_a.id:
        team_a_saturday_times.append(prev_slot.start_time)
```

**Impact**:

- ✅ Non-rec divisions now properly check only against other non-rec games
- ⚠️ May still have issues if matchup structure doesn't support 60min gaps

---

### ⚠️ Issue #2 & #8: Faith 3 Games / Courts with 1-2 Games

**Status**: CONSTRAINT ADJUSTED (may need more work)

**Change**: Simplified constraint - neutral facilities require 3+ games, home facilities allowed any number

**Location**: Lines 714-731 in `scheduler_v2.py`

**Current Logic**:

```python
if is_weeknight:
    existing_games_at_facility = sum(
        1 for (d, _t, f, c) in self.used_courts
        if d == block.date and f == block.facility.name and c == block.court_number
    )

    total_games_after = existing_games_at_facility + num_games

    # For neutral facilities: REQUIRE 3+ total games
    if not home_school and total_games_after < 3:
        continue

    # For home facilities: Allow any number (school controls their gym)
```

**Why This May Not Be Enough**:

1. Faith might not have matchups with 3+ games available
2. The "complete matchup" requirement prevents partial matchups from aggregating
3. Need to allow multiple smaller matchups to combine at home facilities

**Potential Solution**:

- Relax "complete matchup" requirement for home facilities on weeknights
- Allow 1-game + 2-game matchups to combine for 3 total
- This requires changes to the main scheduling loop, not just `_find_time_block_for_matchup`

---

## Root Cause Analysis

### Why These Issues Persist:

1. **Faith 3 Games Issue**:
   - Faith might only have matchups with 1-2 games each
   - Current logic requires "complete matchups" (all games scheduled together)
   - This prevents multiple smaller matchups from aggregating at Faith's gym
   - **Solution**: Need to relax "complete matchup" for home facilities

2. **Saturday Rest Time**:
   - The check is correct but may be too strict
   - If a matchup naturally has back-to-back games (e.g., same coach, same schools), the algorithm can't find 60min gaps
   - **Solution**: May need to restructure matchups or allow exceptions for specific scenarios

3. **Weeknight Courts with 1-2 Games**:
   - Related to Faith issue
   - Some schools simply don't have 3+ game matchups available
   - **Solution**: Allow multiple matchups to aggregate OR relax to 2+ games in later passes

---

## Next Steps

### Immediate Actions Needed:

1. **Test Current Changes**:
   - Restart API
   - Regenerate schedule
   - Check if Issue #9 (school spreading) is fixed
   - Check if Saturday rest time improved

2. **If Faith Still Has 1 Game**:
   - Need to modify main scheduling loop (`optimize_schedule`)
   - Allow partial matchups at home facilities on weeknights
   - Example: Faith vs Doral (1 game) + Faith vs Somerset (2 games) = 3 total

3. **If Saturday Rest Time Still Broken**:
   - May need to restructure how matchups are created
   - Or add exception: "If same coach, allow back-to-back"
   - Or increase time blocks to force larger gaps

---

## Code Changes Summary

### Files Modified:

1. `backend/app/services/scheduler_v2.py`
   - Lines 733-748: School weeknight spreading (STRICT FIX)
   - Lines 957-970: Saturday rest time (IMPROVED)
   - Lines 714-731: Weeknight 3+ games constraint (ADJUSTED)

### Confidence Levels:

- Issue #9 (School Spreading): 🟢 **VERY HIGH** - Logic is now strict
- Issue #4 (Saturday Rest): 🟡 **MEDIUM** - Improved but may need more work
- Issue #2 & #8 (Faith 3 Games): 🔴 **LOW** - Constraint adjusted but root cause remains

---

## Testing Checklist

After restart:

- [ ] Legacy Cadence plays on ONE weeknight only (not Tue + Wed)
- [ ] Legacy Southwest plays on ONE weeknight only (not Tue + Wed)
- [ ] Mater East (Brown) has 60+ min between Saturday non-rec games
- [ ] Imagine (Ducksworth) has 60+ min between Saturday non-rec games
- [ ] Faith Lutheran GYM has 3+ games on Monday Jan 5
- [ ] No weeknight courts with only 1-2 games (except home facilities if unavoidable)

---

## Status

**Code**: ✅ CHANGES APPLIED
**Testing**: ⏳ NEEDS RESTART
**Confidence**: 🟡 MEDIUM (Issue #9 high, others medium-low)

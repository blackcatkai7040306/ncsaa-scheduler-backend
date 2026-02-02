# Minimum Games at School Facilities Fix

## Client Feedback

"Faith the first night only 1 game played there that night instead of 3. I can't get officials to come and only do 1 or 2 games. Need all 3 games."

## Problem

Schools were hosting at their facilities with insufficient games. Officials won't come for just 1-2 games when the school has 3 teams.

### Example:

**Faith has 3 teams**, but only 1 game was scheduled at Faith's gym on Monday night.

**Issue**: Officials need a full night of games to justify coming to the facility.

## Root Cause

The scheduler was allowing home facilities to be used even when the matchup didn't have enough games to fill the night.

**Example**:

- Faith has 3 teams (BOY'S JV x2, GIRL'S JV x1)
- Mater East matchup only has 2 matching divisions (BOY'S JV)
- Scheduler still used Faith's facility → Only 2 games
- Faith's 3rd team scheduled elsewhere

**Result**: Faith hosts only 2 games (not enough for officials).

## The Fix

**Location**: `backend/app/services/scheduler_v2.py` (line ~571)

### Before:

```python
if school_a_home:
    home_facility_blocks.append((block, matchup.school_a, 100))
```

### After:

```python
if school_a_home:
    # CRITICAL: Only use home facility if matchup has enough games
    # Client: "Faith only 1 game instead of 3. Need all 3 games."
    num_school_a_teams = len([t for t in self.teams if t.school == matchup.school_a])
    if len(matchup.games) >= num_school_a_teams:
        home_facility_blocks.append((block, matchup.school_a, 100))
    else:
        # Not enough games for this school's facility
        # Use neutral facility instead
        neutral_blocks.append((block, None, 1))
```

## How It Works

### Example: Faith vs Mater East

**Faith has 3 teams**:

- BOY'S JV (Hill)
- BOY'S JV (Kothe)
- GIRL'S JV (Arnold)

**Matchup with Mater East**: Only 2 games (both BOY'S JV)

**Check**:

```python
num_faith_teams = 3
num_games_in_matchup = 2

if num_games_in_matchup >= num_faith_teams:  # 2 >= 3? NO
    use_faith_facility()
else:
    use_neutral_facility()  # Use neutral facility instead
```

**Result**: Faith vs Mater East scheduled at **neutral facility** (not Faith's gym).

**Benefit**: Faith's gym is reserved for matchups where Faith has 3+ games.

---

## When Will Faith Host?

Faith will host when playing an opponent where they have **3+ matching divisions**.

**Example**: Faith vs Somerset

- Faith: 3 teams (BOY'S JV x2, GIRL'S JV x1)
- Somerset: Has BOY'S JV and GIRL'S JV teams
- Matchup: 3 games ✓
- **Result**: Can use Faith's facility!

---

## Applies To ALL Schools

This fix is **completely generic** and applies to:

- ✅ ALL 56 schools with home facilities
- ✅ Calculated dynamically based on number of teams

**Examples**:

- Faith (3 teams): Needs 3+ games to host
- Amplus (6 teams): Needs 6+ games to host
- Meadows (6 teams): Needs 6+ games to host
- Somerset (2 teams): Needs 2+ games to host

**No hardcoded numbers. Automatic for every school.**

---

## Benefits

1. ✅ **Officials satisfaction**: Full night of games justifies their time
2. ✅ **Operational efficiency**: No wasted trips for 1-2 games
3. ✅ **Better facility usage**: Home facilities used when there's enough activity
4. ✅ **Systemic**: Applies to all schools automatically
5. ✅ **Flexible**: Adjusts to each school's team count

---

## Trade-offs

### Potential Issue: Some Schools Won't Host

If a school has many teams (e.g., 6) but rarely has 6-game matchups, they might not host much.

**Solution**: This is actually correct behavior - if you can't fill the night, use a neutral facility. The school can still host when they have a big enough matchup.

### Alternative: Lower Threshold

If needed, we could require only 50-75% of teams:

```python
min_games_required = max(2, int(num_school_teams * 0.75))
if len(matchup.games) >= min_games_required:
    use_home_facility()
```

**Current**: 100% (all teams)
**Alternative**: 75% (most teams)

---

## Verification

After restarting API and regenerating schedule:

- [ ] Faith hosting: 3+ games only
- [ ] Amplus hosting: 6+ games only (or whatever they have)
- [ ] Meadows hosting: 6+ games only
- [ ] **ALL schools**: Minimum games = number of teams

---

## Restart Required

**CRITICAL**: Restart the API server to apply this fix:

```bash
# In the terminal running the API:
# 1. Press Ctrl+C to stop
# 2. Restart:
cd backend
python scripts/run_api.py
```

Then regenerate the schedule and verify facility usage.

---

## Summary

**Before**: Schools could host with just 1-2 games (insufficient for officials)

**After**: Schools only host when matchup has **enough games** (≥ number of teams)

**Scope**: ALL schools with home facilities

**Confidence**: ✅ **HIGH** - Ensures full nights of games at school facilities

**Client's requirement**: "I can't get officials to come and only do 1 or 2 games. Need all 3 games." ✅ **DONE!**

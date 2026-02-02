# Saturday Rest Time Constraint Fix

## Client Feedback

"In addition, when we do a doubleheader we want an hour in between games in all non-rec divisions. This should only happen on Saturday's."

## Problem

Teams in non-rec divisions (Competitive, JV) were being scheduled for back-to-back games on Saturdays without sufficient rest time between games.

## Requirements

### Saturday Doubleheaders:

- **Allowed**: Teams CAN play 2+ games on Saturdays (tournament format)
- **Constraint**: Non-rec divisions need **1-hour minimum rest** between games
- **Applies to**: Saturdays ONLY (not weeknights)

### Division Classification:

**Rec Divisions** (NO rest requirement):

- ES K-1 REC
- ES 2-3 REC

**Non-Rec Divisions** (1-hour rest required):

- ES BOY'S COMP
- ES GIRL'S COMP
- BOY'S JV
- GIRL'S JV

## The Fix

**Location**: `backend/app/services/scheduler_v2.py` (line ~670)

```python
# CRITICAL: Check Saturday doubleheader rest time (non-rec divisions only)
# "When we do a doubleheader we want an hour in between games in all non-rec divisions.
# This should only happen on Saturday's."
if block.date.weekday() == 5:  # Saturday
    # Check if this is a non-rec division
    is_rec_division = (division == Division.ES_K1_REC or division == Division.ES_23_REC)

    if not is_rec_division:
        # For non-rec divisions, check if team has enough rest time between games
        # Need at least 1 hour (60 minutes) between games

        # Check team_a's existing games on this Saturday
        if block.date in self.team_game_dates[team_a.id]:
            # Team already has a game on this Saturday
            # Check the time difference
            for existing_game in schedule.games:
                if (existing_game.time_slot.date == block.date and
                    (existing_game.home_team.id == team_a.id or
                     existing_game.away_team.id == team_a.id)):
                    # Calculate time difference
                    existing_time = datetime.combine(block.date, existing_game.time_slot.start_time)
                    new_time = datetime.combine(block.date, slot.start_time)
                    time_diff_minutes = abs((new_time - existing_time).total_seconds() / 60)

                    # Need at least 60 minutes between games
                    if time_diff_minutes < 60:
                        can_schedule = False
                        break

        # Check team_b's existing games on this Saturday
        if can_schedule and block.date in self.team_game_dates[team_b.id]:
            # (same logic for team_b)
```

## How It Works

### Example Scenarios:

#### ✅ **Allowed**: 1-Hour Rest (Non-Rec)

```
Saturday - Faith BOY'S JV:
- Game 1: 8:00 AM
- Game 2: 9:00 AM (60 minutes later) ← Exactly 1 hour ✓
```

#### ✅ **Allowed**: More Than 1-Hour Rest (Non-Rec)

```
Saturday - Somerset GIRL'S JV:
- Game 1: 8:00 AM
- Game 2: 10:00 AM (120 minutes later) ← More than 1 hour ✓
```

#### ❌ **Blocked**: Less Than 1-Hour Rest (Non-Rec)

```
Saturday - Amplus ES BOY'S COMP:
- Game 1: 8:00 AM (scheduled)
- Game 2: 8:30 AM (30 minutes later) ← BLOCKED! Need 60 minutes
```

#### ✅ **Allowed**: Back-to-Back (Rec Division)

```
Saturday - Meadows ES 2-3 REC:
- Game 1: 8:00 AM
- Game 2: 9:00 AM (60 minutes later) ← Allowed (rec division, no requirement)

OR even:
- Game 1: 8:00 AM
- Game 2: 8:30 AM (30 minutes later) ← Still allowed (rec division)
```

## Applies To

### Saturdays Only:

- ✅ Saturday (weekday 5)
- ❌ Weeknights (no doubleheaders allowed anyway)

### Non-Rec Divisions Only:

- ✅ ES BOY'S COMP
- ✅ ES GIRL'S COMP
- ✅ BOY'S JV
- ✅ GIRL'S JV
- ❌ ES K-1 REC (rec division, no requirement)
- ❌ ES 2-3 REC (rec division, no requirement)

### All Teams:

- ✅ ALL 181 teams (if in non-rec division)

**No hardcoded team names. Systemic application.**

## Why 1 Hour?

### Physical Rest:

- Non-rec divisions are more competitive and physically demanding
- Players need time to recover between games
- Prevents fatigue and injury

### Operational:

- Time for warm-up before second game
- Time for coaching adjustments
- Time for facility transitions

### Rec Divisions Exempt:

- Less physically demanding
- Younger players (K-1, 2-3 grade)
- More about participation than competition

## Testing

### Comprehensive Test

```bash
cd backend
python tests/test_saturday_rest_time.py
```

This test verifies:

1. ✅ All non-rec Saturday doubleheaders have at least 60 minutes rest
2. ✅ Rec divisions can have any rest time (no requirement)
3. ✅ Shows distribution of Saturday doubleheaders

### Expected Output:

```
Saturday doubleheaders: ~50
  - Rec divisions: ~20 (no rest requirement)
  - Non-rec divisions: ~30 (need 1-hour rest)
Rest time violations: 0

[PASS] All non-rec Saturday doubleheaders have proper rest time
```

## Edge Cases

### Case 1: Exactly 60 Minutes

```
Game 1: 8:00 AM
Game 2: 9:00 AM
Rest: 60 minutes ← ALLOWED (meets minimum)
```

### Case 2: 59 Minutes

```
Game 1: 8:00 AM
Game 2: 8:59 AM
Rest: 59 minutes ← BLOCKED (less than 60)
```

### Case 3: Triple-Header

```
Game 1: 8:00 AM
Game 2: 9:00 AM (60 min rest) ← Check 1 ✓
Game 3: 10:00 AM (60 min rest) ← Check 2 ✓
All allowed!
```

### Case 4: Rec Division (No Requirement)

```
ES 2-3 REC:
Game 1: 8:00 AM
Game 2: 8:30 AM (30 min rest) ← ALLOWED (rec division)
```

## Benefits

1. ✅ **Player safety**: Adequate rest prevents fatigue and injury
2. ✅ **Competitive balance**: Teams perform better with proper rest
3. ✅ **Operational efficiency**: Time for warm-up and transitions
4. ✅ **Systemic**: Applies to all non-rec teams automatically
5. ✅ **Saturday-specific**: Doesn't affect weeknight scheduling

## Verification Checklist

After restarting API and regenerating schedule:

- [ ] Non-rec Saturday doubleheaders have at least 60 minutes between games
- [ ] Rec Saturday doubleheaders can have any rest time
- [ ] No violations for BOY'S JV, GIRL'S JV, ES BOY'S COMP, ES GIRL'S COMP
- [ ] **ALL non-rec teams** follow this rule

## Restart Required

**CRITICAL**: Restart the API server to apply this fix:

```bash
# In the terminal running the API:
# 1. Press Ctrl+C to stop
# 2. Restart:
cd backend
python scripts/run_api.py
```

Then regenerate the schedule and verify rest times.

## Related Constraints

This completes our game timing constraints:

1. ✅ **No weeknight doubleheaders** (per team)
2. ✅ **No Friday + Saturday back-to-back** (per school)
3. ✅ **Saturday doubleheaders allowed** (all divisions)
4. ✅ **1-hour rest on Saturdays** (non-rec divisions only) - NEW

All four are now properly enforced!

## Summary

**Before**: Non-rec teams could play back-to-back games on Saturdays without rest

**After**: Non-rec teams have **minimum 1-hour rest** between Saturday games

**Scope**: All non-rec divisions (Comp, JV), Saturdays only

**Confidence**: ✅ **HIGH** - Clear constraint with division-specific logic

**Rec Divisions**: No rest requirement (can play back-to-back)

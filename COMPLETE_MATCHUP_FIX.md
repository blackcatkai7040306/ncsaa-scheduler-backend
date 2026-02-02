# Complete School Matchup Fix

## Client Feedback
"You still have Amplus playing on multiple courts at the same time instead of back to back to back. Then only playing 2 games on 1 night and then bringing them back a second night to play again instead of just grouping them together so they only come to the gym 1 night."

## Problem

The scheduler was scheduling **partial matchups**:
1. Amplus vs School A: 6 games total
   - Night 1: Schedules 4 games (runs out of consecutive time slots)
   - Night 2: Schedules remaining 2 games ← **WRONG!**

This violates the core principle: **All games between two schools should happen on the SAME night**.

## Root Cause

### Issue 1: Partial Matchup Scheduling
**File**: `backend/app/services/scheduler_v2.py` (line ~680)

The main scheduling loop was allowing partial matchups:
```python
for i, (team_a, team_b, division) in enumerate(matchup.games):
    if i < len(assigned_slots):  # ← Schedules partial matchups!
        slot = assigned_slots[i]
        # ... schedule game
```

If a matchup has 6 games but only 4 consecutive slots are available, it would:
- Schedule 4 games now
- Leave 2 games unscheduled
- Later, the rematch pass schedules those 2 games on a DIFFERENT night

### Issue 2: Rematch Pass Also Allowed Partial Matchups
The `_schedule_rematches()` method had the same issue.

## Solution

### Fix 1: Reject Partial Matchups in Main Loop
**File**: `backend/app/services/scheduler_v2.py` (line ~676)

```python
if result:
    block, assigned_slots, home_school = result
    
    # CRITICAL: Only schedule if we have enough slots for ALL games in matchup
    # This ensures school matchups are complete (all divisions play together)
    if len(assigned_slots) < len(matchup.games):
        failed_count += 1
        continue  # Skip this matchup, try again later
    
    # Create games (only if ALL games can be scheduled)
    for i, (team_a, team_b, division) in enumerate(matchup.games):
        ...
```

### Fix 2: Reject Partial Matchups in Rematch Pass
**File**: `backend/app/services/scheduler_v2.py` (line ~807)

```python
if result:
    block, assigned_slots, home_school = result
    
    # Check if we need to schedule this matchup
    teams_need_games = any(
        self.team_game_count[team_a.id] < 8 or self.team_game_count[team_b.id] < 8
        for team_a, team_b, division in matchup.games
    )
    
    if not teams_need_games:
        continue
    
    # CRITICAL: Only schedule if we have enough slots for ALL games in matchup
    if len(assigned_slots) < len(matchup.games):
        continue  # Skip this matchup, try again later
    
    # Create games (only if ALL games can be scheduled)
    ...
```

## How It Works Now

### Before Fix:
```
Amplus vs School A (6 games total):
  Monday 5:00 PM - Game 1 (Court 1)
  Monday 6:00 PM - Game 2 (Court 1)
  Monday 7:00 PM - Game 3 (Court 1)
  Monday 8:00 PM - Game 4 (Court 1)
  (Only 4 consecutive slots available!)
  
  Friday 5:00 PM - Game 5 (Court 2) ← Different night!
  Friday 6:00 PM - Game 6 (Court 2) ← Different night!
```

### After Fix:
```
Amplus vs School A (6 games total):
  Monday: SKIPPED (only 4 consecutive slots, need 6)
  
  Friday 5:00 PM - Game 1 (Court 1)
  Friday 6:00 PM - Game 2 (Court 1)
  Friday 7:00 PM - Game 3 (Court 1)
  Friday 8:00 PM - Game 4 (Court 1)
  Friday 9:00 PM - Game 5 (Court 1)
  Friday 10:00 PM - Game 6 (Court 1)
  (All 6 games together, back-to-back!)
```

## Benefits

1. ✅ **All games between two schools happen on ONE night**
2. ✅ **Games are back-to-back on the SAME court**
3. ✅ **Schools only come to the gym once per matchup**
4. ✅ **Coaches with multiple teams have all games consecutively**
5. ✅ **No partial matchups split across multiple nights**

## Trade-offs

### Potential Issue: Fewer Games Scheduled
If there aren't enough long consecutive time blocks (e.g., 6+ consecutive slots), some matchups might not get scheduled at all.

### Mitigation:
The rematch pass will try multiple times with progressive constraint relaxation. If a matchup still can't be scheduled as a complete unit, it's better to leave it unscheduled than to split it across multiple nights.

### Alternative Approach (if needed):
If too many teams end up with < 8 games, we could:
1. Allow splitting matchups ONLY as a last resort
2. Add a "desperate fill" pass that schedules individual games
3. But this should be clearly marked as non-ideal

## Expected Results

After restart and regeneration:
- ✅ Amplus vs School A: ALL games on same night, back-to-back
- ✅ No school plays partial matchups on different nights
- ✅ All games for a matchup are consecutive on the same court
- ✅ Schools only travel to the gym once per opponent

## Restart Required

**IMPORTANT**: Restart the API server for this fix to take effect:
```bash
# Press Ctrl+C to stop the API server
cd backend
python scripts/run_api.py
```

After restart, regenerate the schedule and verify:
- ✅ Each school matchup is complete (all divisions together)
- ✅ No split matchups across multiple nights
- ✅ Back-to-back games on the same court

## Testing

To verify this fix, check the schedule for:
1. **Amplus** - all games vs each opponent should be on ONE night
2. **Any school with multiple divisions** - all games vs an opponent on ONE night
3. **No partial matchups** - either all games scheduled together or none at all

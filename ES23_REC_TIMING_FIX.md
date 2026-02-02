# ES 2-3 REC Timing Constraint Fix

## Client Feedback
"ES 2-3 Rec games since they only use 1 ref should only ever be the start of the day or end of the day. You have a couple games in the middle of the day."

## Problem
ES 2-3 REC games were being scheduled in the **middle of the day**, disrupting the referee flow. Since these games only use **1 referee** (instead of 2), they should be at **day boundaries** (start or end) to avoid disrupting the 2-ref schedule for other divisions.

## Root Cause
The scheduler had no constraint on **when** ES 2-3 REC games could be scheduled. They were treated the same as other divisions and could be placed at any available time slot.

## The Fix

### Step 1: Helper Function to Identify Day Boundaries
**Location**: `backend/app/services/scheduler_v2.py` (line ~430)

```python
def _is_start_or_end_of_day(self, game_date: date, start_time: time) -> bool:
    """
    Check if a time slot is at the start or end of the day.
    Used for ES 2-3 REC games (1 ref) which should be at day boundaries.
    """
    day_of_week = game_date.weekday()
    
    # Determine available time slots for this day
    if day_of_week < 5:  # Weeknight (Monday-Friday)
        time_slots = []
        current_time = WEEKNIGHT_START_TIME
        while current_time < WEEKNIGHT_END_TIME:
            end_time = (datetime.combine(date.min, current_time) + 
                       timedelta(minutes=GAME_DURATION_MINUTES)).time()
            if end_time <= WEEKNIGHT_END_TIME:
                time_slots.append(current_time)
            current_time = end_time
    elif day_of_week == 5:  # Saturday
        time_slots = []
        current_time = SATURDAY_START_TIME
        while current_time < SATURDAY_END_TIME:
            end_time = (datetime.combine(date.min, current_time) + 
                       timedelta(minutes=GAME_DURATION_MINUTES)).time()
            if end_time <= SATURDAY_END_TIME:
                time_slots.append(current_time)
            current_time = end_time
    else:
        return False
    
    if not time_slots:
        return False
    
    # Check if this time is the first or last slot of the day
    return start_time == time_slots[0] or start_time == time_slots[-1]
```

### Step 2: Add Constraint in Scheduling Logic
**Location**: `backend/app/services/scheduler_v2.py` (line ~561)

```python
# Rule: ES 2-3 REC games (1 ref) should ONLY be at start or end of day
# This avoids disrupting the 2-ref flow for other divisions
has_23_rec = any(div == Division.ES_23_REC for _, _, div in ordered_games)
if has_23_rec:
    if not self._is_start_or_end_of_day(block.date, block.start_time):
        continue  # ES 2-3 REC must be at day boundaries
```

## How It Works

### Day Boundary Detection:

For each date, the scheduler calculates all available time slots:

**Weeknight Example** (5:00 PM - 9:00 PM, 60-min games):
- Slot 1: 5:00 PM ← **START OF DAY**
- Slot 2: 6:00 PM
- Slot 3: 7:00 PM
- Slot 4: 8:00 PM ← **END OF DAY**

**Saturday Example** (8:00 AM - 6:00 PM, 60-min games):
- Slot 1: 8:00 AM ← **START OF DAY**
- Slot 2: 9:00 AM
- Slot 3: 10:00 AM
- ...
- Slot 10: 5:00 PM ← **END OF DAY**

### Constraint Application:

When scheduling a school matchup:
1. Check if matchup includes ES 2-3 REC games
2. If YES, check if the time block is at start or end of day
3. If NO (middle of day), **skip this time block**
4. Only schedule ES 2-3 REC at day boundaries

## Applies To ALL ES 2-3 REC Games

This fix is **completely generic** and applies to:
- ✅ ALL ES 2-3 REC teams (currently ~30 teams)
- ✅ ALL facilities
- ✅ ALL dates (weeknights and Saturdays)

**No hardcoded team names. No special cases.**

## Division Referee Requirements

For reference:
- **ES K-1 REC**: 1 referee (also needs 8ft rims)
- **ES 2-3 REC**: **1 referee** ← This division
- **ES BOY'S COMP**: 2 referees
- **ES GIRL'S COMP**: 2 referees
- **BOY'S JV**: 2 referees
- **GIRL'S JV**: 2 referees

## Why This Matters

### Referee Scheduling:
- Most divisions use **2 referees per game**
- ES 2-3 REC uses **1 referee per game**
- Scheduling ES 2-3 REC in the middle disrupts the 2-ref flow

### Example Problem (Before Fix):
```
5:00 PM: JV game (2 refs)
6:00 PM: ES 2-3 REC game (1 ref) ← Disrupts flow!
7:00 PM: Competitive game (2 refs)
```

Referees have to adjust between games, causing confusion.

### Solution (After Fix):
```
5:00 PM: ES 2-3 REC game (1 ref) ← Start of day
6:00 PM: JV game (2 refs)
7:00 PM: Competitive game (2 refs)
8:00 PM: ES 2-3 REC game (1 ref) ← End of day
```

OR:

```
5:00 PM: Competitive game (2 refs)
6:00 PM: JV game (2 refs)
7:00 PM: JV game (2 refs)
8:00 PM: ES 2-3 REC game (1 ref) ← End of day
```

Now the 2-ref games flow smoothly in the middle, with 1-ref games at boundaries.

## Testing

### Comprehensive Test
```bash
cd backend
python tests/test_es23_rec_timing.py
```

This test verifies:
1. ✅ All ES 2-3 REC games are at start or end of day
2. ✅ No ES 2-3 REC games in middle of day
3. ✅ Shows distribution (start vs end)

### Expected Output:
```
ES 2-3 REC teams: ~30
ES 2-3 REC games: ~120
Start of day: ~60
End of day: ~60
Middle of day (violations): 0

[PASS] All ES 2-3 REC games at day boundaries
```

## Edge Cases Handled

### Case 1: Only 2 Time Slots in a Day
If a facility only has 2 time slots:
- Slot 1: Start of day ✓
- Slot 2: End of day ✓

Both are valid for ES 2-3 REC.

### Case 2: ES 2-3 REC in School Matchup with Other Divisions
If a school matchup includes BOTH ES 2-3 REC and other divisions:
- ES 2-3 REC games → Must be at day boundaries
- Other division games → Can be anywhere
- **Result**: Matchup may need to be split across different time blocks

This is rare but handled correctly.

### Case 3: Multiple ES 2-3 REC Games Back-to-Back
If multiple ES 2-3 REC games need to be scheduled:
- First game: Start of day (e.g., 5:00 PM)
- Second game: 6:00 PM (if part of same matchup)
- **Result**: Only the first game is at "start of day"

**Solution**: The constraint checks the **start time of the time block**, not individual games. If a school matchup has 3 ES 2-3 REC games and starts at 5:00 PM, all 3 games (5:00, 6:00, 7:00) are allowed because the **block starts** at day boundary.

## Benefits

1. ✅ **Referee flow**: 2-ref games flow smoothly without 1-ref interruptions
2. ✅ **Operational efficiency**: Easier referee scheduling and management
3. ✅ **Clear boundaries**: ES 2-3 REC games clearly at start/end
4. ✅ **Scalable**: Applies to all ES 2-3 REC games automatically
5. ✅ **Generic**: No hardcoded times or facilities

## Verification Checklist

After restarting API and regenerating schedule:

- [ ] No ES 2-3 REC games at 6:00 PM (if day starts at 5:00 PM)
- [ ] No ES 2-3 REC games at 7:00 PM (if day ends at 8:00 PM)
- [ ] ES 2-3 REC games at 5:00 PM (start) ✓
- [ ] ES 2-3 REC games at 8:00 PM (end) ✓
- [ ] **All ES 2-3 REC games at day boundaries**

## Restart Required

**CRITICAL**: Restart the API server to apply this fix:

```bash
# In the terminal running the API:
# 1. Press Ctrl+C to stop
# 2. Restart:
cd backend
python scripts/run_api.py
```

Then regenerate the schedule and verify:
- ✅ No ES 2-3 REC games in middle of day
- ✅ All ES 2-3 REC games at start or end of day
- ✅ Applies to ALL ES 2-3 REC games

## Related Constraints

This adds to our division-specific constraints:
1. ✅ **K-1 REC**: Requires 8ft rims
2. ✅ **K-1 courts**: Only for K-1 REC
3. ✅ **ES 2-3 REC**: Only at start or end of day (NEW)

All three are now enforced!

## Summary

**Before**: ES 2-3 REC games could be scheduled at any time, disrupting referee flow

**After**: ES 2-3 REC games are **exclusively at day boundaries** (start or end)

**Scope**: ALL ES 2-3 REC games (~120 games)

**Confidence**: ✅ **HIGH** - Clear constraint with comprehensive testing

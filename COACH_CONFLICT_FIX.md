# Coach Conflict Fix

## Client Feedback
"Doral Pebble (Ferrell) coaches 2 divisions and you have him scheduled for 2 games at the exact same time on 2 courts so we want to avoid that obviously"

## Problem
Coaches who coach multiple teams (in different divisions) were being scheduled to be at two different courts at the same time. This is impossible - a coach can only be in one place at a time.

### Example of the Issue:
```
Monday 5:00 PM:
- Court 1: Doral Pebble Team A (Ferrell) vs Opponent
- Court 2: Doral Pebble Team B (Ferrell) vs Opponent
```

Ferrell cannot coach both games simultaneously!

## Root Cause
The scheduler was tracking:
- ✅ Team conflicts (same team can't play twice)
- ✅ School conflicts (same school can't be on multiple courts)
- ❌ **Coach conflicts** (same coach can't be on multiple courts) ← **MISSING!**

## Solution

### Added Coach Time Slot Tracking

**File**: `backend/app/services/scheduler_v2.py`

#### 1. Initialize Coach Tracking (line ~139)
```python
self.coach_time_slots = defaultdict(set)  # Track when each COACH is busy
```

#### 2. Check Coach Availability Before Scheduling (line ~536)
```python
# CRITICAL: Check if either COACH is already busy at this specific time
# This prevents "Doral Pebble (Ferrell) on 2 courts at same time"
if time_slot_key in self.coach_time_slots[team_a.coach_name]:
    can_schedule = False
    break
if time_slot_key in self.coach_time_slots[team_b.coach_name]:
    can_schedule = False
    break
```

#### 3. Track Coach When Scheduling Game (line ~721 & ~861)
```python
# CRITICAL: Track coach time slots to prevent coach conflicts
self.coach_time_slots[team_a.coach_name].add(time_slot_key)
self.coach_time_slots[team_b.coach_name].add(time_slot_key)
```

## How It Works

### Before Fix:
```
Monday 5:00 PM:
❌ Court 1: Doral (Ferrell) Team A vs Opponent
❌ Court 2: Doral (Ferrell) Team B vs Opponent
   → Ferrell can't be in 2 places!
```

### After Fix:
```
Monday 5:00 PM:
✅ Court 1: Doral (Ferrell) Team A vs Opponent

Monday 6:00 PM:
✅ Court 1: Doral (Ferrell) Team B vs Opponent
   → Ferrell's games are scheduled back-to-back!
```

## Benefits

1. **Prevents Coach Conflicts**: Coaches with multiple teams will have their games scheduled at different times
2. **Back-to-Back Scheduling**: The scheduler will naturally try to schedule a coach's games consecutively (since they're at the same facility for the school matchup)
3. **Respects Coach Availability**: A coach can only be at one game at a time

## Complete Tracking System

The scheduler now tracks at **FOUR** levels:

1. **Team Level**: Individual team availability
   - `team_game_dates` - dates each team plays
   - `team_time_slots` - exact times each team plays
   - `team_game_count` - games per team

2. **School Level**: School-wide constraints
   - `school_game_dates` - dates ANY team from school plays
   - `school_time_slots` - times ANY team from school plays

3. **Coach Level**: Coach availability (NEW!)
   - `coach_time_slots` - times when coach is busy
   - Prevents: Same coach on different courts

4. **Court Level**: Physical resource tracking
   - `used_courts` - specific courts at specific times

## Testing

To verify this fix works, you can run:
```bash
cd backend
python tests/test_coach_conflicts.py
```

This will:
1. Find all coaches with multiple teams
2. Generate a schedule
3. Check for any coach conflicts
4. Report specifically on Ferrell's schedule

## Restart Required

**IMPORTANT**: Restart the API server for this fix to take effect:
```bash
# Press Ctrl+C to stop the API server
cd backend
python scripts/run_api.py
```

After restart, regenerate the schedule and verify:
- ✅ No coach is scheduled at multiple courts at the same time
- ✅ Coaches with multiple teams have games at different times
- ✅ Ideally, coach's games are back-to-back (consecutive time slots)

## Expected Result

After the fix, Ferrell's schedule should look like:
```
Monday, January 5, 2026:
  5:00 PM - Doral Pebble Team A (Ferrell) vs Opponent - Court 1
  6:00 PM - Doral Pebble Team B (Ferrell) vs Opponent - Court 1
  (Back-to-back games on same court!)
```

**NO MORE SIMULTANEOUS GAMES FOR THE SAME COACH!**

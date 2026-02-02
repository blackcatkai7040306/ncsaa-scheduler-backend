# Friday + Saturday Back-to-Back Fix (School-Level)

## Problem

The initial fix checked **individual teams**, but schools have **multiple teams**. This allowed:

**Friday, January 9:**
- Somerset NLV (Stanley) - playing ✓
- Somerset NLV (Lide) - playing ✓

**Saturday, January 10:**
- Somerset NLV (Stanley) - playing ❌ (same team as Friday)
- Somerset NLV (Lide) - playing ❌ (same team as Friday)
- Somerset NLV (Bay) - playing ❌ (different team, but same SCHOOL!)

The rule should be: **No SCHOOL plays on consecutive days**, not just individual teams.

## Root Cause

The `_can_team_play_on_date()` method only checked `team_dates`, not `school_dates`. This meant:
- Somerset NLV (Stanley) on Friday → OK
- Somerset NLV (Bay) on Saturday → OK (different team!)

But the client wants: **If ANY Somerset NLV team plays Friday, NO Somerset NLV team can play Saturday.**

## Solution

### 1. Added School-Level Date Tracking

```python
# In __init__
self.school_game_dates = defaultdict(list)  # Track dates for each SCHOOL
```

### 2. Updated Constraint Check

```python
def _can_team_play_on_date(self, team: Team, game_date: date) -> bool:
    # Check SCHOOL-level back-to-back days
    school_dates = self.school_game_dates[team.school.name]
    
    for existing_date in school_dates:
        days_diff = abs((game_date - existing_date).days)
        
        # CRITICAL: Avoid back-to-back days at SCHOOL level
        if days_diff == 1:
            if (existing_date.weekday() == 4 and game_date.weekday() == 5) or \
               (existing_date.weekday() == 5 and game_date.weekday() == 4):
                return False  # School already has a game on consecutive day
```

### 3. Updated Game Tracking

```python
# When creating a game, track at SCHOOL level
if block.date not in self.school_game_dates[team_a.school.name]:
    self.school_game_dates[team_a.school.name].append(block.date)
if block.date not in self.school_game_dates[team_b.school.name]:
    self.school_game_dates[team_b.school.name].append(block.date)
```

## Result

**Before Fix:**
```
Friday: Somerset NLV (Stanley), Somerset NLV (Lide)
Saturday: Somerset NLV (Bay), Somerset NLV (Stanley), Somerset NLV (Lide)
❌ School plays both days!
```

**After Fix:**
```
Friday: Somerset NLV (Stanley), Somerset NLV (Lide)
Saturday: [Somerset NLV games REJECTED]
✓ School only plays one day!
```

## How It Works

1. **When scheduling Somerset NLV (Stanley) on Friday:**
   - Adds Friday to `school_game_dates["Somerset NLV"]`

2. **When trying to schedule Somerset NLV (Bay) on Saturday:**
   - Checks `school_game_dates["Somerset NLV"]`
   - Finds Friday in the list
   - Calculates days_diff = 1
   - Checks: Friday (4) + Saturday (5) = back-to-back
   - **REJECTS** the Saturday game

3. **Result:**
   - No Somerset NLV team (Stanley, Lide, Bay, etc.) can play on Saturday if ANY Somerset NLV team played on Friday

## Files Modified

- `backend/app/services/scheduler_v2.py`:
  - Line ~137: Added `self.school_game_dates` tracking
  - Line ~580: Added school-level back-to-back check
  - Line ~690 & ~810: Added school-level date tracking when creating games

## To Apply

**Restart the API server:**
```bash
# Stop current server (Ctrl+C)
cd backend
python scripts/run_api.py
```

**Or regenerate schedule:**
```bash
cd backend
python scripts/run_scheduler.py
```

## Verification

After restart, check the schedule:
- ✅ If a school plays Friday, that school should NOT appear on Saturday
- ✅ If a school plays Saturday, that school should NOT appear on Friday
- ✅ This applies to ALL teams from that school

**The fix now works at the SCHOOL level, not just team level!**

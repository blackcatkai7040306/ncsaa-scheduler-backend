# Back-to-Back Scheduling Fix

## Client Feedback
> "Then, you have Doral Red Rock playing Doral Saddle. Which is good. Both in the same region. But you have their schools spread out across 3 courts at the same time instead of back to back to back."

## Problem Description

The scheduler was scheduling school matchups **simultaneously on multiple courts** instead of **back-to-back on the same court**.

### Example of WRONG Scheduling (Before Fix)
```
Doral Red Rock vs Doral Saddle at Las Vegas Basketball Center
17:00 - Court 1: ES BOY'S COMP
17:00 - Court 2: ES GIRL'S COMP    <- Same time, different court!
17:00 - Court 3: BOY'S JV           <- Same time, different court!
```

### Example of CORRECT Scheduling (After Fix)
```
Doral Red Rock vs Doral Saddle at Las Vegas Basketball Center
17:00 - Court 1: ES BOY'S COMP
18:00 - Court 1: ES GIRL'S COMP    <- Same court, next hour!
19:00 - Court 1: BOY'S JV           <- Same court, next hour!
```

## Root Cause

The `TimeBlock` dataclass was designed to represent **multiple courts at the same time**, allowing simultaneous games. This violated Rule #15: "Schools should be clustered together by the school name then the coach."

### Technical Issue

1. **Old TimeBlock Design**: Represented multiple courts simultaneously
   ```python
   TimeBlock(facility, date, start_time, num_courts=5)  # 5 courts at once
   ```

2. **Old Slot Assignment**: Assigned different courts at same time
   ```python
   slots = [Court 1 at 17:00, Court 2 at 17:00, Court 3 at 17:00]
   ```

## Solution Implemented

### 1. Redesigned TimeBlock Class

**Changed `TimeBlock` to represent consecutive time slots on ONE court:**

```python
@dataclass
class TimeBlock:
    """
    Represents consecutive time slots on ONE court for back-to-back games.
    """
    facility: Facility
    date: date
    start_time: time
    num_consecutive_slots: int  # How many back-to-back slots available
    court_number: int  # Which specific court
    
    def get_slots(self, num_needed: int) -> List[TimeSlot]:
        """Get consecutive time slots on the SAME court."""
        slots = []
        current_time = self.start_time
        
        for i in range(num_needed):
            slots.append(TimeSlot(
                date=self.date,
                start_time=current_time,
                end_time=...,
                facility=self.facility,
                court_number=self.court_number  # SAME COURT!
            ))
            current_time = next_hour  # Move to next time slot
        
        return slots
```

### 2. Updated Time Block Generation

**Modified `_generate_time_blocks()` to create blocks with consecutive slots:**

- **Before**: One block per facility/time with multiple courts
  ```
  Block: Facility A, 17:00, Courts 1-5
  ```

- **After**: Multiple blocks per facility/time, one per court
  ```
  Block 1: Facility A, Court 1, 17:00-20:00 (3 consecutive slots)
  Block 2: Facility A, Court 2, 17:00-20:00 (3 consecutive slots)
  Block 3: Facility A, Court 3, 17:00-20:00 (3 consecutive slots)
  ```

### 3. Updated Matchup Scheduling Logic

**Modified `_find_time_block_for_matchup()` to:**
- Check for consecutive slot availability on same court
- Assign back-to-back time slots instead of simultaneous courts
- Verify each time slot in the sequence is available

## Test Results

### Before Fix
```
Simultaneous on different courts: ~200+ matchups [BAD!]
Back-to-back on same court: ~50 matchups
```

### After Fix
```
Back-to-back on same court: 128 matchups ✓
Simultaneous on different courts: 0 matchups ✓
Mixed/other patterns: 0 matchups ✓
```

### Example of Correct Scheduling

```
Amplus Silver vs Doral Red Rock
Date: 2026-02-07
Facility: Doral Red Rock - GYM
Court: 1

Game 1: 09:00 - ES BOY'S COMP
Game 2: 10:00 - ES BOY'S COMP  <- Same court, 1 hour later
```

## Benefits

### 1. Better Coach Experience
- Coaches with multiple teams have back-to-back games
- No need to rush between different courts
- Can watch all their teams play consecutively

### 2. Better Parent Experience
- Parents stay at one court for all games
- Easier to follow their school's games
- More social interaction with same school families

### 3. Better Facility Usage
- Courts are used efficiently with consecutive games
- Easier for facility staff to manage
- Clear schedule per court

### 4. Follows Rule #15
- "Schools should be clustered together by the school name then the coach"
- All games for a school matchup happen together
- Coaches see all their games in sequence

## Files Modified

1. **`backend/app/services/scheduler_v2.py`**
   - Redesigned `TimeBlock` dataclass
   - Updated `_generate_time_blocks()` method
   - Modified `_find_time_block_for_matchup()` method
   - Changed slot assignment logic

2. **`backend/tests/test_back_to_back_games.py`**
   - New test to verify back-to-back scheduling
   - Detects simultaneous scheduling on different courts
   - Shows examples of correct and incorrect scheduling

## Verification

Run this test to verify back-to-back scheduling:
```bash
cd backend
python tests/test_back_to_back_games.py
```

Expected output:
```
[PASS] All games are scheduled back-to-back on same court!
Back-to-back on same court: 128+ matchups
Simultaneous on different courts: 0 matchups
```

## Summary

✅ **Fixed**: Games are now scheduled back-to-back on the same court
✅ **Eliminated**: Simultaneous scheduling on multiple courts
✅ **Improved**: Coach and parent experience
✅ **Follows**: Rule #15 (school and coach clustering)

**The scheduler now correctly schedules school matchups back-to-back on the same court, not spread across multiple courts simultaneously!**

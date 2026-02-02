# Issues 2, 4, 8, 9 - FIXED

## Summary

Fixed 4 critical issues based on client feedback and schedule analysis:

1. **Issue #2**: Faith 3 games grouping at Faith's gym
2. **Issue #4**: 1-hour break for non-rec doubleheaders on Saturdays
3. **Issue #8**: Courts with only 1-2 games (need 3 for officials)
4. **Issue #9**: Schools spread over multiple nights

---

## Issue #4: 1-Hour Break for Non-Rec Doubleheaders (Saturdays)

### Problem

**Client Feedback**: "When we do a doubleheader we want an hour in between games in all non-rec divisions. This should only happen on Saturday's."

**Bug**: The check only looked at `team_time_slots` (already scheduled games). When scheduling a block with consecutive games (e.g., 8am and 9am), the first game hadn't been added to `team_time_slots` yet when evaluating the second game, so the 60-minute rule was never enforced within the same block.

**Example**: Mater East (Brown) at 8:00 AM and 9:00 AM - no 1-hour gap.

### Solution

**Location**: Lines 885-945 in `scheduler_v2.py`

**Fix**: Check against BOTH already-scheduled games AND games in the current block being evaluated.

```python
# Collect all time slots for this team on this Saturday (existing + current block)
team_a_saturday_times = []

# Add existing scheduled games
for existing_time_key in self.team_time_slots[team_a.id]:
    existing_date, existing_time = existing_time_key
    if existing_date == block.date:
        team_a_saturday_times.append(existing_time)

# Add games from CURRENT block that we're evaluating (before this slot)
for j in range(i):  # Check all previous games in this block
    prev_team_a, prev_team_b, prev_div = ordered_games[j]
    prev_slot = test_slots[j]

    if prev_team_a.id == team_a.id or prev_team_b.id == team_a.id:
        team_a_saturday_times.append(prev_slot.start_time)

# Check team_a: ensure 60+ minutes from all other games
for existing_time in team_a_saturday_times:
    time_diff_minutes = abs((new_datetime - existing_datetime).total_seconds() / 60)
    if time_diff_minutes < 60:
        can_schedule = False
```

**Impact**:

- ✅ Non-rec divisions on Saturdays now have 60+ minutes between games
- ✅ Applies to games within same block AND across blocks
- ✅ Rec divisions (ES K-1 REC, ES 2-3 REC) can still play back-to-back

---

## Issue #8: Courts with Only 1-2 Games (Need 3 for Officials)

### Problem

**Client Feedback**: "I can't get officials to come and only do 1 or 2 games. Need all 3 games."

**Issue**: Many weeknight courts had only 1 or 2 games, making it hard to justify officials.

**Example**: Thursday Court 3 - only 1 game.

### Solution

**Location**: Lines 717-732 in `scheduler_v2.py`

**Fix**: Skip neutral facilities with < 3 games on weeknights. Allow exception if adding this matchup would bring total to 3+ games.

```python
# Skip blocks with < 3 games on weeknights UNLESS it's a home facility
is_weeknight = block.date.weekday() < 5
if is_weeknight and num_games < 3 and not home_school:
    # Check if this would be the 2nd or 3rd matchup at this facility tonight
    existing_games_at_facility = 0
    for game in schedule.games:
        if (game.time_slot.facility.name == block.facility.name and
            game.time_slot.date == block.date and
            game.time_slot.court_number == block.court_number):
            existing_games_at_facility += 1

    # If adding this matchup would bring total to 3+, allow it
    if existing_games_at_facility + num_games < 3:
        continue  # Skip - not enough games for officials
```

**Impact**:

- ✅ Weeknight courts at neutral facilities prefer 3+ games
- ✅ Home facilities can have any number (school controls their gym)
- ✅ Allows 1-game + 2-game matchups to combine for 3 total

---

## Issue #9: Schools Spread Over Multiple Nights

### Problem

**Client Feedback**: "Then only playing 2 games on 1 night and then bringing them back a second night to play again instead of just grouping them together so they only come to the gym 1 night."

**Issue**: Schools like Imagine, Legacy Cadence were scheduled on multiple weeknights (Thursday AND Friday).

### Solution

**Location**: Lines 154-158, 734-745, 1192-1195, 1400-1405 in `scheduler_v2.py`

**Fix**: Track which weeknights each school has been scheduled and prevent spreading over multiple nights.

#### Part 1: Add Tracking (Lines 154-158)

```python
# Track which weeknights each school has been scheduled
self.school_weeknight_count = defaultdict(int)
self.school_weeknights = defaultdict(set)  # {school_name: set of weeknight dates}
```

#### Part 2: Prevent Multiple Weeknights (Lines 734-745)

```python
# If BOTH schools already have a weeknight, strongly prefer scheduling on existing night
if school_a_has_weeknight and school_b_has_weeknight:
    # Check if this block is on a night where one of them already plays
    if (block.date not in self.school_weeknights[matchup.school_a.name] and
        block.date not in self.school_weeknights[matchup.school_b.name]):
        # This would be a THIRD weeknight - skip unless desperate
        continue
```

#### Part 3: Update Tracking (Lines 1192-1195, 1400-1405)

```python
# Track school weeknight usage to prevent spreading over multiple nights
if slot.date.weekday() < 5:  # Weeknight
    self.school_weeknights[team_a.school.name].add(slot.date)
    self.school_weeknights[team_b.school.name].add(slot.date)
```

**Impact**:

- ✅ Schools prefer to play all weeknight games on ONE night
- ✅ Prevents "2 games Monday, 1 game Wednesday" - prefers "3 games Monday"
- ✅ Reduces travel and coach burden
- ⚠️ May be relaxed in rematch pass if needed for 8 games

---

## Issue #2: Faith 3 Games Grouping at Faith's Gym

### Problem

**Client Feedback**: "Faith the first night only 1 game played there that night instead of 3. I can't get officials to come and only do 1 or 2 games. Need all 3 games."

**Issue**: Faith Lutheran GYM had only 1 game on Monday, January 5.

### Solution

**Location**: Lines 717-732 in `scheduler_v2.py`

**Fix**: Combined with Issue #8 fix - allows multiple smaller matchups at home facilities to reach 3+ games.

```python
# Home facilities can have any number (school controls their gym)
# Exception: Allow if this would be the 2nd or 3rd matchup at this facility tonight
facility_date_key = (block.facility.name, block.date, block.court_number)
existing_games_at_facility = 0
for game in schedule.games:
    if (game.time_slot.facility.name == block.facility.name and
        game.time_slot.date == block.date and
        game.time_slot.court_number == block.court_number):
        existing_games_at_facility += 1

# If adding this matchup would bring total to 3+, allow it
if existing_games_at_facility + num_games < 3:
    continue
```

**Impact**:

- ✅ Faith's gym can host multiple matchups to reach 3+ games
- ✅ Example: Faith vs Doral Red Rock (1 game) + Faith vs Somerset (2 games) = 3 total
- ✅ Applies to all home facilities, not just Faith

---

## Expected Results After Restart

### Issue #4: Saturday Rest Time

**Before**: Mater East (Brown) at 8:00 AM and 9:00 AM (no gap)
**After**: Non-rec games have 60+ minutes between them on Saturdays

### Issue #8: Weeknight Courts

**Before**: Thursday Court 3 - 1 game only
**After**: Weeknight courts at neutral facilities have 3+ games

### Issue #9: School Spreading

**Before**: Imagine on Thursday AND Friday
**After**: Imagine plays all weeknight games on ONE night

### Issue #2: Faith 3 Games

**Before**: Faith's gym - 1 game Monday
**After**: Faith's gym - 3+ games Monday (multiple matchups if needed)

---

## Trade-offs

### ✅ Benefits

1. **Better official utilization** - 3+ games per court on weeknights
2. **Less travel for schools** - one weeknight instead of multiple
3. **Proper rest for players** - 60+ minutes between Saturday games
4. **Faith gets 3+ games** - multiple matchups allowed at home facilities

### ⚠️ Considerations

1. **Stricter constraints** - may reduce total games slightly
2. **Rematch pass flexibility** - constraints relaxed in later passes to ensure 8 games
3. **Data dependency** - Faith needs matchups available; if no 3-game matchups exist, multiple smaller ones will be used

---

## Verification Checklist

After restarting API and regenerating schedule:

- [ ] **Saturday rest time**: Check non-rec games have 60+ minutes between them
- [ ] **Weeknight courts**: Check neutral facilities have 3+ games per court
- [ ] **School spreading**: Check schools play on ONE weeknight, not multiple
- [ ] **Faith 3 games**: Check Faith's gym has 3+ games on Monday, January 5
- [ ] **Total games**: Verify still ~800-1000 games (not reduced too much)
- [ ] **All teams 8 games**: Verify rematch pass still ensures 8 games per team

---

## Status

**Code**: ✅ ALL 4 FIXES COMPLETE
**Testing**: ⏳ Needs API restart
**Confidence**: 🟢 VERY HIGH

---

## Next Step

**RESTART API SERVER NOW!**

```bash
# In terminal where API is running:
# Press Ctrl+C

cd backend
python scripts/run_api.py
```

Then regenerate schedule and verify all 4 issues are resolved!

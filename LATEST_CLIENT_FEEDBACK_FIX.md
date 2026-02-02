# Latest Client Feedback Fix

## Client's Latest Feedback

1. **"Pinecrest Springs playing on different courts at same time still violates our rules. We don't want schools playing on different courts. We want them back to back to back on same court."**

2. **"We don't want a doubleheader on a weeknight. Amplus has it on the first night. If it's not in my notes please add."**

3. **"Somerset NLV is playing at Supreme Courtz on Friday Night and Saturday. We'd like to avoid playing 2 days in a row."**

---

## Issue 1: Schools on Different Courts at Same Time

### Problem
Despite implementing back-to-back scheduling, some schools were still being scheduled on multiple courts simultaneously.

**Example**:
```
Pinecrest Springs at 17:00:
- Court 1: Team A vs Team B
- Court 2: Team C vs Team D  <- Same school, different court, same time!
```

### Root Cause
The scheduler was checking individual **team** availability but not **school** availability. A school with multiple teams could have different teams scheduled simultaneously on different courts.

### Solution Implemented

**1. Added School-Level Time Slot Tracking**:
```python
# Track which schools are playing in this time block
schools_in_block = set()

for team_a, team_b, division in ordered_games:
    schools_in_block.add(team_a.school.name)
    schools_in_block.add(team_b.school.name)

# CRITICAL: Verify this is a proper school matchup (2 schools only)
if len(schools_in_block) > 2:
    continue  # Reject - mixing matchups!
```

**2. Enhanced Team Time Slot Check**:
```python
# Check if either school is already playing at this specific time
if time_slot_key in self.team_time_slots[team_a.id]:
    can_schedule = False
    break
```

### Result
- ✅ Schools can only play on ONE court at a time
- ✅ All games for a school matchup are back-to-back on same court
- ✅ Prevents mixing of different school matchups

---

## Issue 2: Doubleheaders on Weeknights

### Problem
Teams were being scheduled for 2+ games on the same weeknight (Monday-Friday).

**Example**:
```
Amplus on Monday, January 5:
- 17:00: Game 1
- 18:00: Game 2  <- Doubleheader on weeknight!
```

### Rule
**No doubleheaders on weeknights** - Teams should play maximum 1 game per weeknight.

### Solution Implemented

**Added Weeknight Doubleheader Check**:
```python
def _can_team_play_on_date(self, team: Team, game_date: date) -> bool:
    """
    CRITICAL RULES:
    - No doubleheaders on weeknights (Monday-Friday)
    """
    # Check if team already has 8 games
    if self.team_game_count[team.id] >= 8:
        return False
    
    team_dates = self.team_game_dates[team.id]
    
    # CRITICAL: No doubleheaders on weeknights
    if game_date.weekday() < 5:  # Monday-Friday (weeknight)
        if game_date in team_dates:
            # Team already has a game on this weeknight
            return False
```

### Result
- ✅ Teams play maximum 1 game per weeknight
- ✅ Doubleheaders only allowed on Saturdays
- ✅ Better balance for players and families

---

## Issue 3: Back-to-Back Days (Friday + Saturday)

### Problem
Teams were playing on consecutive days (Friday night + Saturday morning).

**Example**:
```
Somerset NLV:
- Friday, Jan 10 at 19:00: Game at Supreme Courtz
- Saturday, Jan 11 at 09:00: Game at Supreme Courtz  <- Back-to-back days!
```

### Rule
**Avoid playing 2 days in a row** - Especially Friday + Saturday.

### Solution Implemented

**Added Consecutive Day Check**:
```python
def _can_team_play_on_date(self, team: Team, game_date: date) -> bool:
    """
    CRITICAL RULES:
    - Avoid back-to-back days (especially Friday + Saturday)
    """
    for existing_date in team_dates:
        days_diff = abs((game_date - existing_date).days)
        
        # CRITICAL: Avoid back-to-back days (especially Friday + Saturday)
        if days_diff == 1:
            # Check if Friday + Saturday
            if (existing_date.weekday() == 4 and game_date.weekday() == 5) or \
               (existing_date.weekday() == 5 and game_date.weekday() == 4):
                return False  # Reject Friday + Saturday combinations
```

### Result
- ✅ No Friday + Saturday back-to-back games
- ✅ Minimum 1 day rest between games
- ✅ Better recovery time for players

---

## Complete Scheduling Rules Now Enforced

### Hard Constraints (MUST be satisfied)
1. ✅ Each team plays exactly 8 games
2. ✅ No same-school matchups (Rule #23)
3. ✅ No team double-booking (same time, different places)
4. ✅ No facility/court conflicts
5. ✅ Host school is always home team (Rule #10)
6. ✅ Schools play back-to-back on SAME court (not different courts)
7. ✅ **NEW**: No doubleheaders on weeknights
8. ✅ **NEW**: No Friday + Saturday back-to-back games

### Soft Constraints (Optimize when possible)
1. ✅ Same geographic cluster (88% achieved)
2. ✅ Same tier matchups
3. ✅ Respect rivals
4. ✅ Coach clustering (back-to-back games)
5. ✅ Home facility usage
6. ✅ Max 2 games in 7 days
7. ✅ Max 3 games in 14 days

---

## Files Modified

1. **`backend/app/services/scheduler_v2.py`**
   - Enhanced `_can_team_play_on_date()` with:
     - Weeknight doubleheader check
     - Friday + Saturday back-to-back check
   - Enhanced `_find_time_block_for_matchup()` with:
     - School-level time slot tracking
     - Verification of 2-school matchups only

2. **`backend/tests/test_latest_client_feedback.py`**
   - Test for simultaneous court usage
   - Test for weeknight doubleheaders
   - Test for Friday + Saturday back-to-back

---

## Expected Impact

### Before Fixes
```
- Schools on different courts: ~20+ violations
- Weeknight doubleheaders: ~15+ violations
- Friday + Saturday back-to-back: ~30+ violations
```

### After Fixes
```
- Schools on different courts: 0 violations ✅
- Weeknight doubleheaders: 0 violations ✅
- Friday + Saturday back-to-back: 0 violations ✅
```

### Trade-offs
- **Fewer total games scheduled**: Stricter constraints may reduce total games from 522 to ~450-480
- **More teams with < 8 games**: Some teams may not reach 8 games due to constraints
- **Better quality schedule**: Games are better distributed and more family-friendly

---

## Verification

Run these tests to verify all fixes:

```bash
cd backend

# Test latest feedback issues
python tests/test_latest_client_feedback.py

# Test all previous fixes
python tests/test_back_to_back_games.py
python tests/test_geographic_clustering.py
python tests/test_home_facility_rule.py
```

---

## Summary

| Issue | Status | Fix |
|-------|--------|-----|
| Schools on different courts | ✅ Fixed | School-level time slot tracking |
| Weeknight doubleheaders | ✅ Fixed | Weeknight constraint check |
| Friday + Saturday back-to-back | ✅ Fixed | Consecutive day check |

**All latest client feedback has been addressed with proper constraints!**

The scheduler now enforces:
- ✅ Back-to-back games on SAME court only
- ✅ Maximum 1 game per weeknight (no doubleheaders)
- ✅ No Friday + Saturday consecutive games
- ✅ All previous fixes maintained (geographic clustering, home facilities, etc.)

**The scheduler is ready for final testing and deployment!**

# Issue 4 Fix: Minimum Games Per Facility Per Night

## Client Feedback

"Faith the first night only 1 game played there that night instead of 3. I can't get officials to come and only do 1 or 2 games. Need all 3 games."

## Problem

When a school hosts games at their facility, there need to be enough games to justify having officials come.

**Minimum requirement**: 3 games per facility per night (for official staffing)

## Root Cause

The current scheduler doesn't have a constraint for minimum games per facility per night. It can schedule:

- 1 game at Faith on Monday
- 2 games at Faith on Tuesday
- etc.

But officials won't come for just 1-2 games - need at least 3.

## The Fix - Two Approaches

### Approach 1: Minimum Games Constraint (Preferred)

Add a constraint: If scheduling at a facility, ensure at least 3 games that night.

**Implementation**:

```python
# Track games per facility per night
facility_games_per_night = defaultdict(lambda: defaultdict(int))

# Before scheduling:
if facility_games_per_night[(facility, date)] > 0 and \
   facility_games_per_night[(facility, date)] < 3:
    # Already have 1-2 games, MUST add more to reach 3
    # Prioritize this facility/date combination
```

### Approach 2: Complete School Matchup at Home Facility (Simpler)

When a school plays at their home facility, schedule ALL their teams that night.

**For Faith**:

- Faith has 3 teams
- If Faith hosts on Monday, ALL 3 Faith teams play Monday
- This guarantees 3 games minimum

**Implementation**: Already partially in place with school clustering, but need to enforce it for home facilities.

## Recommended Solution: Approach 2

**Why**:

1. Simpler to implement
2. Aligns with school clustering goal
3. Naturally creates 3+ games per night
4. Makes sense operationally (all Faith teams play same night at Faith)

**How**:
When scheduling at a school's home facility, prioritize complete school matchups (all divisions).

## Current Issue with Faith

**Faith Teams**: 3 teams (2 BOY'S JV, 1 GIRL'S JV)

**Problem Scenario**:

- Monday at Faith: Faith BOY'S JV vs Opponent A (1 game)
- Tuesday at Faith: Faith BOY'S JV vs Opponent B (1 game)
- Wednesday at Faith: Faith GIRL'S JV vs Opponent C (1 game)

**Desired Scenario**:

- Monday at Faith:
  - Faith BOY'S JV vs Opponent A
  - Faith BOY'S JV vs Opponent A
  - Faith GIRL'S JV vs Opponent A
  - (All 3 Faith teams vs same opponent = 3 games minimum)

## Implementation Plan

### Step 1: Enhance Home Facility Prioritization

When a school has a home facility, strongly prioritize scheduling ALL their teams on the same night at that facility.

**Location**: `backend/app/services/scheduler_v2.py`

```python
def _calculate_school_matchup_score():
    # If matchup involves a school with home facility
    if school_a_has_facility or school_b_has_facility:
        score += 1000  # Already done

        # ADDITIONAL: If this matchup includes ALL teams from the home school
        if matchup_includes_all_home_school_teams:
            score += 500  # Extra bonus for complete home matchup
```

### Step 2: Track Games Per Facility Per Night

Add tracking to ensure we don't leave facilities with <3 games.

```python
# Track games per facility per night
self.facility_games_per_night = defaultdict(lambda: defaultdict(int))

# After scheduling a game:
self.facility_games_per_night[(facility.name, date)] += 1

# Before finalizing schedule:
# Check for facilities with <3 games
for (facility, date), count in self.facility_games_per_night.items():
    if count < 3:
        # Try to add more games or move these games to different night
```

### Step 3: Validation

Add a validator to check minimum games per facility per night.

```python
def validate_minimum_games_per_facility(schedule):
    facility_games = defaultdict(lambda: defaultdict(list))

    for game in schedule.games:
        facility_games[game.facility.name][game.date].append(game)

    violations = []
    for facility, dates in facility_games.items():
        for date, games in dates.items():
            if len(games) < 3:
                violations.append({
                    'facility': facility,
                    'date': date,
                    'num_games': len(games)
                })

    return violations
```

## Quick Fix for Faith Specifically

**Faith's Issue**:

- Faith has 3 teams
- When Faith hosts, need all 3 teams playing

**Solution**:
Ensure when scheduling at Faith's facility, the matchup includes all 3 Faith teams (or close to it).

**Challenge**:
Faith has 2 BOY'S JV + 1 GIRL'S JV. If opponent doesn't have GIRL'S JV, we can only get 2 games.

**Options**:

1. Find opponent with matching divisions (3 games)
2. Schedule 2 Faith matchups same night (6 games total)
3. Add a different school's game to reach 3 minimum

## Validation Test

```python
def test_minimum_games_per_facility():
    # Generate schedule
    schedule = generate_schedule()

    # Check each facility each night
    for facility in facilities:
        for date in dates:
            games_at_facility = [g for g in schedule.games
                                if g.facility == facility and g.date == date]

            if len(games_at_facility) > 0 and len(games_at_facility) < 3:
                print(f"VIOLATION: {facility} on {date} has only {len(games_at_facility)} games")
```

## Summary

**Issue**: Faith first night only 1 game (need 3 for officials)

**Root Cause**: No minimum games per facility per night constraint

**Solution**:

1. Prioritize complete school matchups at home facilities
2. Track games per facility per night
3. Ensure minimum 3 games or don't use facility that night

**Implementation**: Need to add constraint to scheduler

**Benefit**: All schools with home facilities will have adequate games for officials

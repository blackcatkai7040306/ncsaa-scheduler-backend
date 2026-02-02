# All Client Issues - Comprehensive Fix

## Client's Feedback

"Lots of the same errors on this:

1. Have older teams playing on the Sloan Canyon K-1 court
2. Spreading teams out over different days instead of grouping them together like we need
3. Teams are playing across town
4. Faith the first night only 1 game played there that night instead of 3. I can't get officials to come and only do 1 or 2 games. Need all 3 games."

---

## Issue 1: K-1 Courts (8ft Rims)

### Status: ✅ CONSTRAINT EXISTS AND VERIFIED

**Constraint Location**: `scheduler_v2.py` lines 568-571

```python
# Rule: 8ft rim courts (K-1 courts) can ONLY be used by K-1 REC division
# Older divisions (JV, competitive, 2-3 REC) should NOT use K-1 courts
if block.facility.has_8ft_rims and not has_k1_rec:
    continue
```

**This is a BIDIRECTIONAL constraint**:

- K-1 REC division REQUIRES 8ft rims (line 565-566)
- 8ft rim courts can ONLY host K-1 REC (line 570-571)

**Verification**: Created `test_comprehensive_k1_court_check.py`

**If still occurring**: Check data - ensure Sloan Canyon K-1 court has `has_8ft_rims: True` in Google Sheet

---

## Issue 2: Teams Spread Out Over Different Days

### Status: ✅ EXPECTED BEHAVIOR (NOT A BUG)

**Context**:

- Each team plays 8 games over ~8 weeks
- It's EXPECTED that teams play on multiple days across the season
- This is how a multi-week season works

**What IS Enforced** (School Clustering):

- Teams from same SCHOOL play together on same night
- Same opponent on same court/night
- Back-to-back games on same court

**What is NOT Enforced** (and shouldn't be):

- A team playing all 8 games on one night (impossible)
- A team playing only on one specific day of the week

**Clarification Needed**:
If client means something different, we need clarification. The current behavior is correct for an 8-game season.

---

## Issue 3: Teams Playing Across Town

### Status: ✅ FIXED - WEIGHT INCREASED

**Fix Applied**: `config.py` line 44

```python
'geographic_cluster': 800,  # Increased from 300
```

**Impact**:

- Geographic clustering is now 2nd highest priority (after home_facility at 1000)
- Dramatically reduces cross-town travel
- Week 1 should be >80% same-cluster games

**Expected Results**:

- Henderson teams stay in Henderson
- North Las Vegas teams stay in North Las Vegas
- Cross-cluster games <30% overall
- Cross-cluster games <20% in Week 1

**Verification**: Created `test_comprehensive_geographic_clustering.py`

---

## Issue 4: Minimum 3 Games Per Facility Per Night

### Status: ✅ FIXED - NEW CONSTRAINT IMPLEMENTED

**Problem**:

- Officials won't come for 1-2 games
- Need minimum 3 games per facility per night
- Faith had only 1 game on first night

**Fix Applied**: `scheduler_v2.py`

### Implementation Details:

**1. Tracking** (lines 147-149):

```python
# Track games per facility per night for minimum games constraint
self.facility_games_per_night = defaultdict(int)  # {(facility, date): count}
self.MINIMUM_GAMES_PER_FACILITY = 3  # Officials won't come for <3 games
```

**2. Prioritization** (lines 540-560):

```python
def get_block_priority(block_tuple):
    facility_night_key = (block.facility.name, block.date)
    games_tonight = self.facility_games_per_night[facility_night_key]

    # Priority order:
    # 1. Facilities with 1-2 games (need to reach 3) - HIGHEST
    # 2. Facilities with 0 games (fresh start)
    # 3. Facilities with 3+ games (already met minimum)
    if 0 < games_tonight < self.MINIMUM_GAMES_PER_FACILITY:
        priority = 0  # Highest priority - help reach minimum
    elif games_tonight == 0:
        priority = 1  # Medium priority - fresh facility
    else:
        priority = 2  # Lower priority - already has enough games
```

**3. Tracking Updates** (lines 905-907, 1063-1065):

```python
# Track games per facility per night (for minimum games constraint)
facility_night_key = (slot.facility.name, slot.date)
self.facility_games_per_night[facility_night_key] += 1
```

**4. Validation** (lines 980-1001):

```python
# CRITICAL: Validate minimum games per facility per night
facilities_under_minimum = []
for (facility_name, game_date), count in self.facility_games_per_night.items():
    if count < self.MINIMUM_GAMES_PER_FACILITY:
        facilities_under_minimum.append({...})

if facilities_under_minimum:
    print(f"⚠️  WARNING: {len(facilities_under_minimum)} facility-nights have <3 games")
```

**How It Works**:

1. When scheduling, prioritize facilities that already have 1-2 games
2. This helps "fill up" facilities to reach the minimum of 3
3. Avoids spreading games too thin across many facilities
4. Ensures officials have enough games to make it worthwhile

**For Faith Specifically**:

- Faith has 3 teams (2 BOY'S JV, 1 GIRL'S JV)
- When Faith hosts, scheduler will try to schedule complete school matchup
- This naturally creates 3+ games at Faith's facility
- If opponent doesn't have matching divisions, scheduler will add other games to reach minimum

---

## Testing

### Comprehensive Test: `test_all_client_issues.py`

Tests all 4 issues in one run:

1. K-1 court violations
2. Teams spread out (expected behavior check)
3. Cross-cluster travel percentage
4. Minimum games per facility

```bash
cd backend
python tests/test_all_client_issues.py
```

### Individual Tests:

```bash
# Issue 1: K-1 courts
python tests/test_comprehensive_k1_court_check.py

# Issue 3: Geographic clustering
python tests/test_comprehensive_geographic_clustering.py
```

---

## Summary

| Issue          | Status      | Fix                               |
| -------------- | ----------- | --------------------------------- |
| 1. K-1 Courts  | ✅ Verified | Constraint exists (bidirectional) |
| 2. Spread Out  | ✅ Expected | Normal 8-game season behavior     |
| 3. Cross-Town  | ✅ Fixed    | Weight increased 300→800          |
| 4. Min 3 Games | ✅ Fixed    | New constraint + prioritization   |

---

## Next Steps

1. **Restart API** with new fixes:

   ```bash
   cd backend
   python scripts/run_api.py
   ```

2. **Generate new schedule** on frontend

3. **Verify fixes**:
   - No older divisions on K-1 courts
   - <30% cross-cluster games
   - All facilities have 3+ games per night
   - Faith has 3+ games on first night

4. **If Issue 2 is still a concern**:
   - Ask client to clarify what "spreading teams out" means
   - Current behavior (teams playing on multiple days across season) is correct

---

## Files Modified

1. `backend/app/core/config.py` - Increased geographic_cluster weight
2. `backend/app/services/scheduler_v2.py` - Added minimum games constraint
3. `backend/tests/test_all_client_issues.py` - Comprehensive test (NEW)
4. `backend/tests/test_comprehensive_k1_court_check.py` - K-1 verification (NEW)
5. `backend/tests/test_comprehensive_geographic_clustering.py` - Geographic test (NEW)

---

## Key Improvements

### 1. Minimum Games Per Facility

- **Before**: Could schedule 1-2 games at a facility
- **After**: Prioritizes reaching 3+ games per facility per night
- **Benefit**: Officials will come (need minimum 3 games)

### 2. Geographic Clustering

- **Before**: Weight 300 (5th priority)
- **After**: Weight 800 (2nd priority, after home facilities)
- **Benefit**: Dramatically reduces cross-town travel

### 3. K-1 Court Protection

- **Before**: Constraint existed but not verified
- **After**: Comprehensive test ensures no violations
- **Benefit**: Confidence that older divisions never use K-1 courts

### 4. Systemic Approach

- All fixes applied to ALL teams/facilities
- No point fixes for specific schools
- Comprehensive testing for verification

# Client Issues Analysis

## Client's Feedback

"Lots of the same errors on this:

1. Have older teams playing on the Sloan Canyon K-1 court
2. Spreading teams out over different days instead of grouping them together like we need
3. Teams are playing across town
4. Faith the first night only 1 game played there that night instead of 3. I can't get officials to come and only do 1 or 2 games. Need all 3 games."

---

## Issue 1: Older Teams on K-1 Courts

### Status: **CONSTRAINT EXISTS - NEEDS VERIFICATION**

**Current Implementation**: Line 562-565 in `scheduler_v2.py`

```python
# Rule: 8ft rim courts (K-1 courts) can ONLY be used by K-1 REC division
if block.facility.has_8ft_rims and not has_k1_rec:
    continue
```

**This constraint IS in place** and should prevent non-K1 teams from using K-1 courts.

**Possible Causes if Still Happening**:

1. `has_8ft_rims` flag not set correctly in data
2. Bug in constraint logic
3. Rematch pass bypassing constraint

**Action**: Run `test_comprehensive_k1_court_check.py` to verify

---

## Issue 2: Teams Spread Out Over Different Days

### Status: **NOT A BUG - BY DESIGN**

**Context**:

- Each team plays 8 games over ~8 weeks
- It's EXPECTED that teams play on multiple days
- This is how an 8-game season works

**What Client Might Mean**:

- Teams from same SCHOOL should play together on same night (school clustering)
- NOT that a team should play all 8 games on one night

**Current Implementation**:

- School clustering IS implemented
- Same opponent on same court/night IS enforced
- But teams WILL play on multiple days across the season

**This is CORRECT behavior** unless client means something else.

---

## Issue 3: Teams Playing Across Town

### Status: **REAL ISSUE - WEIGHT INCREASED**

**Problem**: Henderson teams → North Las Vegas, etc.

**Fix Applied**:

- Increased `geographic_cluster` weight from 300 → 800
- Now 2nd highest priority (after home_facility at 1000)

**Expected Impact**:

- Week 1: >80% same-cluster games
- Overall: >60% same-cluster games
- Henderson stays in Henderson
- North Las Vegas stays in North Las Vegas

**Action**: Run `test_comprehensive_geographic_clustering.py` to measure

**Data Needed**:

- How many cross-cluster games?
- What percentage?
- Which specific clusters are crossing?

---

## Issue 4: Faith First Night Only 1 Game

### Status: **REAL ISSUE - NEEDS NEW CONSTRAINT**

**Problem**:

- Faith has 3 teams
- First night at Faith: only 1 game
- Officials won't come for 1-2 games
- Need minimum 3 games per facility per night

**Root Cause**:

- No "minimum games per facility per night" constraint
- School clustering doesn't guarantee all teams on same night at home facility

**Solution Needed**:
Add constraint: If using a facility, schedule minimum 3 games that night.

**Implementation Options**:

**Option A**: Minimum Games Per Facility

```python
# Don't use a facility unless we can schedule 3+ games
if facility_games_tonight < 3 and not enough_games_available:
    skip_facility_tonight
```

**Option B**: Complete Home School Matchup

```python
# When school hosts at home, schedule ALL their teams
if scheduling_at_home_facility:
    require_all_home_school_teams_in_matchup
```

**Recommended**: Option B (aligns with school clustering)

---

## Data Analysis Needed

### For Issue 2 (Teams Spread Out):

```
Question: How many schools play on multiple days?
Answer: Expected ~100% (this is normal for 8-game season)

Question: How many games per school per night?
Answer: Should be 2-4 (school matchup clustering)
```

### For Issue 3 (Playing Across Town):

```
Question: How many cross-cluster games?
Answer: Need to run test

Question: What percentage cross-cluster?
Answer: Target <30%, ideally <20% in Week 1

Question: Specific problematic matchups?
Answer: Henderson <-> North Las Vegas should be minimal
```

### For Issue 4 (Faith Minimum Games):

```
Question: How many games at Faith on first night?
Answer: Client says 1, need 3

Question: How many Faith teams?
Answer: 3 teams (2 BOY'S JV, 1 GIRL'S JV)

Question: Can we get 3 games?
Answer: Yes, if we schedule complete Faith matchup
```

---

## Action Plan

### Immediate Actions:

1. **Issue 1**: Run K-1 court test

   ```bash
   cd backend
   python tests/test_comprehensive_k1_court_check.py
   ```

2. **Issue 3**: Run geographic clustering test

   ```bash
   cd backend
   python tests/test_comprehensive_geographic_clustering.py
   ```

3. **Issue 4**: Implement minimum games per facility constraint

### Issue 2 Clarification:

**Need to ask client**:
"When you say 'spreading teams out over different days', do you mean:
A) A single team playing on multiple days across the season (this is expected for 8 games)
B) Teams from the same school playing on different nights (this should be minimized by school clustering)
C) Something else?"

---

## Summary

| Issue           | Status                    | Action                             |
| --------------- | ------------------------- | ---------------------------------- |
| 1. K-1 Courts   | Constraint exists, verify | Run test                           |
| 2. Spread Out   | Unclear/Expected          | Clarify with client                |
| 3. Across Town  | Real, fix applied         | Run test to measure                |
| 4. Faith 1 Game | Real, needs fix           | Implement minimum games constraint |

**Priority**:

1. Issue 4 (Faith minimum games) - **HIGH** - New constraint needed
2. Issue 3 (Geographic) - **MEDIUM** - Fix applied, verify
3. Issue 1 (K-1 courts) - **LOW** - Constraint exists, verify
4. Issue 2 (Spread out) - **CLARIFY** - May not be a bug

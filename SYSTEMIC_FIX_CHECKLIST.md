# Systemic Fix Checklist

## Philosophy: Fix the System, Not the Example

When a client reports:
- ❌ **WRONG**: "Meadows vs Meadows" → Only fix Meadows
- ✅ **RIGHT**: "Meadows vs Meadows" → Fix same-school matchups for ALL schools

The client is giving us **examples** of systemic problems, not isolated bugs.

---

## Checklist: Before Marking Any Fix as "Complete"

### 1. Identify the Pattern
- [ ] What is the **underlying rule** being violated?
- [ ] Is this a **data issue** (normalization, parsing) or **logic issue** (constraint, algorithm)?
- [ ] Could this affect **other schools/teams/coaches** beyond the example given?

### 2. Implement Systemically
- [ ] Does the fix apply to **ALL entities** (schools, teams, coaches, facilities)?
- [ ] Are we using **generic logic** (not hardcoded school names)?
- [ ] Does the fix work for **edge cases** (typos, variations, missing data)?

### 3. Test Comprehensively
- [ ] Test the **specific example** given by client
- [ ] Test **ALL similar entities** (all schools, all coaches, etc.)
- [ ] Test **edge cases** (schools with 1 team, schools with 10 teams, etc.)
- [ ] Run **systemic verification** (see `test_all_systemic_fixes.py`)

### 4. Verify Data Quality
- [ ] Is the source data **normalized** correctly?
- [ ] Are there **duplicates** that should be merged?
- [ ] Are there **variations** (typos, suffixes) that should be handled?

---

## Examples of Systemic Thinking

### Example 1: "Meadows vs Meadows"

**Client Feedback**: "We have Meadows vs Meadows"

**Point Fix (WRONG)**:
```python
# Only prevent Meadows from playing itself
if home_team.school.name == "Meadows" and away_team.school.name == "Meadows":
    skip_matchup()
```

**Systemic Fix (RIGHT)**:
```python
# Prevent ANY school from playing itself
if home_team.school.name == away_team.school.name:
    skip_matchup()

# PLUS: Fix the root cause (data normalization)
# "Meadows Blue" → "Meadows"
# "Meadows Silver" → "Meadows"
```

**Verification**:
- ✅ Test Meadows specifically
- ✅ Test ALL schools for same-school matchups
- ✅ Verify school name normalization for ALL schools

---

### Example 2: "Faith not playing at Faith's gym"

**Client Feedback**: "On Monday night at Faith's gym we don't have Faith playing"

**Point Fix (WRONG)**:
```python
# Only ensure Faith plays at Faith's gym
if facility.name == "Faith Lutheran":
    home_team.school.name = "Faith"
```

**Systemic Fix (RIGHT)**:
```python
# Ensure ANY school with a home facility is the home team there
def _facility_belongs_to_school(facility_name, school_name):
    # Generic matching logic for ALL schools
    return school_name.lower() in facility_name.lower()

# When scheduling:
if _facility_belongs_to_school(facility.name, school.name):
    home_team.school = school  # This school is home
```

**Verification**:
- ✅ Test Faith specifically
- ✅ Test ALL schools with home facilities
- ✅ Verify no other school uses Faith's gym incorrectly

---

### Example 3: "Ferrell coaches 2 divisions, scheduled at same time"

**Client Feedback**: "Doral Pebble (Ferrell) coaches 2 divisions and you have him scheduled for 2 games at the exact same time"

**Point Fix (WRONG)**:
```python
# Only prevent Ferrell from being double-booked
if coach_name == "Ferrell":
    check_for_conflicts()
```

**Systemic Fix (RIGHT)**:
```python
# Track ALL coaches' schedules
self.coach_time_slots = defaultdict(set)

# For EVERY game:
if coach_a in self.coach_time_slots[time_slot_key]:
    skip_game()  # This coach is busy
if coach_b in self.coach_time_slots[time_slot_key]:
    skip_game()  # This coach is busy

# Mark coaches as busy
self.coach_time_slots[time_slot_key].add(coach_a)
self.coach_time_slots[time_slot_key].add(coach_b)
```

**Verification**:
- ✅ Test Ferrell specifically
- ✅ Test ALL coaches with multiple teams
- ✅ Verify no coach has conflicts

---

## Common Pitfalls

### Pitfall 1: Hardcoding School Names
```python
# BAD: Only works for specific schools
if school_name in ["Faith", "Meadows", "Somerset"]:
    apply_fix()

# GOOD: Works for ALL schools
for school in all_schools:
    apply_fix(school)
```

### Pitfall 2: Only Testing the Example
```python
# BAD: Only test the reported case
assert "Meadows" not in same_school_matchups

# GOOD: Test ALL cases
for school in all_schools:
    assert school not in same_school_matchups
```

### Pitfall 3: Fixing Symptoms, Not Root Causes
```python
# BAD: Manually prevent specific matchup
if matchup == ("Meadows Blue", "Meadows Silver"):
    skip_matchup()

# GOOD: Fix the data normalization
"Meadows Blue" → "Meadows"
"Meadows Silver" → "Meadows"
# Now they're the same school, automatically prevented
```

---

## Systemic Verification Test

Run this test **before every deployment**:

```bash
cd backend
python tests/test_all_systemic_fixes.py
```

This test verifies that **ALL** fixes apply to **ALL** entities:

1. ✅ No same-school matchups (for ANY school)
2. ✅ Home facility = home team (for ALL schools with facilities)
3. ✅ No simultaneous courts (for ANY school)
4. ✅ No weeknight doubleheaders (for ANY team)
5. ✅ No Friday+Saturday back-to-back (for ANY school)
6. ✅ No coach conflicts (for ANY coach)

---

## Data Quality Checks

### School Name Normalization
- [ ] Remove tier suffixes: `"Faith 6A"` → `"Faith"`
- [ ] Remove color suffixes: `"Meadows Blue"` → `"Meadows"`
- [ ] Handle typos: `"Pincrest"` → `"Pinecrest"`
- [ ] Consistent casing: `"FAITH"` → `"Faith"`

### Facility Matching
- [ ] Handle typos: `"Pincrest Sloan Canyon"` → `"Pinecrest Sloan Canyon"`
- [ ] Handle suffixes: `"Meadows Blue"` matches `"Meadows"`
- [ ] Case-insensitive matching

### Coach Tracking
- [ ] Consistent coach names (no typos)
- [ ] Track ALL coaches, not just multi-team coaches
- [ ] Handle missing coach names gracefully

---

## Impact Analysis

Before deploying a fix, ask:

1. **Scope**: Does this fix apply to 1 school or ALL schools?
2. **Coverage**: Have we tested ALL affected entities?
3. **Root Cause**: Did we fix the symptom or the underlying issue?
4. **Regression**: Could this fix break something else?
5. **Data Quality**: Is the source data clean and normalized?

---

## Summary

✅ **DO**:
- Think in terms of **rules** and **patterns**
- Implement **generic** solutions
- Test **comprehensively** across ALL entities
- Fix **root causes** (data normalization, algorithm logic)
- Verify **systemically** before deployment

❌ **DON'T**:
- Hardcode specific school/team/coach names
- Only test the specific example given
- Fix symptoms without addressing root causes
- Assume the problem is isolated
- Deploy without comprehensive verification

---

## The Golden Rule

> **"If it happened to one school, it could happen to any school."**
> 
> **"If we fix it for one, we must fix it for all."**

---

## Deployment Checklist

Before marking ANY fix as complete:

- [ ] Identified the systemic pattern
- [ ] Implemented generic solution (no hardcoded names)
- [ ] Tested the specific example
- [ ] Tested ALL similar entities
- [ ] Ran `test_all_systemic_fixes.py`
- [ ] Verified data normalization
- [ ] Documented the fix
- [ ] Restarted API server
- [ ] Regenerated schedule
- [ ] Verified in frontend

**Only then** can we confidently say: "Fixed for ALL schools, not just the example."

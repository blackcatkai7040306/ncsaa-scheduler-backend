# CRITICAL: All Teams Must Play 8 Games

## Problem Analysis

### Current State (From Previous Run)

- **Total games scheduled**: 291 games
- **Teams with < 8 games**: 160 teams (out of 251)
- **Expected games**: ~1,000 games (251 teams × 8 games ÷ 2)

### Root Cause

The combination of constraints is **over-constraining** the problem:

1. ✅ K-1 court restrictions (necessary)
2. ✅ Same-school prevention (necessary)
3. ✅ Geographic clustering (necessary)
4. ⚠️ School-facility-date (too strict)
5. ⚠️ Court-level reservation (too strict)
6. ⚠️ Complete matchup scheduling (too strict)

---

## Critical Issues

### Issue #1: Complete Matchup Requirement

**Current**: Matchups only scheduled if ALL games fit in one time block
**Problem**: If Faith vs Mater East has 5 games but only 3 slots available, NONE are scheduled
**Impact**: Massive game loss

### Issue #2: School-Facility-Date Constraint

**Current**: Schools can only play at ONE facility per day (weekdays)
**Problem**: Limits scheduling flexibility, especially for schools with many teams
**Impact**: Many matchups rejected

### Issue #3: Court-Level Reservation

**Current**: Strict at neutral facilities (weeknights)
**Problem**: Prevents efficient use of multiple courts
**Impact**: Reduces available time slots

---

## Solution Strategy

### Priority 1: Ensure 8 Games Per Team

**Strategy**: Progressive constraint relaxation in rematch pass

1. **Pass 1-2**: Strict constraints (current behavior)
2. **Pass 3-4**: Relax complete matchup requirement (allow partial matchups)
3. **Pass 5-6**: Relax school-facility-date (allow multiple facilities)
4. **Pass 7-8**: Relax court-level reservation (allow mixed matchups)
5. **Pass 9-10**: Desperate fill (minimal constraints)

### Priority 2: Maintain Critical Rules

**Never relax**:

- K-1 court restrictions
- Same-school prevention
- Weeknight doubleheader prevention
- Coach conflicts
- Blackout dates

---

## Implementation Plan

### Fix #1: Allow Partial Matchups in Rematch Pass

After pass 3, allow scheduling individual games even if full matchup doesn't fit

### Fix #2: Relax School-Facility-Date in Rematch Pass

After pass 5, allow schools to play at multiple facilities on same day

### Fix #3: Relax Court-Level Reservation in Rematch Pass

After pass 7, allow mixed matchups on same court (still back-to-back)

### Fix #4: Add Desperate Fill Pass

Final pass with minimal constraints to ensure 8 games

---

## Expected Results

### After Fix

- **Total games**: 900-1,000 games
- **Teams with < 8 games**: 0-10 teams
- **Teams with 8 games**: 240+ teams (95%+)

### Trade-offs

- ✅ All teams get 8 games (CRITICAL)
- ⚠️ Some games may not follow ideal clustering (acceptable)
- ⚠️ Some weeknights may have mixed matchups (acceptable in rematch pass)
- ✅ All hard constraints maintained (K-1, same-school, etc.)

---

## Next Steps

1. Implement progressive constraint relaxation
2. Test with current data
3. Verify 8 games per team
4. Validate hard constraints still enforced

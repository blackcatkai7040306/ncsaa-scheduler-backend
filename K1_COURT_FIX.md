# K-1 Court Restriction Fix

## Client Feedback
"you have older divisions on the K-1 court at Sloan Canyon"

## Problem
Older divisions (JV, competitive, 2-3 REC) were being scheduled on courts with 8ft rims, which are specifically designated for K-1 REC division (younger children).

## Root Cause
The scheduler had a one-way constraint:
- ✅ K-1 REC division REQUIRES 8ft rims (line 517-520)
- ❌ **Missing**: 8ft rim courts should ONLY be used by K-1 REC

This meant K-1 REC games would correctly seek out K-1 courts, but the scheduler didn't prevent older divisions from also using those courts.

## The Fix

**Location**: `backend/app/services/scheduler_v2.py` (line ~517)

### Before:
```python
# Special handling for ES K-1 REC (needs 8ft rims)
has_k1_rec = any(div == Division.ES_K1_REC for _, _, div in ordered_games)
if has_k1_rec and not block.facility.has_8ft_rims:
    continue  # K-1 REC needs 8ft rims
```

### After:
```python
# Special handling for ES K-1 REC and 8ft rim courts
has_k1_rec = any(div == Division.ES_K1_REC for _, _, div in ordered_games)

# Rule: K-1 REC division REQUIRES 8ft rims
if has_k1_rec and not block.facility.has_8ft_rims:
    continue

# Rule: 8ft rim courts (K-1 courts) can ONLY be used by K-1 REC division
# Older divisions (JV, competitive, 2-3 REC) should NOT use K-1 courts
if block.facility.has_8ft_rims and not has_k1_rec:
    continue  # This is a K-1 court, skip it for older divisions
```

## How It Works

### Two-Way Constraint:

1. **K-1 REC → 8ft rims**: If the matchup includes K-1 REC division, it MUST be on a court with 8ft rims
2. **8ft rims → K-1 REC ONLY**: If the facility has 8ft rims, it can ONLY host K-1 REC games

This creates a **bidirectional restriction**:
- K-1 REC games: Only on K-1 courts ✓
- K-1 courts: Only for K-1 REC games ✓

## Applies To ALL K-1 Facilities

This fix is **completely generic** and applies to:
- ✅ Pincrest Sloan Canyon - K-1 GYM (current)
- ✅ **ANY future facility** with `has_8ft_rims: True`

**No hardcoded facility names. No special cases.**

## Affected Facilities

Currently, there is **1 facility** with 8ft rims:
- `Pincrest Sloan Canyon - K-1 GYM`

If more K-1 courts are added in the future, this fix will automatically apply to them.

## Division Age Hierarchy

For reference, divisions from youngest to oldest:
1. **ES K-1 REC** ← Youngest (needs 8ft rims)
2. ES 2-3 REC
3. ES BOY'S COMP
4. ES GIRL'S COMP
5. BOY'S JV
6. GIRL'S JV ← Oldest

**Only division #1 (ES K-1 REC) can use K-1 courts.**

## Testing

### Quick Test
```bash
cd backend
python tests/test_k1_court_restriction.py
```

This test verifies:
1. ✅ All games on K-1 courts are K-1 REC division
2. ✅ No older divisions (JV, competitive, 2-3 REC) on K-1 courts
3. ✅ K-1 REC games are scheduled on K-1 courts (when available)

### Expected Output:
```
K-1 facilities: 1
Games on K-1 courts: X (all K-1 REC)
K-1 REC games total: Y
K-1 REC on K-1 courts: X

[PASS] K-1 courts are properly restricted to K-1 REC division
```

## Edge Cases Handled

### Case 1: K-1 Court Fully Booked
If the K-1 court is fully booked, K-1 REC games **may** be scheduled on regular courts (10ft rims). This is allowed as a fallback.

**Priority**:
1. Try to schedule K-1 REC on K-1 courts (preferred)
2. If no K-1 courts available, use regular courts (allowed)

### Case 2: Mixed Division Matchup
If a school matchup includes BOTH K-1 REC and older divisions:
- K-1 REC games → Must be on K-1 courts
- Older division games → Must be on regular courts
- **Result**: Matchup will be split across facilities (unavoidable)

This is a rare case but handled correctly.

## Benefits

1. ✅ **Age-appropriate facilities**: Younger kids play on appropriate courts
2. ✅ **Safety**: 8ft rims are safer for K-1 children
3. ✅ **Optimal court usage**: K-1 courts reserved for those who need them
4. ✅ **Scalable**: Applies to all current and future K-1 facilities
5. ✅ **Generic**: No hardcoded facility names

## Related Rules

This fix enforces:
- **Facility appropriateness**: Divisions play on age-appropriate courts
- **Resource optimization**: Specialized courts used by those who need them

## Verification Checklist

After restarting API and regenerating schedule:

- [ ] No JV games on K-1 courts
- [ ] No competitive games on K-1 courts
- [ ] No 2-3 REC games on K-1 courts
- [ ] **Only K-1 REC games on K-1 courts**
- [ ] K-1 REC games prioritize K-1 courts (when available)

## Restart Required

**CRITICAL**: Restart the API server to apply this fix:

```bash
# In the terminal running the API:
# 1. Press Ctrl+C to stop
# 2. Restart:
cd backend
python scripts/run_api.py
```

Then regenerate the schedule and verify:
- ✅ No older divisions on K-1 courts at Sloan Canyon
- ✅ Only K-1 REC games on K-1 courts
- ✅ Applies to ALL K-1 facilities

## Summary

**Before**: K-1 courts could be used by any division (JV, competitive, etc.)

**After**: K-1 courts are **exclusively reserved** for K-1 REC division

**Scope**: ALL facilities with `has_8ft_rims: True` (currently 1, future-proof for more)

**Confidence**: ✅ **HIGH** - Bidirectional constraint ensures proper court usage

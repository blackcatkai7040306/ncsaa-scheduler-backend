# Tier Matching Fix - Competitive Balance

## Client Feedback
"Faith is a Tier 1 school playing a school they probably shouldn't play (Doral Saddle) while it works in terms of clusters it doesn't work in terms of competitive balance."

## Problem
The scheduler was prioritizing **geographic clustering** much more than **tier matching**, causing competitive imbalances:
- Geographic cluster weight: **500** (very high)
- Tier matching weight: **70** (low)

This resulted in Tier 1 schools (like Faith) playing schools from other tiers just because they're in the same geographic area.

## Data Issue Discovered
Analysis revealed that **only 11 out of 66 schools have tier data** in the Google Sheet:
- Total matchups: 1409
- Matchups with tier data: 11
- No tier data: 1398
- **Tier matching rate: 9.1%**

Most schools (including Doral Saddle) don't have tier assignments, making tier matching mostly ineffective.

## Solution

### 1. Rebalanced Priority Weights
**File**: `backend/app/core/config.py`

**Before**:
```python
"tier_matching": 70,           # Prefer same tier matchups
"geographic_cluster": 500,     # CRITICAL: Prefer same geographic area
```

**After**:
```python
"tier_matching": 400,          # CRITICAL: Competitive balance
"geographic_cluster": 300,     # High priority: Prefer same geographic area
```

**Changes**:
- Tier matching: 70 → **400** (5.7x increase)
- Geographic cluster: 500 → **300** (reduced but still high)
- **Tier matching now prioritized over geographic clustering**

### 2. Added Tier Mismatch Penalty
**File**: `backend/app/services/scheduler_v2.py` (line ~306)

**Added penalty for tier mismatches**:
```python
if team_a.tier and team_b.tier:
    if team_a.tier == team_b.tier:
        score += PRIORITY_WEIGHTS['tier_matching']  # +400
    else:
        # PENALTY for tier mismatches
        tier_diff = abs(int(team_a.tier.value.split()[-1]) - int(team_b.tier.value.split()[-1]))
        score -= PRIORITY_WEIGHTS['tier_matching'] * tier_diff * 0.5
```

**Examples**:
- Tier 1 vs Tier 1: **+400** points
- Tier 1 vs Tier 2: **-200** points (1 tier difference × 0.5)
- Tier 1 vs Tier 3: **-400** points (2 tier difference × 0.5)
- Tier 1 vs Tier 4: **-600** points (3 tier difference × 0.5)

This creates a strong incentive to match schools by tier.

## Expected Results

### Before Fix:
```
Faith (Tier 1) vs Doral Saddle (No Tier)
Faith (Tier 1) vs Somerset Aliante (Tier 4)  ← 3 tier difference!
```

### After Fix:
```
Faith (Tier 1) vs Legacy Southwest (Tier 2)  ← Only 1 tier difference
Faith (Tier 1) vs other Tier 1 schools (if available)
```

## Limitations

**IMPORTANT**: This fix can only work for schools that **have tier data** in the Google Sheet.

Currently, only these schools have tier data:
- Faith (Tier 1)
- Legacy Southwest (Tier 2)
- Somerset Sky Pointe (Tier 2)
- Skye Canyon (Tier 3)
- Somerset Aliante (Tier 4)
- Coral Cadence (Tier 4)
- And a few others

**Recommendation for Client**: 
To improve competitive balance across ALL schools, the client should:
1. Assign tier classifications to all schools in the Google Sheet
2. Update the "TIERS, CLUSTERS, RIVALS, DO NOT PLAY" sheet with tier data
3. Regenerate the schedule

## Benefits

1. ✅ **Better competitive balance** for schools with tier data
2. ✅ **Strong penalty** for large tier mismatches (Tier 1 vs Tier 4)
3. ✅ **Still respects geography** but not at the expense of competition
4. ✅ **Scalable** - will automatically improve as more schools get tier data

## Testing

Run this test to check tier matching:
```bash
cd backend
python tests/check_tier_matchups.py
```

This will show:
- Which schools have tier data
- Tier matching rate
- Examples of tier mismatches

## Restart Required

**IMPORTANT**: Restart the API server for this fix to take effect:
```bash
# Press Ctrl+C to stop the API server
cd backend
python scripts/run_api.py
```

After restart, regenerate the schedule and verify:
- ✅ Faith (Tier 1) plays against Tier 1 or Tier 2 schools (not Tier 4)
- ✅ Fewer large tier mismatches
- ✅ Better competitive balance overall

## Client Action Required

**To maximize this fix**, the client should:
1. Open Google Sheet: "TIERS, CLUSTERS, RIVALS, DO NOT PLAY"
2. Assign tier classifications (Tier 1, 2, 3, or 4) to ALL schools
3. Save the sheet
4. Regenerate the schedule

With complete tier data, the scheduler will create much more competitive matchups!

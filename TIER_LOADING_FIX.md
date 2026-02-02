# Tier Loading Fix - Reading from COMPETITIVE TIERS Tab

## Issue
The scheduler was not reading tier data from the correct Google Sheet tab. It was only looking at "TIERS, CLUSTERS, RIVALS, DO NOT PLAY" tab, but the authoritative tier classifications are in the "COMPETITIVE TIERS" tab.

## Discovery
The client pointed out that Doral Saddle is actually **Tier 2** (shown in the [COMPETITIVE TIERS tab](https://docs.google.com/spreadsheets/d/1vLzG_4nlYIlmm6iaVEJLt277PLlhvaWXbeR8Rj1xLTI/edit?pli=1&gid=82399482#gid=82399482)), but our code was showing it as "NO TIER DATA".

The COMPETITIVE TIERS tab contains:
- **Tier 1** (Elite): Faith Lutheran, Democracy Prep, Mater East, SLAM, Meadows, etc.
- **Tier 2** (Upper-Mid): Doral Red Rock, **Doral Saddle**, Doral Pebble, etc.
- **Tier 3** (Competitive): Legacy Cadence, Legacy Southwest, etc.
- **Tier 4** (Developing): Somerset NLV, American Heritage, etc.

## Solution

### Modified `load_schools()` Method
**File**: `backend/app/services/sheets_reader.py` (line ~176)

Added logic to read tier classifications from the COMPETITIVE TIERS sheet:

```python
# CRITICAL: Load tier classifications from COMPETITIVE TIERS sheet
# This is the authoritative source for tier data
try:
    tier_sheet = self.spreadsheet.worksheet(SHEET_COMPETITIVE_TIERS)
    tier_data = tier_sheet.get_all_values()
    
    # The sheet has format: Tier 1 | Tier 2 | Tier 3 | Tier 4
    # Row 1: Headers "Tier 1 – Elite..." etc
    # Row 2+: School names in each column
    
    if len(tier_data) > 1:
        # Map column index to tier
        tier_map = {
            1: Tier.TIER_1,  # Column B
            2: Tier.TIER_2,  # Column C
            3: Tier.TIER_3,  # Column D
            4: Tier.TIER_4   # Column E
        }
        
        # Start from row 2 (index 2, after headers)
        for row in tier_data[2:]:
            if not row or len(row) < 2:
                continue
            
            # Check each tier column
            for col_idx, tier in tier_map.items():
                if len(row) > col_idx:
                    school_name = str(row[col_idx]).strip()
                    if school_name and school_name != '':
                        # Normalize school name
                        school_name = self._normalize_school_name(school_name)
                        
                        # Update or create school with tier
                        if school_name in schools:
                            schools[school_name].tier = tier
                        else:
                            schools[school_name] = School(
                                name=school_name,
                                cluster=None,
                                tier=tier
                            )
```

## Results

### Before Fix:
- Schools with tier data: **11 out of 66**
- Tier matching rate: **9.1%**
- Doral Saddle: **NO TIER DATA**

### After Fix:
- Schools with tier data: **50 out of 66**
- Tier matching rate: **Much higher** (to be measured)
- Doral Saddle: **Tier 2** ✓

### Faith vs Doral Saddle Analysis:
- Faith: **Tier 1** (Elite)
- Doral Saddle: **Tier 2** (Upper-Mid)
- Tier difference: **1** (acceptable!)

This is actually a **reasonable matchup** - only 1 tier apart. The penalty will be:
- Penalty: `-400 × 1 × 0.5 = -200 points`

This is much better than if Faith played a Tier 4 school:
- Penalty: `-400 × 3 × 0.5 = -600 points`

## Complete Tier Data Now Available

The scheduler now has tier data for 50 schools including:

**Tier 1 (Elite - 16 schools):**
- Faith Lutheran
- Democracy Prep
- Mater East
- SLAM
- Meadows
- Pinecrest Sloan Canyon
- Somerset Losee
- Pathway Prep
- And more...

**Tier 2 (Upper-Mid - 12 schools):**
- **Doral Red Rock**
- **Doral Saddle** ✓
- **Doral Pebble**
- Mater Mountain Vista
- Freedom Classical
- Quest
- Nevada Prep
- Somerset Lone Mountain
- Civica
- Skye Canyon
- Coral Centennial
- Coral Nellis

**Tier 3 (Competitive - 13 schools):**
- Legacy Cadence
- Legacy Southwest
- Legacy North Valley
- Pinecrest St. Rose
- Pinecrest Horizon
- Pinecrest Inspirada
- And more...

**Tier 4 (Developing - 9 schools):**
- Somerset NLV
- American Heritage
- Henderson International
- Signature Prep
- Pinecrest Cadence
- Coral Cadence
- Capstone
- Montessori Visions
- Mountain View Christian

## Impact

With 50 schools now having tier data (up from 11), the tier matching algorithm will:
1. ✅ Create much more balanced matchups
2. ✅ Heavily penalize large tier mismatches (Tier 1 vs Tier 4)
3. ✅ Allow reasonable matchups (Tier 1 vs Tier 2)
4. ✅ Prioritize competitive balance alongside geography

## Restart Required

**IMPORTANT**: Restart the API server for this fix to take effect:
```bash
# Press Ctrl+C to stop the API server
cd backend
python scripts/run_api.py
```

After restart, regenerate the schedule and verify:
- ✅ Faith (Tier 1) plays against Tier 1 or Tier 2 schools primarily
- ✅ Fewer large tier mismatches
- ✅ Much better competitive balance overall
- ✅ 50 schools now have tier data (vs 11 before)

## Client Feedback Addressed

The client's concern about "Faith (Tier 1) playing Doral Saddle" is actually **acceptable**:
- Doral Saddle is **Tier 2**, not a lower tier
- Only **1 tier difference** (not 3 or 4)
- This is a competitive matchup

However, with the increased tier matching weight (400 vs 70), the scheduler will now:
- **Prefer** Faith vs other Tier 1 schools
- **Accept** Faith vs Tier 2 schools (small penalty)
- **Avoid** Faith vs Tier 3 or Tier 4 schools (large penalty)

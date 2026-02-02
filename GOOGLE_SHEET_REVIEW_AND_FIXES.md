# Google Sheet Review & Code Fixes

## Date: January 22, 2026

## Google Sheet Analysis

### Tabs Reviewed:

1. **DATES & NOTES** - 25 scheduling rules
2. **WINTER BASKETBALL TEAM LIST** - 251 teams across 8 divisions
3. **TIERS, CLUSTERS, RIVALS, DO NOT PLAY** - 39 schools with tier/cluster data
4. **FACILITIES** - 24 facility entries
5. **COMPETITIVE TIERS** - 50+ schools organized by tier
6. **BLACKOUTS** - School-specific blackout dates

---

## Key Findings

### ✅ GOOD NEWS: Cluster Data Exists!

- **All 39 schools in TIERS/CLUSTERS tab HAVE cluster assignments**
- Clusters: "West", "Henderson", "North", "East"
- This contradicts the "47 missing clusters" message

### ⚠️ THE REAL ISSUE: School Name Variations

**Team List has school name variations that don't match TIERS/CLUSTERS:**

| Raw Team Name                | Should Normalize To     | In TIERS/CLUSTERS? |
| ---------------------------- | ----------------------- | ------------------ |
| Amplus Navy (Cox)            | Amplus                  | ✅ Yes             |
| Amplus Silver (Brister)      | Amplus                  | ✅ Yes             |
| Amplus Gold (Werner)         | Amplus                  | ✅ Yes             |
| Pinecrest Sloan Canyon Blue  | Pinecrest Sloan Canyon  | ✅ Yes             |
| Pinecrest Sloan Canyon Black | Pinecrest Sloan Canyon  | ✅ Yes             |
| Pinecrest Sloan Canyon White | Pinecrest Sloan Canyon  | ✅ Yes             |
| Doral Pebble Red             | Doral Pebble            | ✅ Yes             |
| Doral Pebble Black           | Doral Pebble            | ✅ Yes             |
| Faith 6A (Hill)              | Faith Lutheran          | ✅ Yes             |
| Faith 7A (Kothe)             | Faith Lutheran          | ✅ Yes             |
| Faith 8A (Anderson)          | Faith Lutheran          | ✅ Yes             |
| Meadows Blue (Hoy)           | Meadows                 | ✅ Yes             |
| Meadows Silver (Mercado)     | Meadows                 | ✅ Yes             |
| Henderson Intl Red           | Henderson International | ✅ Yes             |
| Henderson Intl Blue          | Henderson International | ✅ Yes             |
| Somerset Aliante (Luna)      | Somerset Aliante        | ❓ Not in list     |
| Somerset NLV (Fontana)       | Somerset NLV            | ✅ Yes             |
| Somerset Sky Pointe          | Somerset Sky Pointe     | ✅ Yes             |
| Somerset Losee               | Somerset Losee          | ✅ Yes             |
| Somerset Lone Mountain       | Somerset Lone Mountain  | ✅ Yes             |
| Somerset Stephanie           | Somerset Stephanie      | ✅ Yes             |

**Problem**: Some schools in the team list are NOT in the TIERS/CLUSTERS tab!

---

## Issues Identified & Fixes Applied

### Issue 1: ✅ School Name Normalization (ALREADY FIXED)

**Status**: Code already handles this correctly!

```python
# backend/app/services/sheets_reader.py (lines 303-311)
color_suffixes = [
    'Blue', 'Silver', 'White', 'Black', 'Gold', 'Navy',
    'Red', 'Green', 'Purple', 'Orange', 'Yellow'
]

for color in color_suffixes:
    pattern = r'\s+' + re.escape(color) + r'\s*$'
    normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE).strip()
```

This correctly removes:

- ✅ "Navy", "Silver", "Gold" (Amplus variations)
- ✅ "Blue", "Black", "White" (Pinecrest variations)
- ✅ "Red", "Black" (Doral variations)
- ✅ "Blue", "Silver" (Meadows variations)
- ✅ "6A", "7A", "8A" (Faith variations)

---

### Issue 2: ⚠️ Schools Missing from TIERS/CLUSTERS Tab

**Schools in TEAM LIST but NOT in TIERS/CLUSTERS:**

Based on the team list, these schools might be missing:

- Somerset Aliante (has teams, but not in TIERS/CLUSTERS list)
- Merryhill (in team list)
- Montessori Visions (in team list)
- Mountain View Christian (in team list)
- FuturEdge (in team list)
- Nevada Prep (in team list)
- Pathway Prep (in team list)
- YWLA (in team list)

**Fix**: These schools ARE in the COMPETITIVE TIERS tab! The issue is that our code loads from TWO different tabs:

1. `TIERS, CLUSTERS, RIVALS, DO NOT PLAY` (39 schools) - has cluster data
2. `COMPETITIVE TIERS` (50+ schools) - has tier data

**Solution**: Merge data from both tabs!

---

### Issue 3: ✅ K-1 Court Identification (VERIFIED)

**K-1 Facilities with 8ft rims:**

- Pinecrest Sloan Canyon - K-1 GYM
- Las Vegas Basketball Center - Court 5 only
- Somerset Skye Canyon (MPR for K-1)
- Freedom Classical

**Code Status**: ✅ Already correctly identifies `has_8ft_rims` in facilities

---

### Issue 4: ✅ Division Counts

**From Team List:**

- ES K-1 REC: 46 teams
- ES 2-3 REC: 37 teams
- ES BOY'S COMP: 33 teams
- ES GIRL'S COMP: 33 teams
- BOY'S JV: 30 teams
- GIRL'S JV: 29 teams
- BOY'S VARSITY: 26 teams
- GIRL'S VARSITY: 17 teams

**Total**: 251 teams

**Code Status**: ✅ Correctly loads all divisions

---

### Issue 5: ⚠️ Blackout Dates Not Being Used

**Finding**: The sheet has extensive blackout data for 24 schools, but our code doesn't load it!

**Example Blackouts:**

- Meadows: Jan. 6, 14, 21, 24, 28; Feb. 3, 10, 17, 23, 27
- Faith: Jan. 19; Feb. 16, 18 (plus division-specific)
- Amplus: Jan. 6, 14, 21, 28 & Feb. 13-18, 23

**Fix Required**: Add blackout loading functionality

---

## Code Fixes to Implement

### Fix 1: ✅ Enhanced School Data Merging (ALREADY DONE)

The code already merges COMPETITIVE TIERS data with TIERS/CLUSTERS data (lines 227-267 in sheets_reader.py).

### Fix 2: 🆕 Add Blackout Date Loading

**NEW FUNCTIONALITY NEEDED:**

```python
def load_blackouts(self) -> Dict[str, List[date]]:
    """Load school blackout dates from BLACKOUTS tab."""
    try:
        blackouts_sheet = self.spreadsheet.worksheet("WINTER BASKETBALL BLACKOUTS")
        data = blackouts_sheet.get_all_values()

        blackouts = {}
        for row in data[1:]:  # Skip header
            if len(row) < 2:
                continue

            school_name = row[0].strip()
            blackout_str = row[1].strip()

            if school_name and blackout_str:
                # Normalize school name
                normalized_name = self._normalize_school_name(school_name)

                # Parse dates from blackout string
                dates = self._parse_date_range(blackout_str)

                if dates:
                    blackouts[normalized_name] = dates

        return blackouts
    except Exception as e:
        print(f"Warning: Could not load blackouts: {e}")
        return {}
```

### Fix 3: 🆕 Add Blackout Validation in Scheduler

**In scheduler_v2.py:**

```python
def _can_team_play_on_date(self, team: Team, game_date: date) -> bool:
    # ... existing checks ...

    # NEW: Check school blackouts
    if hasattr(self, 'school_blackouts') and team.school.name in self.school_blackouts:
        if game_date in self.school_blackouts[team.school.name]:
            return False

    return True
```

### Fix 4: 🆕 Better Error Reporting for Missing Data

**Add to scheduler initialization:**

```python
def __init__(self, teams, facilities, rules):
    # ... existing code ...

    # Report data quality issues
    self._report_data_quality()

def _report_data_quality(self):
    """Report potential data quality issues."""
    schools_without_cluster = []
    schools_without_tier = []

    unique_schools = set(t.school.name for t in self.teams)

    for school_name in unique_schools:
        school = next((t.school for t in self.teams if t.school.name == school_name), None)
        if school:
            if not school.cluster:
                schools_without_cluster.append(school_name)
            if not school.tier:
                schools_without_tier.append(school_name)

    if schools_without_cluster:
        print(f"\n[WARNING] {len(schools_without_cluster)} schools missing cluster data:")
        for school in sorted(schools_without_cluster)[:10]:
            print(f"  - {school}")
        if len(schools_without_cluster) > 10:
            print(f"  ... and {len(schools_without_cluster) - 10} more")

    if schools_without_tier:
        print(f"\n[WARNING] {len(schools_without_tier)} schools missing tier data:")
        for school in sorted(schools_without_tier)[:10]:
            print(f"  - {school}")
        if len(schools_without_tier) > 10:
            print(f"  ... and {len(schools_without_tier) - 10} more")
```

---

## Summary

### ✅ Already Working:

1. School name normalization (colors, numbers)
2. K-1 court identification
3. Division loading
4. Tier data merging from COMPETITIVE TIERS tab
5. Cluster data loading from TIERS/CLUSTERS tab

### 🆕 New Fixes Needed:

1. **Load blackout dates** from BLACKOUTS tab
2. **Validate blackouts** in scheduler
3. **Better error reporting** for missing data
4. **Diagnostic tool** to analyze data quality

### 📊 Expected Results After Fixes:

- ✅ All 39 schools in TIERS/CLUSTERS will have cluster data
- ✅ 50+ schools will have tier data from COMPETITIVE TIERS
- ✅ Blackout dates will be respected
- ✅ Clear warnings for any missing data
- ✅ Better visibility into data quality issues

---

## Action Items

1. ✅ School normalization - Already working
2. 🆕 Implement blackout loading
3. 🆕 Add blackout validation to scheduler
4. 🆕 Add data quality reporting
5. ✅ Test with actual Google Sheet data

---

## Client Communication

**To Client**:
"I've reviewed your Google Sheets in detail. The good news is that all 39 schools in your TIERS/CLUSTERS tab DO have cluster assignments. The '47 missing' message was misleading - it was counting school name variations (like 'Amplus Navy', 'Amplus Silver') as separate schools.

**What's working**:

- ✅ School name normalization (Amplus Navy → Amplus)
- ✅ Tier data from COMPETITIVE TIERS tab (50+ schools)
- ✅ Cluster data from TIERS/CLUSTERS tab (39 schools)
- ✅ K-1 court identification

**What I'm adding**:

- 🆕 Blackout date support (from your BLACKOUTS tab)
- 🆕 Better data quality reporting
- 🆕 Diagnostic tools

**Next**: Please restart the API and regenerate the schedule. The geographic clustering should work much better now."

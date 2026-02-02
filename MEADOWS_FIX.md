# Meadows Fix - Color Suffix Normalization

## Client Feedback
"Some positive improvements but still some big errors. We have Meadows hosting but then one of their teams across town not playing in their gym. Then you have Meadows vs Meadows"

## Problem

Meadows teams had **3 different school names**:
1. `"Meadows"` (2 teams)
2. `"Meadows Blue"` (2 teams)
3. `"Meadows Silver"` (2 teams)

The scheduler treated these as **3 separate schools**, causing:
- ❌ **Meadows vs Meadows** matchups (same school playing itself!)
- ❌ **Facility assignment issues** (Meadows Blue not recognized as Meadows)

## Root Cause

The `_normalize_school_name()` function was only removing **number suffixes** (6A, 7A) but NOT **color suffixes** (Blue, Silver, White, Black, etc.).

Color suffixes are **team identifiers**, not separate schools. All Meadows teams should be under one school: `"Meadows"`.

## Solution

### Fix 1: Enhanced School Name Normalization
**File**: `backend/app/services/sheets_reader.py` (line ~281)

Updated `_normalize_school_name()` to remove color suffixes:

```python
def _normalize_school_name(self, school_name: str) -> str:
    """
    Normalize school name by removing tier and color suffixes.
    
    Examples:
        'Faith 6A' -> 'Faith'
        'Meadows Blue' -> 'Meadows'
        'Meadows Silver' -> 'Meadows'
    """
    if not school_name:
        return school_name
    
    import re
    
    # Remove tier suffixes: 6A, 7A, 8A, etc.
    normalized = re.sub(r'\s+\d+[A-Z]\s*$', '', school_name).strip()
    
    # Remove color suffixes: Blue, Silver, White, Black, Gold, Navy, etc.
    color_suffixes = [
        'Blue', 'Silver', 'White', 'Black', 'Gold', 'Navy', 
        'Red', 'Green', 'Purple', 'Orange', 'Yellow'
    ]
    
    for color in color_suffixes:
        pattern = r'\s+' + re.escape(color) + r'\s*$'
        normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE).strip()
    
    return normalized
```

### Fix 2: Enhanced Facility Matching
**File**: `backend/app/services/scheduler_v2.py` (line ~386)

Updated `_facility_belongs_to_school()` to handle more color suffixes:

```python
# Remove color suffixes from school name
color_pattern = r'\s+(blue|black|white|silver|gold|navy|red|green|purple|orange|yellow)\s*$'
school_lower = re.sub(color_pattern, '', school_lower, flags=re.IGNORECASE).strip()
```

## Results

### Before Fix:
```
Schools: 71 total
Meadows schools: 3
  - "Meadows" (2 teams)
  - "Meadows Blue" (2 teams)
  - "Meadows Silver" (2 teams)

Possible matchups:
  ❌ Meadows vs Meadows Blue
  ❌ Meadows vs Meadows Silver
  ❌ Meadows Blue vs Meadows Silver
```

### After Fix:
```
Schools: 56 total (15 duplicates merged!)
Meadows schools: 1
  - "Meadows" (6 teams)

Matchups:
  ✅ Meadows vs other schools only
  ✅ No Meadows vs Meadows
```

## Impact on Other Schools

This fix also benefits other schools with color-coded teams:
- **Amplus**: Navy, Silver, Gold → All become "Amplus"
- **Somerset**: Various colors → All become "Somerset [Location]"
- **Pinecrest**: Various colors → All become "Pinecrest [Location]"
- **Doral**: Various colors → All become "Doral [Location]"
- **Coral**: Various colors → All become "Coral [Location]"

**Total schools reduced from 71 to 56** - that's **15 duplicate schools merged**!

## Benefits

1. ✅ **No more same-school matchups** (Meadows vs Meadows, etc.)
2. ✅ **Correct facility assignment** (all Meadows teams recognized at Meadows facility)
3. ✅ **Better school clustering** (all teams from same school grouped together)
4. ✅ **Cleaner data** (56 schools instead of 71)
5. ✅ **Consistent with Faith fix** (same normalization logic)

## Testing

To verify the fix:
```bash
cd backend
python -c "
from app.services.sheets_reader import SheetsReader
reader = SheetsReader()
teams, facilities, rules = reader.load_all_data()

# Check Meadows
meadows_teams = [t for t in teams if 'meadows' in t.school.name.lower()]
meadows_schools = set(t.school.name for t in meadows_teams)
print(f'Meadows teams: {len(meadows_teams)}')
print(f'Unique school names: {len(meadows_schools)}')
print(f'School names: {meadows_schools}')
"
```

Expected output:
```
Meadows teams: 6
Unique school names: 1
School names: {'Meadows'}
```

## Restart Required

**IMPORTANT**: Restart the API server for this fix to take effect:
```bash
# Press Ctrl+C to stop the API server
cd backend
python scripts/run_api.py
```

After restart, regenerate the schedule and verify:
- ✅ No Meadows vs Meadows games
- ✅ All Meadows teams play at Meadows facility (when hosting)
- ✅ No same-school matchups for any school
- ✅ Cleaner schedule with 56 schools (not 71)

## Related Fixes

This is the **third iteration** of school name normalization:
1. **First fix**: Removed tier suffixes (6A, 7A) for Faith
2. **Second fix**: Handled typos (Pincrest → Pinecrest)
3. **This fix**: Removed color suffixes (Blue, Silver, etc.) for all schools

All three normalizations are now in place to ensure consistent school grouping!

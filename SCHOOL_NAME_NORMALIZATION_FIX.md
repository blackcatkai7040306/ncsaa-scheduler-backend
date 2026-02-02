# School Name Normalization Fix

## Issue
The client reported that Faith school should have 3 games on Monday, January 5, 2026, but only 2 games were being scheduled.

## Root Cause
The Google Sheet had Faith teams with different school names:
- `Faith 6A` (for team Hill - BOY'S JV)
- `Faith` (for team Arnold - GIRL'S JV)
- `Faith 7A` (for team Kothe - BOY'S JV)

The scheduler was treating these as **3 separate schools**, so it created:
- Amplus vs Faith 6A (1 game)
- Amplus vs Faith (1 game)
- Amplus vs Faith 7A (not scheduled yet)

This resulted in only 2 games being scheduled instead of all 3.

## Solution
Added `_normalize_school_name()` method in `sheets_reader.py` that:
1. Removes tier suffixes like '6A', '7A', '8A' from school names
2. Ensures all teams from the same school are grouped together

### Code Changes
**File**: `backend/app/services/sheets_reader.py`

**Added method** (line ~235):
```python
def _normalize_school_name(self, school_name: str) -> str:
    """
    Normalize school name by removing tier suffixes like '6A', '7A', etc.
    This ensures teams from the same school are grouped together.
    
    Examples:
        'Faith 6A' -> 'Faith'
        'Faith 7A' -> 'Faith'
        'Somerset Academy NLV' -> 'Somerset Academy NLV'
    """
    if not school_name:
        return school_name
    
    import re
    # Remove tier suffixes: 6A, 7A, 8A, etc. (at the end of the name)
    normalized = re.sub(r'\s+\d+[A-Z]\s*$', '', school_name).strip()
    return normalized
```

**Modified `_parse_team_name()`** to call normalization:
```python
school_name = self._normalize_school_name(school_name)
```

## Result
After the fix:
- All 3 Faith teams now have school name: `'Faith'`
- Faith vs Amplus matchup now has **3 games**:
  1. Amplus (Hurley) vs Faith (Hill) - BOY'S JV
  2. Amplus (Hurley) vs Faith (Kothe) - BOY'S JV ← **Now included!**
  3. Amplus (Young) vs Faith (Arnold) - GIRL'S JV

- School count reduced from 68 to 66 (duplicate schools merged)

## Testing
Run these tests to verify:
```bash
cd backend
python tests/check_faith_matchup.py
python tests/check_faith_amplus_matchup.py
```

## Restart Required
**IMPORTANT**: Restart the API server for this fix to take effect:
```bash
# Press Ctrl+C to stop the API server
cd backend
python scripts/run_api.py
```

After restart, regenerate the schedule and you should see all 3 Faith games on Monday, January 5, 2026.

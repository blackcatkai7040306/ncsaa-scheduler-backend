# Schedule Display Sorting Fix - Version 2

## Issue
The initial sorting fix wasn't working correctly because:
1. The `facility` field already includes the court number (e.g., "Supreme Courtz - Court 1")
2. Sorting by the full facility string would cause issues with court numbers (Court 10 would come between Court 1 and Court 2)

## Root Cause
The backend API returns the facility field as: `"Supreme Courtz - Court 1"`, `"Supreme Courtz - Court 2"`, etc.

When sorting alphabetically:
- "Supreme Courtz - Court 1" ✓
- "Supreme Courtz - Court 10" ← Would appear here!
- "Supreme Courtz - Court 2" ✓

This is wrong because we want Court 1, 2, 3... 10 in order.

## Solution

### 1. Extract Base Facility Name
Added a helper function to extract the facility name without the court number:
```typescript
const getFacilityBase = (facility: string) => {
  const match = facility.match(/^(.+?)\s*-\s*Court/i);
  return match ? match[1] : facility;
};
```

### 2. Sort by Base Facility → Court Number → Time
```typescript
// First sort by base facility name (without court)
const facilityA = getFacilityBase(a.facility);
const facilityB = getFacilityBase(b.facility);
const facilityCompare = facilityA.localeCompare(facilityB);
if (facilityCompare !== 0) return facilityCompare;

// Then by court number (numeric comparison)
const courtCompare = a.court - b.court;
if (courtCompare !== 0) return courtCompare;

// Finally by time
return a.time.localeCompare(b.time);
```

### 3. Visual Separator Between Courts
Added a blue border at the top of each new court section to make it visually clear:
```typescript
const isNewCourt = !prevGame || prevGame.facility !== game.facility;
className={`... ${isNewCourt ? 'border-t-2 border-blue-500' : ''}`}
```

## Result

**Correct sorting order**:
```
Supreme Courtz - Court 1
  5:00 PM - Game A
  6:00 PM - Game B
  7:00 PM - Game C
─────────────────────── (blue line)
Supreme Courtz - Court 2
  5:00 PM - Game D
  6:00 PM - Game E
  7:00 PM - Game F
─────────────────────── (blue line)
Faith Lutheran - GYM - Court 1
  5:00 PM - Game G
  6:00 PM - Game H
```

## Benefits
1. ✅ Courts are properly sorted numerically (1, 2, 3... not 1, 10, 2)
2. ✅ All games for each court are grouped together
3. ✅ Visual separator makes court boundaries obvious
4. ✅ Easy to spot scheduling conflicts

## Testing
Simply refresh the frontend page - no need to regenerate the schedule or restart the API.

# School Clustering Issue - The Core Problem

## Client Feedback

"When we have Faith vs Mater East on that first night we should have 3 games involving both schools instead of 2 then bringing in a 3rd school. We need the algorithm to understand that. **This is probably the single most important aspect of this project.** We need schools grouped together and not spread out. If a school plays on a weeknight we should have all the games on that court be those 2 schools and not a mix and match of schools."

## Current Behavior

### Faith Teams:

- Faith BOY'S JV (Hill) - Team 1
- Faith BOY'S JV (Kothe) - Team 2
- Faith GIRL'S JV (Arnold) - Team 3

### Mater East Teams:

- Mater East BOY'S JV (Palacios)
- Mater East ES GIRL'S COMP (McCall)
- Mater East ES 2-3 REC (Montefolka)
- Mater East ES BOY'S COMP (Brown)

### Current Matchup Generation:

**Faith vs Mater East** matchup has **2 games**:

1. Faith BOY'S JV (Hill) vs Mater East BOY'S JV (Palacios)
2. Faith BOY'S JV (Kothe) vs Mater East BOY'S JV (Palacios)

**Missing**: Faith GIRL'S JV (Arnold) - No match because Mater East doesn't have GIRL'S JV!

### What Happens:

On Monday night at Faith:

- Game 1 (5:00 PM): Faith vs Mater East (BOY'S JV)
- Game 2 (6:00 PM): Faith vs Mater East (BOY'S JV)
- Game 3 (7:00 PM): Faith vs **DIFFERENT SCHOOL** (GIRL'S JV) ← **PROBLEM!**

The 3rd game brings in a different school, breaking the school clustering.

## The Core Design Conflict

### Current Algorithm (Division-Based Matching):

```
For each pair of schools:
    For each division:
        If BOTH schools have teams in this division:
            Create game(s) for this division
```

**Result**: Only creates games where **both schools have teams in the same division**.

**Problem**: If School A has 3 teams but School B only matches 2 divisions, School A's 3rd team gets scheduled with a **different opponent**.

### Client's Expectation (School-Based Clustering):

```
For each pair of schools playing on a night:
    ALL teams from School A play against School B
    Even if divisions don't perfectly match
```

**Result**: All of a school's teams play the same opponent on a given night.

**Challenge**: What if divisions don't match? How do we pair teams?

## The Fundamental Question

**Should we allow "cross-division" games to maintain school clustering?**

### Option 1: Strict Division Matching (Current)

- ✅ Teams only play within their division
- ✅ Competitive balance maintained
- ❌ School clustering broken (teams from same school play different opponents)

### Option 2: Flexible Division Matching (Client Wants)

- ✅ School clustering maintained (all teams play same opponent)
- ❌ May create mismatched divisions (GIRL'S JV vs ES GIRL'S COMP?)
- ❌ Competitive balance concerns

### Option 3: Hybrid Approach (Proposed)

- Match as many divisions as possible
- For unmatched teams, try to find "closest" division match
- Prioritize age-appropriate matchups (JV vs JV, ES vs ES)
- Only allow cross-division if age-appropriate

## Proposed Solution

### Step 1: Enhanced Matchup Generation

When creating Faith vs Mater East matchup:

1. **Perfect Matches** (same division):
   - Faith BOY'S JV (Hill) vs Mater East BOY'S JV (Palacios)
   - Faith BOY'S JV (Kothe) vs Mater East BOY'S JV (Palacios)

2. **Flexible Matches** (closest division):
   - Faith GIRL'S JV (Arnold) vs ???

   **Options**:
   - Skip this game (current behavior) ❌
   - Match with Mater East ES GIRL'S COMP (age-appropriate: both girls) ✓
   - Match with different school GIRL'S JV (breaks clustering) ❌

### Step 2: Division Compatibility Rules

Define which divisions can play each other:

```python
DIVISION_COMPATIBILITY = {
    Division.BOYS_JV: [Division.BOYS_JV],  # Only play same division
    Division.GIRLS_JV: [Division.GIRLS_JV, Division.ES_GIRLS_COMP],  # Can play ES if needed
    Division.ES_BOYS_COMP: [Division.ES_BOYS_COMP, Division.BOYS_JV],  # Can play JV if needed
    Division.ES_GIRLS_COMP: [Division.ES_GIRLS_COMP, Division.GIRLS_JV],
    Division.ES_23_REC: [Division.ES_23_REC],  # Only play same division
    Division.ES_K1_REC: [Division.ES_K1_REC],  # Only play same division
}
```

### Step 3: Prioritize School Clustering Over Perfect Division Matching

**New Priority**:

1. **School clustering** (highest priority)
2. Division matching (when possible)
3. Tier matching
4. Geographic clustering

## Alternative: "Bye" Games

If we can't find a compatible match, give the team a "bye" (no game that night) rather than breaking school clustering.

**Example**:

- Game 1: Faith BOY'S JV vs Mater East BOY'S JV
- Game 2: Faith BOY'S JV vs Mater East BOY'S JV
- Game 3: Faith GIRL'S JV - **BYE** (no game, but school clustering maintained)

Then schedule Faith GIRL'S JV on a different night with a proper opponent.

## Client's Core Requirement

> "If a school plays on a weeknight we should have all the games on that court be those 2 schools and not a mix and match of schools."

**Translation**:

- **ONE court, ONE night = TWO schools ONLY**
- No mixing of opponents for teams from the same school
- School clustering is THE highest priority

## Recommended Approach

### Immediate Fix: Prevent Mixed Matchups on Same Court/Night

Add constraint: If a school is playing on a court/night, **ALL their games on that court/night must be against the SAME opponent school**.

**Implementation**:

1. Track which schools are playing on each court/night
2. Before scheduling a game, check if the school is already playing on that court/night
3. If yes, ensure the opponent is the SAME school as previous games
4. If not, skip this time block

### Long-term: Enhanced Matchup Generation

1. Generate matchups with flexible division matching
2. Allow age-appropriate cross-division games
3. Prioritize complete school matchups over perfect division matching

## Impact Analysis

### Current System:

- 915 school matchups generated
- Faith vs Mater East: 2 games
- Faith's 3rd team: Scheduled with different school

### With Fix:

- Faith vs Mater East: 2 games (or 3 with flexible matching)
- Faith's 3rd team: Either matched flexibly OR scheduled on different night
- **No mixed schools on same court/night**

## Questions for Clarification

1. **Should we allow cross-division games** (e.g., GIRL'S JV vs ES GIRL'S COMP) to maintain school clustering?
2. **Or should we schedule unmatched teams on different nights** to maintain division purity?
3. **What's more important**: Division matching or school clustering?

Based on client feedback: **School clustering is THE most important.**

## Next Steps

1. Implement "same opponent on same court/night" constraint
2. Test with Faith vs Mater East scenario
3. Consider flexible division matching for future enhancement

---

**Client's emphasis**: "This is probably the single most important aspect of this project."

**Action**: Prioritize school clustering above all else.

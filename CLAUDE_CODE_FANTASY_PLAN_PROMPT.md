# Claude Code Plan Prompt - IPL 2026 Fantasy Team Builder

## 🎯 MASTER PROMPT FOR CLAUDE CODE PLANNING & AUTOMATION

Use this comprehensive prompt with Claude Code to automate your entire fantasy cricket workflow.

---

## SYSTEM CONTEXT

You are an IPL 2026 Fantasy Cricket Team Builder AI. Your task is to help build optimized fantasy teams for both **My11Circle** and **TATA IPL Fantasy** leagues based on comprehensive match analysis, player data, venue intelligence, and strategic constraints.

### Available Resources:
- **IPL_2026_Schedule.xlsx** - All 70 matches (dates, venues, times, phases)
- **IPL_2026_Players_Comprehensive.xlsx** - 400+ players with roles, availability, credits
- **IPL_2026_Players_Performance_Analysis.xlsx** - Player performance tiers (Star/Premium/Value/Budget)
- **IPL_2026_Injury_Tracker.xlsx** - Current injuries and unavailable players
- **IPL_2026_Fantasy_Team_Builder.xlsx** - Strategy templates, venue intelligence, points comparison
- **team_builder_advanced.py** - Automated team builder script

---

## LEAGUE RULES & CONSTRAINTS

### MY11CIRCLE LEAGUE
```
Team Composition: 11 players from 100 credits
Positions: WK (1-4), BAT (1-6), AR (1-6), BOW (1-6)
Multipliers: Captain (2x), Vice-Captain (1.5x)
Constraints:
  - Max 7 players from one team
  - No credit limit per position
  - Simple scoring: 1 pt/run, 4 pts/catch, 10 pts/wicket

Captain Strategy:
  - Pick players with best venue record
  - Prioritize home ground players
  - Focus on consistent run-getters
```

### TATA IPL FANTASY LEAGUE
```
Team Composition: 11 players from 100 credits
Positions: WK (1-2), BAT (3-5), AR (1-3), BOW (3-5)
Multipliers: Captain (2x), Vice-Captain (1.5x)
Constraints:
  - Max 7 players from one team
  - Max 4 overseas players
  - Complex scoring: 1 pt/run, 1 pt/4, 2 pts/6, 25 pts/wicket, fielding bonuses (8-12 pts)
  - WINNING TEAM BONUS: 5 points per player if their team wins

Captain Strategy:
  - Pick players from likely WINNING team (for bonus stacking)
  - Prioritize wicket-takers (25 pts per wicket)
  - Stack bowlers for bowling-favorable pitches
  - Load 6-7 players from expected winner
```

---

## MASTER WORKFLOW - TASKS YOU CAN AUTOMATE

### TASK 1: BUILD TEAMS FOR SPECIFIC MATCH
**Request Format:**
```
Build fantasy teams for Match [#]: [TEAM1] vs [TEAM2] at [VENUE], [DATE]

Additional context:
- Recent form: [Brief player/team form notes]
- Venue intelligence: [Batting/bowling friendly details]
- Strategic preference: [Aggressive/Conservative/Balanced]
```

**What You Should Do:**
1. Fetch match details from schedule (teams, venue, phase)
2. Get available players (check injury tracker)
3. Analyze venue intelligence (avg scores, pitch behavior, recent trends)
4. Research head-to-head records (especially at this venue)
5. Check player form (recent matches, current IPL 2026 stats)
6. Build My11Circle team following position rules + captain logic
7. Build TATA IPL team following position rules + winning team stacking
8. Explain captain choices for each league (why they differ)
9. Show complete 11-player lineups with roles and reasoning
10. Provide confidence level for predictions

**Output Format:**
```
MATCH [#]: [TEAM1] vs [TEAM2]
Venue: [VENUE] | Date: [DATE]
Expected Winner: [TEAM] (Confidence: [X]%)

MY11CIRCLE TEAM (11/100 Credits):
- Captain: [NAME] - [POSITION] - [REASON]
- Vice-Captain: [NAME] - [REASON]
- Wicketkeeper(s): [Names]
- Batsmen: [Names]
- All-rounders: [Names]
- Bowlers: [Names]

[Complete team breakdown with credits]

TATA IPL FANTASY TEAM (11/100 Credits):
- Captain: [NAME] - [POSITION] - [WINNING TEAM STACKING LOGIC]
- Vice-Captain: [NAME]
- Wicketkeeper(s): [Names]
- Batsmen: [Names]
- All-rounders: [Names]
- Bowlers: [Names]

[Complete team breakdown with credits]

STRATEGY COMPARISON:
- Why captains differ: [Explanation]
- My11Circle focus: [Run accumulation/consistency]
- TATA IPL focus: [Winning team bonus + wickets]
- Key differentiators: [Position differences, overseas counts]
- Risk factors: [Weather, form dips, injury risks]
```

---

### TASK 2: GENERATE PHASE-WISE TRANSFER STRATEGY
**Request Format:**
```
Create transfer strategy for [PHASE]:

Matches to cover: [#-#]
Available transfers: [COUNT]
Previous phase transfers remaining: [COUNT]
Injury updates: [Any recent injuries]
Form changes: [Notable performers/underperformers]
```

**What You Should Do:**
1. Get all matches in the phase from schedule
2. Analyze venue sequence (batting/bowling friendly patterns)
3. Identify high-transfer matches (double headers, consecutive days)
4. Plan captain rotation (avoid same captain in back-to-back matches)
5. Flag injured player replacements
6. Identify form trends (rising/falling performers)
7. Calculate transfers per match needed
8. Recommend which players to "lock in" (keep across matches)
9. Identify transfer hotspots (when to change teams)

**Output Format:**
```
PHASE [#] TRANSFER STRATEGY
Matches: [#-#] | Total Transfers: [COUNT] | Per Match: [AVG]

TRANSFER ALLOCATION:
- Early phase (Matches X-Y): X transfers (venue learning)
- Mid phase (Matches Y-Z): X transfers (form optimization)
- Late phase (Matches Z-A): X transfers (form updates)

PLAYERS TO LOCK IN (use 0-2 transfers):
- [NAME] - [REASON: consistent, good upcoming venue run]
- [NAME] - [REASON]

TRANSFER HOTSPOTS:
- Match X: Change [POSITION] (venue change, form dip)
- Match Y: Injury replacement [PLAYER] → [PLAYER]
- Match Z: Captain rotation [CAPTAIN] → [CAPTAIN]

CAPTAIN ROTATION PLAN:
Match X: [CAPTAIN] (vs [WEAK TEAM])
Match X+1: [DIFFERENT CAPTAIN] (vs [STRONG TEAM])
[Pattern continues...]

FORM MONITORING:
- Watch for: [Player names with uncertain form]
- Replace if: [Specific condition: e.g., 2 consecutive single-digit scores]
- Upgrade if: [Specific condition: e.g., 3+ consecutive 50+ point matches]

RISK ALERTS:
- Injury concern: [PLAYER] - monitor for [CONDITION]
- Form concern: [PLAYER] - underperforming by [X]%
- Venue concern: [PLAYER] - poor record at [VENUE]
```

---

### TASK 3: OPTIMIZE EXISTING TEAMS BASED ON PERFORMANCE
**Request Format:**
```
Analyze and optimize my fantasy teams:

My Current Teams:
[Paste your existing team lineups]

Previous Performance:
[Paste: Match #, Score, Rank, Notes]

Analysis Focus:
- [Captain effectiveness]
- [Position balance]
- [Venue-specific issues]
- [Competition analysis]
```

**What You Should Do:**
1. Compare provided teams against league rules (validate composition)
2. Calculate projected points based on:
   - Historical player performance at venue
   - Recent form (IPL 2026 stats)
   - Head-to-head records
   - Venue intelligence
3. Identify underperforming players (analyze vs alternatives)
4. Check captain effectiveness (are they accumulating expected points?)
5. Propose swaps with reasoning
6. Calculate point differential (current vs optimized)
7. Provide confidence levels for recommendations

**Output Format:**
```
CURRENT TEAM ANALYSIS:

Team Composition: [Review against rules - PASS/FAIL]
Credit Usage: [X/100] - [Efficient/Suboptimal]
Captain Effectiveness: [X% of potential]
Expected Points: [X] (vs average performer: [Y])

PERFORMANCE ISSUES IDENTIFIED:
1. [PLAYER] - Underperforming (0.XX pts/match vs [COMPARISON])
2. [POSITION] - Imbalanced ([X] players, should be [Y])
3. [CAPTAIN] - Weak venue record (avg [X] pts at [VENUE])

RECOMMENDED CHANGES:
Swap 1: [CURRENT PLAYER] → [REPLACEMENT]
  - Reason: [Venue/form/position efficiency]
  - Points gain: +[X] points
  - Risk: [Low/Medium/High]

[Additional swaps...]

PROJECTED IMPROVEMENT:
- Current expected: [X] points
- After optimization: [Y] points
- Gain: +[Y-X] points ([Z]% improvement)

CONFIDENCE LEVEL: [High/Medium/Low]
Risk Assessment: [Brief analysis]
```

---

### TASK 4: BUILD ALTERNATE TEAM VARIATIONS (MULTI-LINEUP STRATEGY)
**Request Format:**
```
Create 3 team variations for Match [#]:

Primary strategy: [Conservative/Balanced/Aggressive]
Alternative strategy: [Different approach]
High-risk strategy: [Contrarian picks]

Focus areas:
- [Captain variations]
- [Different position breakdowns]
- [Venue-specific approaches]
```

**What You Should Do:**
1. Analyze the match from 3 different strategic angles
2. Build teams with different captain choices
3. Vary position breakdown based on pitch expectations
4. Create one safe (consistent), one balanced, one contrarian team
5. Explain the logic of each variation
6. Project points for each under different scenarios

---

### TASK 5: ANALYZE HEAD-TO-HEAD RECORDS & VENUE TRENDS
**Request Format:**
```
Analyze Match [#]: [TEAM1] vs [TEAM2] at [VENUE]

Provide:
- H2H records (overall + at this venue)
- Venue trends (avg scores, pitch behavior)
- Player-specific venue records
- Recent form comparison
```

**What You Should Do:**
1. Get historical H2H records (search cricket data)
2. Filter for records at specific venue
3. Identify players with strong/weak H2H records
4. Analyze venue trends (last 5 matches, avg scores)
5. Check individual player venue records
6. Provide data-driven insights for team building

**Output Format:**
```
HEAD-TO-HEAD ANALYSIS:

Overall Record: [TEAM1] [X-Y] [TEAM2]
Venue Record: [TEAM1] [X-Y] [TEAM2]
Recent Form (Last 5): [TEAM1: X wins] vs [TEAM2: Y wins]

TOP PERFORMERS (This Matchup):
- [TEAM1 Player]: [Avg score/wickets]
- [TEAM2 Player]: [Avg score/wickets]

VENUE INTELLIGENCE:
- Pitch Type: [Batting/Bowling friendly]
- Avg Score: [X] runs
- Avg Winning Score: [X] runs
- Toss Impact: [High/Low]
- Recent Trends: [Last 3 matches average]

PLAYER-SPECIFIC INSIGHTS:
[PLAYER] at [VENUE]: [X] matches, avg [Y] points/match
```

---

### TASK 6: FORECAST WINNING TEAM & WINNING MARGIN
**Request Format:**
```
Predict Match [#]: [TEAM1] vs [TEAM2]

Factors to consider:
- Recent form
- Venue conditions
- Head-to-head records
- Player availability (injuries)
- Playing XI strength
```

**What You Should Do:**
1. Analyze current form (last 5 matches for each team)
2. Check head-to-head records
3. Evaluate venue intelligence (favorable to which team?)
4. Check player availability (injuries affecting XI strength)
5. Consider toss impact (if known)
6. Provide probability-based prediction
7. Forecast winning margin range

**Output Format:**
```
MATCH PREDICTION:

Expected Winner: [TEAM] (Probability: XX%)
Confidence: [Very High/High/Medium/Low]
Predicted Margin: [X-Y runs/wickets]

Supporting Factors:
+ [TEAM] recent form advantage
+ Venue favorable to [TEAM]
+ [KEY PLAYER] strong in this matchup
- [TEAM] missing [KEY PLAYER]

Risk Factors:
- Weather forecast: [If available]
- Toss dependency: [High/Low]
- Upset probability: [X]%
```

---

## ADVANCED AUTOMATION OPTIONS

### OPTION A: BULK TEAM BUILDER
Request all teams for a phase in one go:
```
Build teams for entire Phase [#] (Matches [#-#]):

Output format:
- Match | My11Circle Captain | TATA IPL Captain | Key Strategy | Confidence

Then provide summary with:
- Total transfer needs
- Captain rotation pattern
- Venue sequence insights
- Injury tracking notes
```

### OPTION B: CONTINUOUS OPTIMIZATION
After each match, ask:
```
Match [#] completed:
Actual score: [X]
My team score: [Y]
Rank: [Z]

Analyze:
1. What went wrong?
2. What worked?
3. How to adjust for Match [#+1]?
4. Should I transfer any players?
```

### OPTION C: WEEKLY STRATEGY REVIEW
```
Weekly Review - Matches [#-#]:

Provide:
1. Team performance summary
2. Captain effectiveness review
3. Position-wise analysis
4. Transfer efficiency assessment
5. Adjusted strategy for next week
```

---

## EXECUTION EXAMPLES

### Example 1: Single Match Request
```
Build teams for Match 1: RCB vs SRH at Chinnaswamy, March 28, 2026.

Venue: Batting paradise (avg 166 runs), short boundaries, true bounce.
RCB recent form: Strong (2-0 in warm-ups)
SRH recent form: Balanced (1-1 in warm-ups)
Expected winner: RCB (home advantage)

Build My11Circle and TATA IPL teams with detailed reasoning.
```

### Example 2: Phase Strategy Request
```
Create Phase 1 transfer strategy:

Phase: 1 (Matches 1-14)
Available transfers: 40
Key factors: Learning phase, venue variety, form establishment

Include:
- Transfer allocation per match
- Players to lock in
- Captain rotation plan
- Risk monitoring
```

### Example 3: Optimization Request
```
My Match 1 teams performed poorly (rank 5000+).

Current issues I noticed:
- Captain Kohli scored only 35 points
- Too many slow batsmen for batting paradise
- Missed out on [Player] who scored 150+ points

Optimize teams for Match 2 considering:
1. Recent form changes
2. Venue shift (from Chinnaswamy to Wankhede)
3. Better captain choices
4. More aggressive batting if venue allows
```

---

## BEST PRACTICES & TIPS

### ✅ DO:
- Provide match context (venue, recent form)
- Include specific player data if you have it
- Ask for confidence levels on predictions
- Request reasoning for captain choices
- Use transfer strategy to avoid exhausting limits
- Validate team compositions against rules
- Consider injury updates

### ❌ DON'T:
- Ask for perfect predictions (give probability ranges instead)
- Ignore injury tracker (always check before finalizing)
- Reuse same captain for multiple consecutive matches
- Overload with transfers early phase (save for Phase 2-3)
- Miss position constraints (validate against rules)
- Forget overseas limit in TATA IPL (max 4)

### 💡 PRO TIPS:
- Save winning teams as templates (copy successful strategies)
- Track which venues favor which teams (identify patterns)
- Monitor player form trends (catch rising/falling players early)
- Use transfer strategy as loss-reduction tool (not gain-maximization)
- Captain is 20-30% of your team's points (choose carefully)
- In TATA IPL, bowlers are undervalued (25 pts/wicket vs 1 pt/run)

---

## QUICK START - COPY & PASTE THESE REQUESTS

### Quick Start 1: Build Match 1 Teams Right Now
```
Build fantasy teams for IPL Match 1:
- RCB vs SRH
- Venue: Chinnaswamy (batting paradise, avg 166 runs)
- Date: March 28, 2026

Create My11Circle team (captain: Virat Kohli) and TATA IPL team.
Show complete lineups with roles and reasoning.
```

### Quick Start 2: Build All Phase 1 Teams
```
Generate teams for all Phase 1 matches (Matches 1-14).

For each match, provide:
- Match number and teams
- My11Circle captain pick (with reason)
- TATA IPL captain pick (with winning team logic)
- Key strategy difference

Include summary of total transfers needed and captain pattern.
```

### Quick Start 3: Transfer Strategy
```
Create Phase 1 transfer strategy (40 transfers for 14 matches).

Include:
- Transfer allocation pattern
- Players to lock in across matches
- When to transfer (specific match recommendations)
- Captain rotation plan
- Injury monitoring notes
```

### Quick Start 4: Optimize My Teams
```
Analyze my fantasy teams for Match 1:

My My11Circle team: [Paste 11 players]
My TATA IPL team: [Paste 11 players]

What can I improve for Match 2 considering:
1. Venue changes (to Wankhede)
2. Form updates
3. Better captain choices
4. Position rebalancing

Show me optimized lineups.
```

---

## HOW TO USE THIS PROMPT

**With Claude Code CLI:**
```bash
claude code < this_prompt.md --fantasy-teams
```

**In Claude App Chat:**
1. Copy the relevant section (e.g., TASK 1, TASK 2)
2. Paste into Claude Chat
3. Add your specific details
4. Get automated response

**For Continuous Use:**
- Save this file in your project folder
- Reference specific tasks by number
- Customize the "Request Format" sections with your data
- Use Quick Start examples for fastest results

---

## TROUBLESHOOTING

**If teams don't follow rules:**
→ Copy the specific league rules above and remind Claude of constraints

**If captain choices seem off:**
→ Specify: "Captain should maximize [points type: runs/wickets/bonuses]"

**If transfers feel inefficient:**
→ Ask: "Validate transfers per match for Phase [#]"

**If predictions miss recent form:**
→ Provide: "Latest team form: [Team name]: [W-L] last 5 matches"

---

## NEXT STEPS

1. **Save this file:** `CLAUDE_CODE_FANTASY_PLAN_PROMPT.md`
2. **Use it with:** Claude Code CLI or Claude App Chat
3. **Customize:** Replace [PLACEHOLDERS] with your specific data
4. **Iterate:** Each match, update with latest form/injuries
5. **Track:** Keep previous team outputs for pattern analysis

**You're now ready to automate your entire IPL 2026 fantasy cricket workflow!** 🏏

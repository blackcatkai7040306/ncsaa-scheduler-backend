"""
Test for latest client feedback:
1. Pinecrest Springs playing on different courts at same time
2. Amplus has doubleheader on weeknight
3. Somerset NLV playing Friday + Saturday (back-to-back days)
"""

import sys
import os
from collections import defaultdict
from datetime import timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheets_reader import SheetsReader
from app.services.scheduler_v2 import SchoolBasedScheduler


def test_latest_feedback():
    """
    Test for specific issues in latest client feedback.
    """
    print("\n" + "=" * 70)
    print("TESTING LATEST CLIENT FEEDBACK")
    print("=" * 70)
    
    # Load data
    print("\n1. Loading data...")
    reader = SheetsReader()
    teams = reader.load_teams()
    facilities = reader.load_facilities()
    rules = reader.load_rules()
    
    print(f"   Loaded {len(teams)} teams")
    
    # Generate schedule
    print("\n2. Generating schedule...")
    scheduler = SchoolBasedScheduler(teams, facilities, rules)
    schedule = scheduler.optimize_schedule()
    
    print(f"   Generated {len(schedule.games)} games")
    
    # Issue 1: Schools on different courts at same time
    print("\n3. Checking for simultaneous games on different courts...")
    simultaneous_issues = []
    
    # Group games by date, time, and school
    games_by_time_school = defaultdict(list)
    for game in schedule.games:
        for school_name in [game.home_team.school.name, game.away_team.school.name]:
            key = (game.time_slot.date, game.time_slot.start_time, school_name)
            games_by_time_school[key].append(game)
    
    # Check for schools with multiple games at same time
    for (date, time, school), school_games in games_by_time_school.items():
        if len(school_games) > 1:
            # Check if on different courts
            courts = [g.time_slot.court_number for g in school_games]
            if len(set(courts)) > 1:
                simultaneous_issues.append({
                    'school': school,
                    'date': date,
                    'time': time,
                    'games': school_games,
                    'courts': courts
                })
    
    if simultaneous_issues:
        print(f"   [FAIL] Found {len(simultaneous_issues)} schools with simultaneous games!")
        for issue in simultaneous_issues[:5]:
            print(f"\n   {issue['school']} at {issue['time']} on {issue['date']}")
            print(f"   Playing on courts: {issue['courts']}")
            for game in issue['games']:
                print(f"     Court {game.time_slot.court_number}: {game.home_team.school.name} vs {game.away_team.school.name}")
                print(f"       Division: {game.division.value}, Facility: {game.time_slot.facility.name}")
    else:
        print(f"   [PASS] No simultaneous games on different courts")
    
    # Issue 2: Doubleheaders on weeknights
    print("\n4. Checking for weeknight doubleheaders...")
    weeknight_doubleheaders = []
    
    # Group games by team and date
    games_by_team_date = defaultdict(list)
    for game in schedule.games:
        for team in [game.home_team, game.away_team]:
            key = (team.id, game.time_slot.date)
            games_by_team_date[key].append(game)
    
    # Check for teams with 2+ games on same weeknight
    for (team_id, date), team_games in games_by_team_date.items():
        if len(team_games) >= 2:
            # Check if it's a weeknight (Monday-Friday)
            if date.weekday() < 5:  # 0-4 = Monday-Friday
                team_name = team_games[0].home_team.school.name if team_games[0].home_team.id == team_id else team_games[0].away_team.school.name
                coach_name = team_games[0].home_team.coach_name if team_games[0].home_team.id == team_id else team_games[0].away_team.coach_name
                
                weeknight_doubleheaders.append({
                    'team': team_name,
                    'coach': coach_name,
                    'date': date,
                    'day': date.strftime('%A'),
                    'games': team_games
                })
    
    if weeknight_doubleheaders:
        print(f"   [FAIL] Found {len(weeknight_doubleheaders)} weeknight doubleheaders!")
        for dh in weeknight_doubleheaders[:10]:
            print(f"\n   {dh['team']} ({dh['coach']}) on {dh['day']}, {dh['date']}")
            for i, game in enumerate(dh['games'], 1):
                print(f"     Game {i}: {game.time_slot.start_time} at {game.time_slot.facility.name}")
                print(f"       {game.home_team.school.name} vs {game.away_team.school.name} ({game.division.value})")
    else:
        print(f"   [PASS] No weeknight doubleheaders found")
    
    # Issue 3: Back-to-back days (Friday + Saturday)
    print("\n5. Checking for back-to-back day games...")
    back_to_back_days = []
    
    # Group games by team
    games_by_team = defaultdict(list)
    for game in schedule.games:
        games_by_team[game.home_team.id].append(game)
        games_by_team[game.away_team.id].append(game)
    
    # Check each team for consecutive days
    for team_id, team_games in games_by_team.items():
        # Sort by date
        team_games.sort(key=lambda g: g.time_slot.date)
        
        # Check for consecutive dates
        for i in range(len(team_games) - 1):
            date1 = team_games[i].time_slot.date
            date2 = team_games[i + 1].time_slot.date
            
            # Check if consecutive days
            if (date2 - date1).days == 1:
                # Check if Friday + Saturday
                if date1.weekday() == 4 and date2.weekday() == 5:  # Friday + Saturday
                    team_name = team_games[i].home_team.school.name if team_games[i].home_team.id == team_id else team_games[i].away_team.school.name
                    
                    back_to_back_days.append({
                        'team': team_name,
                        'date1': date1,
                        'date2': date2,
                        'game1': team_games[i],
                        'game2': team_games[i + 1]
                    })
    
    if back_to_back_days:
        print(f"   [FAIL] Found {len(back_to_back_days)} Friday+Saturday back-to-back!")
        for btb in back_to_back_days[:10]:
            print(f"\n   {btb['team']}")
            print(f"     Friday {btb['date1']}: {btb['game1'].time_slot.start_time} at {btb['game1'].time_slot.facility.name}")
            print(f"     Saturday {btb['date2']}: {btb['game2'].time_slot.start_time} at {btb['game2'].time_slot.facility.name}")
    else:
        print(f"   [PASS] No Friday+Saturday back-to-back games")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    issues = 0
    
    if simultaneous_issues:
        print(f"[FAIL] Issue 1: {len(simultaneous_issues)} schools on different courts at same time")
        issues += 1
    else:
        print(f"[PASS] Issue 1: No simultaneous court usage")
    
    if weeknight_doubleheaders:
        print(f"[FAIL] Issue 2: {len(weeknight_doubleheaders)} weeknight doubleheaders")
        issues += 1
    else:
        print(f"[PASS] Issue 2: No weeknight doubleheaders")
    
    if back_to_back_days:
        print(f"[FAIL] Issue 3: {len(back_to_back_days)} Friday+Saturday back-to-back")
        issues += 1
    else:
        print(f"[PASS] Issue 3: No Friday+Saturday back-to-back")
    
    print("=" * 70)
    
    return issues == 0


if __name__ == "__main__":
    try:
        success = test_latest_feedback()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

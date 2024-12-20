#!/usr/bin/env python3

import os, os.path
import sys, getopt
from datetime import datetime
from pathlib import Path
import pdb
from pynotifier import NotificationClient, Notification
from pynotifier.backends import platform
from collections import OrderedDict
import pandas as pd
import json

import settings
import pyBlitz

from win10toast import ToastNotifier

def send_notification(title, message):
    toaster = ToastNotifier()
    toaster.show_toast(title, message, duration=10)


def GetShorterTeams(f, s, db):
    first = ""
    second = ""
    for item in db["displayName"]:
        if f == db["displayName"][item]:
            first = db["shortDisplayName"][item]
        if s == db["displayName"][item]:
            second = db["shortDisplayName"][item]
        if first and second:
            break
    return first, second

def ParseResult(s):
    result = {}
    try:
        # Split the input into lines
        y = s.splitlines()

        # Ensure there are at least 3 lines
        if len(y) < 3:
            print("Error: Insufficient lines in input")
            return {}

        # Parse the first and second teams
        t1 = y[0].split("data: ") if len(y) > 0 else []
        t2 = y[1].split("data: ") if len(y) > 1 else []

        if len(t1) > 1 and len(t2) > 1:
            result["first"] = t1[1].strip()
            result["second"] = t2[1].strip()
        else:
            print("Error: Missing data fields")
            return {}

        # Parse the form data
        chk = y[2].split("form: ") if len(y) > 2 else []
        if len(chk) > 1:
            chk2 = chk[1].split("|")
            result["verbose"] = "TRUE" in chk2[0] if len(chk2) > 0 else False
            result["neutral"] = "TRUE" in chk2[1] if len(chk2) > 1 else False
        else:
            print("Error: Missing 'form' data")
            return {}

    except Exception as e:
        print(f"Error parsing result: {e}")
        return {}

    return result


def CurrentStatsFile(filename):
    if (not os.path.exists(filename)):
        return False
    stat = os.path.getmtime(filename)
    stat_date = datetime.fromtimestamp(stat)
    if stat_date.date() < datetime.now().date():
        return False
    return True

def RefreshStats():
    import scrape_teams
    import scrape_bornpowerindex
    import scrape_teamrankings
    import scrape_schedule
    import scrape_espn_odds
    import combine_stats

def collect_input():
    first = input("Enter the first team (Away team): ").strip()
    second = input("Enter the second team (Home team): ").strip()
    neutral = input("Is this a neutral field? (yes/no): ").strip().lower() == "yes"
    verbose = input("Enable verbose mode? (yes/no): ").strip().lower() == "yes"

    # Simulate the format expected by ParseResult
    mock_output = f"data: {first}\ndata: {second}\nform: {'TRUE' if verbose else 'FALSE'}|{'TRUE' if neutral else 'FALSE'}"
    return mock_output

def main(argv):
    cwd = os.getcwd()

    print("... retrieving teams spreadsheet")
    team_file = '{0}teams.xlsx'.format(settings.data_path)
    if (os.path.exists(team_file)):
        excel_df = pd.read_excel(team_file, sheet_name='Sheet1')
        team_json = json.loads(excel_df.to_json())
    else:
        print("    *** run scrape_teams and then come back ***")
        exit()

    first = ""
    second = ""
    neutral = False
    test = False
    try:
        opts, args = getopt.getopt(argv, "hf:s:nt", ["help", "first=", "second=", "neutral", "test"])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    output = None
    for o, a in opts:
        if o in ("-n", "--neutral"):
            neutral = True
        elif o in ("-t", "--test"):
            test = True
        elif o in ("-h", "--help"):
            usage()
            exit()
        elif o in ("-f", "--first"):
            first = a
        elif o in ("-s", "--second"):
            second = a
        else:
            assert False, "unhandled option"

    print("Score Matchup Tool")
    print("**************************")
    usage()
    print("**************************")

def main(argv):
    cwd = os.getcwd()

    print("... retrieving teams spreadsheet")
    team_file = '{0}teams.xlsx'.format(settings.data_path)
    if os.path.exists(team_file):
        excel_df = pd.read_excel(team_file, sheet_name='Sheet1')
        team_json = json.loads(excel_df.to_json())
    else:
        print("    *** run scrape_teams and then come back ***")
        exit()

    first = ""
    second = ""
    neutral = False
    test = False
    verbose = False
    try:
        opts, args = getopt.getopt(argv, "hf:s:nt", ["help", "first=", "second=", "neutral", "test"])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    for o, a in opts:
        if o in ("-n", "--neutral"):
            neutral = True
        elif o in ("-t", "--test"):
            test = True
        elif o in ("-h", "--help"):
            usage()
            exit()
        elif o in ("-f", "--first"):
            first = a
        elif o in ("-s", "--second"):
            second = a
        else:
            assert False, "unhandled option"

    print("Score Matchup Tool")
    print("**************************")
    usage()
    print("**************************")

    if test:
        testResult = pyBlitz.Test()
        if testResult:
            print("Test result - pass")
        else:
            print("Test result - fail")
    else:
        # Use command-line arguments if provided, otherwise prompt for input
        if not first or not second:
            result_output = collect_input()
            result = ParseResult(result_output)
            if not result:
                print("Error: Parsing input failed")
                exit()

            first, second = result["first"], result["second"]
            verbose = result["verbose"]
            neutral = result["neutral"]

        print(f"Using arguments: First = {first}, Second = {second}, Neutral = {neutral}")

        Path(settings.data_path).mkdir(parents=True, exist_ok=True)
        stat_file = "{0}json/stats.json".format(settings.data_path)
        if not CurrentStatsFile(stat_file):
            RefreshStats()

        ds = {}
        settings.exceptions = []
        ds = pyBlitz.Calculate(first, second, neutral)
        if settings.exceptions:
            print(" ")
            print("\t*** Warnings ***")
            for item in settings.exceptions:
                print(item)
            print("\t*** Warnings ***")
            print(" ")
        if not ds:
            exit()

        if neutral:
            answer = "{0} {1}% vs {2} {3}% {4}-{5}".format(ds["teama"], ds["chancea"], ds["teamb"], ds["chanceb"], ds["scorea"], ds["scoreb"])
        else:
            answer = "{0} {1}% at {2} {3}% {4}-{5}".format(ds["teama"], ds["chancea"], ds["teamb"], ds["chanceb"], ds["scorea"], ds["scoreb"])
        print(answer)
        #blitz_icon = '{0}/football.ico'.format(cwd)
        #c = NotificationClient()
        #c.register_backend(platform.Backend())
        #notification = Notification(title='pyBlitz Predictor', message=answer, icon_path=blitz_icon, duration=20)
        #c.notify_all(notification)


def usage():
    usage = """
    -h --help                 Prints this
    -f --first                First Team  (The Away Team)
    -s --second               Second Team (The Home Team)
    -n --neutral              Playing on a neutral Field
    -t --test                 runs test routine to check calculations
    """
    print(usage)

if __name__ == "__main__":
    main(sys.argv[1:])

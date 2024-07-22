#!/usr/bin/env python3

import sys, getopt
import pdb

import settings

def main(argv):
    merge_file = "{0}merge.json".format(settings.data_path)
    print ("Merge Tool")
    print ("**************************")
    print ("Master Merge file:\t{0}".format(merge_file))
    print ("\tDirectory Location: {0}".format(settings.data_path))
    print ("===")
    print ("	A good time to run is if you corrected any merge spreadsheets")
    print ("	or possibly at the beginning of each season")
    print ("===")
    print ("**************************")
    RefreshMerge()
    print ("done.")

def RefreshMerge():
    import scrape_teams
    import scrape_bornpowerindex
    import scrape_teamrankings
    import scrape_schedule
    import scrape_espn_odds
    import combine_merge
    import combine_stats

if __name__ == "__main__":
  main(sys.argv[1:])

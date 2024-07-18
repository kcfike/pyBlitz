#!/usr/bin/env python3

import json
import pdb
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import csv
from collections import OrderedDict
import os.path
from pathlib import Path
import re
import pandas as pd

import settings
import pyBlitz

print ("Merge teamrankings Tool")
print ("**************************")

print("... retrieving teams JSON file")
file = '{0}teams.xlsx'.format(settings.data_path)
if (os.path.exists(file)):
    teams_excel = "{0}teams.xlsx".format(settings.data_path)
    excel_df = pd.read_excel(teams_excel, sheet_name='Sheet1')
    teams_json = json.loads(excel_df.to_json())
else:
    print ("teams files are missing, run the scrape_teams tool to create")
    exit()

print("... retrieving teamrankings JSON file")
file = '{0}teamrankings.xlsx'.format(settings.data_path)
if (os.path.exists(file)):
    rank_excel = "{0}teamrankings.xlsx".format(settings.data_path)
    excel_df = pd.read_excel(rank_excel, sheet_name='Sheet1')
    rank_json = json.loads(excel_df.to_json())
else:
    print ("teamrankings files are missing, run the scrape_teamrankings tool to create")
    exit()

IDX=[]
teams=[]
abbrs=[]
rank_teams=[]
over=[]
index=0
for item in teams_json["displayName"]:
    team = teams_json["displayName"][item]
    abbr = teams_json["abbreviation"][item]
    found = False
    for rank_item in rank_json["abbr"]:
        rank_abbr = rank_json["abbr"][rank_item]
        rank_team = rank_json["team"][rank_item]
        if abbr == rank_abbr:
            found = True
            rank_teams.append(rank_team)

    teams.append(team)
    abbrs.append(abbr)
    over.append(" ")
    index+=1
    IDX.append(index)
    if not found:
        rank_teams.append(" ")
    
print ("... creating merge_teamrankings JSON file")
the_file = "{0}merge_teamrankings.json".format(settings.data_path)
Path(settings.data_path).mkdir(parents=True, exist_ok=True)
df=pd.DataFrame(IDX,columns=['Index'])
df['team']=teams
df['abbr']=abbrs
df['rankings team']=rank_teams
df['override']=over
  
with open(the_file, 'w') as f:
    f.write(df.to_json(orient='index'))
f.close()
    
print ("... creating merge_teamrankings spreadsheet")
the_file = "{0}merge_teamrankings.xlsx".format(settings.data_path)
writer = pd.ExcelWriter(the_file, engine="xlsxwriter")
df.to_excel(writer, sheet_name="Sheet1", index=False)
writer.close()

print ("done.")

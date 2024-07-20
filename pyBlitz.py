#!/usr/bin/env python3

import os.path
import json
from urllib.request import urlopen
from bs4 import BeautifulSoup
import html5lib
import pdb
from collections import OrderedDict
import re
from thefuzz import fuzz
from thefuzz import process
from unidecode import unidecode

import settings

def myround(x, prec=1, base=.5):
  return round(base * round(float(x)/base),prec)
  
def GetChance(n):       # static code came from betting_talk and merged here
    results={}
    s = str("{:.1f}".format(myround(n)))
    sign = "+"
    if "-" in s:
        sign = "-"
    c_s = s.replace("-", "")
    c_s = c_s.replace("+", "")
    s_n = float(c_s)
    ch={}
    ch["0.0"]=50
    ch["0.5"]=50
    ch["1.0"]=51.2
    ch["1.5"]=52.5
    ch["2.0"]=53.4
    ch["2.5"]=54.3
    ch["3.0"]=57.4
    ch["3.5"]=60.6
    ch["4.0"]=61.9
    ch["4.5"]=63.1
    ch["5.0"]=64.1
    ch["5.5"]=65.1
    ch["6.0"]=66.4
    ch["6.5"]=67.7
    ch["7.0"]=70.3
    ch["7.5"]=73
    ch["8.0"]=73.8
    ch["8.5"]=74.6
    ch["9.0"]=75.1
    ch["9.5"]=75.5
    ch["10.0"]=77.4
    ch["10.5"]=79.3
    ch["11.0"]=79.9
    ch["11.5"]=80.6
    ch["12.0"]=81.6
    ch["12.5"]=82.6
    ch["13.0"]=83
    ch["13.5"]=83.5
    ch["14.0"]=85.1
    ch["14.5"]=86.8
    ch["15.0"]=87.4
    ch["15.5"]=88.1
    ch["16.0"]=88.6
    ch["16.5"]=89.1
    ch["17.0"]=91.4
    ch["17.5"]=93.7
    ch["18.0"]=95
    ch["18.5"]=96.2
    ch["19.0"]=97.3
    ch["19.5"]=98.4
    ch["20.0"]=100
    if s_n > 20:
        pct = 100
    else:
        pct = ch[c_s]
    if sign == "+":
        pct = 100 - pct
    results["answer"] = "{:.1f}".format(pct)
    results["opposite"] = "{:.1f}".format(100 - pct)
    return results
    
def GetFuzzyBest(t, m, k):
    item=[]
    best_lists={}
    for item in m:
        best=""
        the_max=-1
        matches=m[item]
        for i in matches:
            match = matches[i]
            abbr = k[i]
            ratio = fuzz.ratio(t, match)
            if abbr == "zzzz" or abbr == " ":
                ratio = 0
            if the_max < ratio:
                the_max = ratio
                best = i, t, match, abbr, the_max
            best_lists[item] = best
    the_best={}
    for item in best_lists:
        best=""
        the_max=-1
        ratio = best_lists[item][4]
        abbr = best_lists[item][3]
        index = best_lists[item][0]
        if abbr == "zzzz" or abbr == " ":
            ratio = 0
        if the_max < ratio:
            the_max = ratio
            best = index, item, abbr, the_max
        the_best[t]=best
    return the_best[t][0], the_best[t][2], the_best[t][3]

def ErrorToJSON(e, y):
    s = str(e)
    x = '"message": "{0}", "file": "{0}"'.format(s, y)
    x = "<http>{" + x + "}</http>"
    return x

def findTeams(first, second, dict_stats, verbose = True):
    teama = {}
    teamb = {}
    for item in dict_stats.values():
        if (item["BPI"].lower().strip() == first.lower().strip()):
            teama = item
        if (item["BPI"].lower().strip() == second.lower().strip()):
            teamb = item

    if (not teama and not teamb):
        log = "findTeams() - Could not find stats for either team [{0}] or [{1}]".format(first, second)
        settings.exceptions.append(log)
        return {}, {}
    if (not teama):
        log = "findTeams() - Could not find stats for the first team [{0}]".format(first)
        settings.exceptions.append(log)
        return {}, teamb
    if (not teamb):
        log = "findTeams() - Could not find stats for the second team [{0}]".format(second)
        settings.exceptions.append(log)
        return teama, {}
    return teama, teamb

def myFloat(value):
    try:
        answer = float(value)
    except ValueError:
        return 0
    return answer

def GetFloat(item):
    idx = re.findall(r'\d{1,2}[\.]{1}\d{1,2}', str(item))
    if (len(idx) == 0):
        idx.append("-1")
    return myFloat(idx[0])

def CleanString(data):
    data =  re.sub("'","", data)
    data =  re.sub("Ã©","e", data)
    return unidecode(data)

def GetPercent(thespread, dict_percent):
    aPercent = 0
    bPercent = 0
    flip = False
    if (thespread < 0):
        thespread = abs(thespread)
        flip = True
    if (thespread >= 19.5):
        if (flip):
            bPercent = 100
            aPercent = 0
        else:
            aPercent = 100
            bPercent = 0
    else:
        for item in dict_percent.values():
            if ("+" in item['Spread']):
                spread = 20
                if (flip):
                    bPercent = 100
                    aPercent = 0
                else:
                    aPercent = 100
                    bPercent = 0
                break
            else:
                spread = myFloat(item['Spread'])
            if (spread >= thespread and thespread < (spread + .5)):
                if (flip):
                    bPercent = GetFloat(item["Favorite"])
                    aPercent = GetFloat(item["Underdog"])
                else:
                    aPercent = GetFloat(item["Favorite"])
                    bPercent = GetFloat(item["Underdog"])
                break          
    return aPercent, bPercent

def Chance(teama, teamb, homeTeam = 'Neutral', verbose = True):
    EffMgn = Spread(teama, teamb, verbose = False, homeTeam = homeTeam)
    if (verbose):
        print ("Chance(efficiency margin) {0}".format(EffMgn))
    results = GetChance(EffMgn)
    #pdb.set_trace()
    aPercent = results["answer"]
    bPercent = results["opposite"]
    #aPercent, bPercent = GetChance(EffMgn)
    if (verbose):
        if homeTeam == "Neutral":
            print ("Chance({0}) {1}%".format(teama["BPI"], aPercent),
                "vs. Chance({0}) {1}%".format(teamb["BPI"], bPercent))
        else:
            print ("Chance({0}) {1}%".format(teama["BPI"], aPercent),
                "at Chance({0}) {1}%".format(teamb["BPI"], bPercent))
    return aPercent, bPercent

def Tempo(teama, teamb, verbose = True):
    TdiffaScore = myFloat(teama['PLpG3']) * myFloat(teama['PTpP3'])
    TdiffaOScore = myFloat(teama['OPLpG3']) * myFloat(teama['OPTpP3'])
    TdiffbScore = myFloat(teamb['PLpG3']) * myFloat(teamb['PTpP3'])
    TdiffbOScore = myFloat(teamb['OPLpG3']) * myFloat(teamb['OPTpP3'])
    Tdiff = (TdiffaScore + TdiffbScore + TdiffaOScore + TdiffbOScore)/2.0
    if (verbose):
        print ("Tempo(tempo) {0}".format(Tdiff))
    return Tdiff

def Test(verbose):
    result = 0
    # Alabama, Clemson on 1/1/18 (stats from 1/7/18)
    # Actual Score: 24-6
    # venue was: Mercedes-Benz Super dome in New Orleans, Louisiana (Neutral Field "The Sugar Bowl")

    teama = {'BPI':"alabama", 'Ranking':118.5, 'PLpG3':64.7, 'PTpP3':.356, 'OPLpG3':18.7, 'OPTpP3':.246, \
        'Result1':65.1, 'Result2':17}
    teamb = {'BPI':"clemson", 'Ranking':113, 'PLpG3':79.3, 'PTpP3':.328, 'OPLpG3':12.3, 'OPTpP3':.199, \
        'Result1':34.9,'Result2':11}

    if (verbose):
        print ("Test #1 Alabama vs Clemson on 1/1/18")
        print ("        Neutral field, Testing Chance() routine")
    chancea, chanceb =  Chance(teama, teamb, homeTeam = 'Neutral', verbose = verbose)
    if (str(teama['Result1']) == chancea):
        result += 1
    if (str(teamb['Result1']) == chanceb):
        result += 1
    if (verbose and result == 2):
        print ("Test #1 - pass")
        print ("*****************************")
    if (verbose and result != 2):
        print ("Test #1 - fail")
        print ("*****************************")
    if (verbose):
        print ("Test #2 Alabama vs Clemson on 1/1/18")
        print ("        Neutral field, testing Score() routine")
    scorea, scoreb = Score(teama, teamb, verbose = verbose, homeTeam = 'Neutral')
    if (teama['Result2'] == scorea):
        result += 1
    if (teamb['Result2'] == scoreb):
        result += 1
    if (result == 4):
        return True
    return False

def Score(teama, teamb, verbose = True, homeTeam = 'Neutral'):
    tempo = Tempo(teama, teamb, False)
    if (verbose):
        print ("Score(tempo) {0}".format(tempo))
    EffMgn = Spread(teama, teamb, verbose = False, homeTeam = homeTeam)
    if (verbose):
        print ("Score(efficiency margin) {0}".format(EffMgn))
    aScore = round((tempo/2.0) - (EffMgn / 2.0))
    bScore = round((tempo/2.0) + (EffMgn /2.0))
    if (aScore < 0):
        aScore = 0
    if (bScore < 0):
        bScore = 0
    if (verbose):
        print ("Score({0}) {1} at Score({2}) {3}".format(teama["BPI"], aScore, teamb["BPI"], bScore))
    return aScore, bScore

def Spread(teama, teamb, verbose = True, homeTeam = 'Neutral'):
    #EMdiff = (myFloat(teama['Ranking']) - myFloat(teamb['Ranking']))
    EMdiff = (myFloat(teamb['Ranking']) - myFloat(teama['Ranking']))
    #pdb.set_trace()
    EffMgn = 0
    if (homeTeam.lower().strip() == teama["BPI"].lower().strip()):
        EffMgn = EMdiff + settings.homeAdvantage
    elif (homeTeam.lower().strip() == teamb["BPI"].lower().strip()):
        EffMgn = EMdiff - settings.homeAdvantage
    else:
        EffMgn = EMdiff
    if (verbose):
        print ("Spread(efficiency margin) {0}".format(EffMgn))
    return EffMgn

def Calculate(first, second, neutral, verbose):
    if (verbose):
        if (neutral):
            info = "{0} verses {1} at a neutral location".format(first, second)
            print (info)
        else:
            info = "Visiting team: {0} verses Home team: {1}".format(first, second)
            print (info)
    file = "{0}json/stats.json".format(settings.data_path)
    with open(file) as stats_file:
        dict_stats = json.load(stats_file, object_pairs_hook=OrderedDict)
    file = "{0}json/odds.json".format(settings.data_path)
    if (not os.path.exists(file)):
        info = "Calculate() - odds file is missing, run the scrape_espn_odds tool to create"
        settings.exceptions.append(info)
        print (info)
        exit()
    with open(file) as percent_file:
        dict_percent = json.load(percent_file, object_pairs_hook=OrderedDict)

    teama, teamb = findTeams(first, second, dict_stats, verbose = verbose)
    if (not teama and not teamb):
        info = "Calculate() - [{0}] and [{1}] missing from stats, can't predict".format(first, second)
        settings.exceptions.append(info)
        print (info)
        return {}
    classa = "?"
    if (teama):
        classa = teama["Class"].lower().strip()
    classb = "?"
    if (teamb):
        classb = teamb["Class"].lower().strip()
    if (classa == "?" and classb == "?"):
        settings.exceptions.append("Calculate() - [{0}] team playing [{1}] team,  Cannot predict, Fix merge spreadsheet(s)".format(classa, classb))
        dict_score = {'teama':first, 'scorea':"0", 'chancea':"0" ,'teamb':second, 'scoreb':"0", 'chanceb':"0", 'spread': 0, 'tempo':"0"}
        print ("Warning: {0} playing {1}, Cannot Predict, Fix merge spreadsheet(s)".format(first, second))
        return dict_score
    else:
        if (classa == "division 1  fbs" and classb != "division 1  fbs"):
            settings.exceptions.append("Calculate() - [{0}] team playing [{1}] team, {2} wins".format(classa, classb, first))
            dict_score = {'teama':first, 'scorea':"0", 'chancea':"100" ,'teamb':second, 'scoreb':"0", 'chanceb':"0", 'spread': 0, 'tempo':"0"}
            return dict_score
        if (classa != "division 1  fbs" and classb == "division 1  fbs"):
            settings.exceptions.append("Calculate() - [{0}] team playing [{1}] team, {2} wins".format(classa, classb, second))
            dict_score = {'teama':first, 'scorea':"0", 'chancea':"0" ,'teamb':second, 'scoreb':"0", 'chanceb':"100", 'spread': 0, 'tempo':"0"}
            return dict_score
    if (not neutral):
        chancea, chanceb =  Chance(teama, teamb, homeTeam = teamb["BPI"], verbose = verbose)
        scorea, scoreb = Score(teama, teamb, verbose = verbose, homeTeam = teamb["BPI"])
        spread = Spread(teama, teamb, verbose = verbose, homeTeam = teamb["BPI"])
    else:
        chancea, chanceb =  Chance(teama, teamb, dict_percent, verbose = verbose)
        scorea, scoreb = Score(teama, teamb, verbose = verbose)
        spread = Spread(teama, teamb, verbose = verbose)

    tempo = Tempo(teama, teamb, verbose = verbose)

    dict_score = {'teama':first, 'scorea':"{0}".format(scorea), 'chancea':"{0}".format(chancea) ,'teamb':second, 'scoreb':"{0}".format(scoreb), 'chanceb':"{0}"
        .format(chanceb), 'spread': round(spread, 3), 'tempo':"{0}".format(int(round(tempo))) }
    if (verbose):
        print ("Calculate(dict_score) {0}".format(dict_score))
    return dict_score

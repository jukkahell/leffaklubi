from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree
from bs4 import BeautifulSoup
import json
from imdb import *
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from localizer import *
from pprint import pprint
from pick import pick

chooseEnvTitle = 'Valitse ympäristö (vscodessa j näppäin): '
envOptions = ['Testi', 'Tuotanto']
option, index = pick(envOptions, chooseEnvTitle)

# Prod
prodTeamsWebhook = "REPLACE_WITH LEFFAKLUBI TEAMS WEBHOOK"
# Test
testTeamsWebhook = "REPLACE_WITH LEFFAKLUBI TEST CHANNEL TEAMS WEBHOOK"

teamsWebhook = prodTeamsWebhook if option == 'Tuotanto' else testTeamsWebhook

def postToTeams(json):
    jsonbytes = json.encode('utf-8')
    try:
        request = Request(teamsWebhook, jsonbytes, headers={'Content-Type': 'application/json', 'Content-Length': len(jsonbytes)})
        with urlopen(request) as f:
            res = f.read()
            pprint(res.decode())
    except Exception as e:
        pprint(e)

tmpTeamsPostFilename = "tmpTeamsPost.json"
savedTeamsJsonFile = Path(tmpTeamsPostFilename)
if savedTeamsJsonFile.is_file():
    savedTeamsJson = json.load(open(tmpTeamsPostFilename, "r"))
    postToTeams(json.dumps(savedTeamsJson))
    savedTeamsJsonFile.unlink()
    exit(0)

#Run script
#give input in dd.MM.yyyy format
dateInput = input('Anna leffapäivä (dd.MM.yyyy): ')
voteEndInput = input('Anna äänestyksen päättymispäivä (dd.MM.yyyy): ')

voteEndDate = datetime.strptime(voteEndInput, '%d.%m.%Y')
voteEndWeekday = weekdays[voteEndDate.weekday()].upper()

showDate = datetime.strptime(dateInput, '%d.%m.%Y')
showMonth = months[showDate.month]
showWeekday = weekdays[showDate.weekday()].upper()

signUpDelta = abs(voteEndDate - showDate)
signUpEnd = ""
if signUpDelta.days <= 1:
    signUpEnd = "samana päivänä"
else:
    signUpEndDate = voteEndDate + timedelta(days=signUpDelta.days - 1)
    signUpEndWeekday = weekdays[signUpEndDate.weekday()]
    signUpEnd = f'{signUpEndWeekday.upper()}NA {signUpEndDate.day}.{signUpEndDate.month}. klo 12:00'

url = 'https://www.finnkino.fi/xml/Schedule/'
queryParams = {
    'blockID': '4571',
    'area': '1035',
    'dt': dateInput,
    'orderBy': 'showTime',
    'order': 'asc'
}

request = Request(url, urlencode(queryParams).encode(),headers={'User-Agent': 'Mozilla/5.0'})
finnkinoXml = urlopen(request).read().decode()
movieSchedule = ET.fromstring(finnkinoXml)

emptyBlock = {
    "type": "TextBlock",
    "text": " ",
    "size": "Small"
}

cardTitle = {
    "type": "Container",
    "spacing": "None",
    "padding": "Default",
    "items": [
        {
            "type": "TextBlock",
            "text": f'{showMonth}n leffaäänestys!',
            "size": "Large",
            "weight": "Bolder"
        }
    ],
    "separator": True
}

cardIntro = {
    "type": "Container",
    "items": [
        emptyBlock,
        {
            "type": "TextBlock",
            "text": f'Leffapäivä {showWeekday} {showDate.day}.{showDate.month}. Näytöksistä valitaan kaksi suosituinta. Voit äänestää haluamaasi elokuvaa kommentoimalla tähän ketjuun jonkin alla olevista vaihtoehdoista. Äänestys päättyy {voteEndWeekday}NA {voteEndDate.day}.{voteEndDate.month}. klo 12:00. Ilmoittautuminen alkaa heti äänestyksen päätyttyä ja päättyy {signUpEnd}. Kaikki näytösajat Tampereen Plevnassa. Edelliset voittajat poistettu listasta.',
            "wrap": True,
            "spacing": "None",
            "size": "Small"
        },
        emptyBlock
    ],
    "separator": True,
    "padding": "Default",
    "spacing": "Small",
    "bleed": True
}

cardBody = [
    cardTitle,
    cardIntro
]

previousSelectionsJson = open("previous-selections.json", "r")
previousMovieSelections = json.load(previousSelectionsJson)

for show in movieSchedule.iter("Show"):
    movie = {}
    movie['title'] = show.find("Title").text
    startTime = show.find("dttmShowStart").text
    startDate = datetime.strptime(startTime, "%Y-%m-%dT%H:%M:%S")

    if startDate.hour < 16 or (startDate.hour == 21 and startDate.minute > 0):
        continue
    if movie['title'] in previousMovieSelections:
        continue

    startMinute = f'0{startDate.minute}' if startDate.minute < 10 else startDate.minute
    movie['time'] = f'{startDate.hour}:{startMinute}'
    lengthInMinutes = show.find("LengthInMinutes").text
    movie['length'] = lengthInMinutes
    movie['place'] = show.find("TheatreAndAuditorium").text
    movie['url'] = show.find("EventURL").text

    imdbUrl = get_imdb_url(movie['title'])
    if imdbUrl is not None:
        movie['imdbUrl'] = imdbUrl
        movie['score'] = get_imdb_score(imdbUrl)

    detailItems = [
        {
            "type": "TextBlock",
            "text": f'[{movie["title"]}]({movie["url"]}), {movie["time"]}, {movie["place"]}',
        },
        {
            "type": "TextBlock",
            "text": f'Kesto: {movie["length"]}min',
            "spacing": "None",
            "size": "Small"
        }
    ]

    if imdbUrl is not None:
        imdbDetails = {
            "type": "TextBlock",
            "text": f'[IMDb]({movie["imdbUrl"]}) ⭐️ {movie["score"]}',
            "wrap": True,
            "size": "Small",
            "spacing": "None"
        }
        detailItems.append(imdbDetails)

    movieDetails = {
        "type": "Container",
        "padding": "Default",
        "spacing": "Small",
        "items": detailItems,
        "separator": True
    }

    cardBody.append(movieDetails)

teamsCard = {
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "type": "AdaptiveCard",
    "version": "1.0",
    "body": cardBody,
    "padding": "None",
    "@type": "AdaptiveCard",
    "@context": "http://schema.org/extensions"
}

postMessage = {
    "type": "message",
    "attachments": [
        {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "contentUrl": None,
            "content": teamsCard
        }
    ]
}
postJson = json.dumps(postMessage)
print(postJson)
postToTeams(postJson)

if (teamsWebhook == testTeamsWebhook):
    saveTempFile = input("Tallenna json tuotantopostausta varten (y/n): ")
    if saveTempFile == "y":
        with open(tmpTeamsPostFilename, 'w') as file:
            file.write(postJson)
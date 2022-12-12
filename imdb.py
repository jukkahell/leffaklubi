from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree
from bs4 import BeautifulSoup
import datetime

#Run script
def get_imdb_url(title):
    movieTitle = urlencode({'q':title})
    req = Request(
        url='https://www.imdb.com/find?' + movieTitle, 
        data=None, 
        headers={
            'User-Agent': 'Chrome/35.0.1916.47'
        }
    )
    html = urlopen(req).read().decode()
    soup = BeautifulSoup(html, "html.parser")

    # find all movies in soup
    titleInfos = soup.find_all("a", {"class": "ipc-metadata-list-summary-item__t"})
    if len(titleInfos) > 0:
        titleInfo = titleInfos[0]
        movieUrl = titleInfo['href']
        return 'https://www.imdb.com' + movieUrl

def get_imdb_score(imdbUrl):
    req = Request(
        url=imdbUrl, 
        data=None, 
        headers={
            'User-Agent': 'Chrome/35.0.1916.47'
        }
    )
    movieHtml = urlopen(req).read().decode()
    detailsSoup = BeautifulSoup(movieHtml, "html.parser")
    ratings = detailsSoup.select("div[data-testid^=hero-rating-bar__aggregate-rating__score]")
    if len(ratings) > 0:
        voteCount = ratings[0].fetchNextSiblings()[1].text if len(ratings[0].fetchNextSiblings()) > 1 else None
        rating = ratings[0].contents[0].text
        if (voteCount is not None):
            rating += " (" + voteCount + " ääntä)"
        return rating
    else:
        return '-'

# Just for testing
if __name__ == '__main__':
    url = get_imdb_url('Fantastic Beasts: The Secrets of Dumbledore')
    if (url is not None):
        print(get_imdb_score(url))
    else:
        print('-')
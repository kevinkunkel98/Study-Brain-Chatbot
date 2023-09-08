# see https://github.com/pkalkunte18/medium-text-scraper/blob/master/mediumTextScraper.py

from bs4 import BeautifulSoup
from urllib.request import urlopen, Request
import os
from dotenv import load_dotenv
import re
from urllib.parse import urlparse

tags = ["gpt-3"] #tags to scrape
years = ['2020'] #years to scrape during
months = ['06', '07'] #months to scrape during (every available day within the month will be scraped)
load_dotenv()
scrapeFolderName = os.getenv('SCRAPE_FOLDER_NAME')

#don't touch unless you need to
hdr = {'User-Agent': 'Mozilla/5.0'}

def scrapeLinksToArticles(tag, years, months):
    startLink = "https://medium.com/tag/"+tag+"/archive/"
    articleLinks = []
    for y in years:
        yearLink = startLink + y
        for m in months:
            monLink = yearLink + "/" + m
            #open the month link and scrape all valid days (days w/ link) into drive
            req = Request(monLink,headers=hdr)
            page = urlopen(req)
            monSoup = BeautifulSoup(page, 'html.parser')
            try: #if there are days
                allDays = list(monSoup.find("div", {"class": "col u-inlineBlock u-width265 u-verticalAlignTop u-lineHeight35 u-paddingRight0"}).find_all("div", {"class":"timebucket"}))
                for a in allDays:
                    try: #try to see if that day has a link
                        dayLink = a.find("a")['href']
                        req = Request(dayLink,headers=hdr)
                        page = urlopen(req)
                        daySoup = BeautifulSoup(page)
                        links = list(daySoup.find_all("div", {"class": "postArticle-readMore"}))
                        for l in links:
                            articleLinks.append(l.find("a")['href'])
                    except: pass
            except: #take the month's articles
                links = list(monSoup.find_all("div", {"class": "postArticle-readMore"}))
                for l in links:
                    articleLinks.append(l.find("a")['href'])
                #print("issueHere")
            # as medium.com changed layout of archive page new way to scrape is needed
            try:
               links = list(monSoup.find_all('article')) 
               for link in links:
                   linktitel = re.sub(r'[^a-zA-Z0-9\s-]', '',  link.find_all('h2')[0].text.lower()).replace(' ', '-')
                   #print(linktitel)
                   for anchors in link.find_all('a'):
                       anchorHref = anchors['href']
                       #print(anchorHref)
                       match = re.search(linktitel, anchorHref)            
                       if match:
                        matchAsci = re.search(r'[^\x00-\x7f]', anchorHref)
                        if not matchAsci:
                            articleLinks.append('https://medium.com' + anchorHref)    
            except:
                print('nothing to scrape')
    return list(set(articleLinks))

#INPUT - link to a medium article
#OUTPUT - string with all the article text
def scrapeArticle(link):
    bodyText = ""
    req = Request(link, headers=hdr)
    page = urlopen(req)
    soup = BeautifulSoup(page, 'html.parser')    
    textBoxes = list(soup.find("div", {"class": "l c"}).find_all("p"))
    for t in textBoxes:
        bodyText = bodyText + t.get_text()
    return bodyText

#get text of articles, default: take top 5 entries
#scrapedArticles should have minLen of at least 1000
def getArticleText(articleLinks, top=5, minLen=1000):
    isExisting = os.path.exists(scrapeFolderName)
    if not isExisting: 
        os.makedirs(scrapeFolderName)
    count = 0
    articleArray = []
    while count < top:
        for art in articleLinks:
            parsed_url = urlparse(art)
            titel = parsed_url.path.split('/')[-1]
            outPutText = open(scrapeFolderName + "scrapeTxt{}_".format(count) + titel + ".txt", "a+", encoding='utf8')
            # print(count)
            scrapedArticle = (str(scrapeArticle(art)))
            if "Member-only" not in scrapedArticle:
                result = re.sub(r'[^\x00-\x7f]',r'', scrapedArticle) #removes non ascii chars
                articleArray.append(result)
                outPutText.write(result)
                count += 1   
            if count == top:
                break 
    return articleArray

if __name__ == "__main__":
    articleLinks = []
    for tag in tags: 
       articleLinks.extend(scrapeLinksToArticles(tag, years, months))
    articleLinks = set(articleLinks) #get rid of any duplicates

    articles = getArticleText(articleLinks)
    # print(articles)

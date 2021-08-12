import requests
import bs4
import re
from bs4 import BeautifulSoup
from collections import Counter
from nltk.corpus import stopwords

def scrape_article(url):
    response = requests.get(url = url,)
    soup = BeautifulSoup(response.text, 'html.parser')
    body = soup.find('div', attrs = {'id':'mw-content-text'})
    text = {}
    start = None
    section = None
    
    #being scraping sections after table of contents
    while True:
        #locate first seection after table of contents
        next_sib = body.find('div', attrs = {'id': 'toc'}).find_next_sibling()
        tag = next_sib.contents[0].attrs['class'][0]
        if tag != 'mw-headline':
            #continue searching if section not found
            continue
        else:
            #first section tag found, create text dictionary
            section = next_sib.contents[0].attrs['id']
            text[section] = {'text': [], 'links': []}
            start = next_sib
            break

    #scrape all sections until we reach the 'see also' section
    while section != 'See_also':
        start = start.find_next_sibling()
        #scrape the next sibling of the section header
        while True:
            contents = start.contents
            if (len(contents) == 1) and (start.attrs == {}):
                #text is in a section with no attributes
                text[section]['text'].append(start.text.strip('\n'))
                start = start.find_next_sibling()
            elif (len(contents) == 1) and (start.attrs != {}):
                #no text located
                start = start.find_next_sibling()
            else:
                #text in multiple sections
                #extract hyperlinks from text
                links = start.find_all('a')
                for link in links: 
                    if 'cite' not in link.attrs['href']:
                        text[section]['links'].append('https://en.wikipedia.org/' + link.attrs['href'])  
                #new section found
                if start.name == 'h2':
                    section = contents[0].attrs['id']
                    text[section] = {'text': [], 'links': []}
                    break
                #extract text
                text[section]['text'].append(start.text.strip('\n'))
                start = start.find_next_sibling()
    
    #helper function to clean text
    def clean_text(text):
        text = text.lower()
        #remove citation tag
        text = re.sub(r'\[\w+\]', '', text)
        #remove delimiters
        text = re.sub('\\n', '', text)
        #remove single non-alphanumerics
        text = re.sub(r'\W', ' ', text)
        #remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        return text
    
    text.pop('See_also')
    stop_words = set(nltk.corpus.stopwords.words('english'))
    
    for key in text.keys():
        #join scraped text into single string
        full_text = " ".join(text[key]['text'])
        #preprocess scraped teext
        cleaned = clean_text(full_text)
        words = cleaned.split(' ')
        #remove stopwords
        filtered = [word for word in words if not word.lower() in stop_words]
        #determine the 10 most common words in each section
        counter = Counter(filtered)
        #update dictionary with most common words
        text[key]['text'] = counter.most_common()[:10]
        
    return text

scrape_article("https://en.wikipedia.org/wiki/Web_scraping")
import requests
from bs4 import BeautifulSoup
import re
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'de-DE,de;q=0.9',
}

def detect_source(url):
    if 'mobile.de' in url: return 'mobile'
    if 'autoscout24' in url: return 'autoscout'
    if 'kleinanzeigen' in url: return 'kleinanzeigen'
    return 'unknown'

def scrape_mobile(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200: return None
        soup = BeautifulSoup(r.text, 'html.parser')
        data = {}
        h1 = soup.find('h1')
        if h1: data['title'] = h1.get_text(strip=True)
        for el in soup.find_all(True):
            t = el.get_text(strip=True)
            if re.search(r'\d{1,3}\.\d{3}\s*km', t) and 'mileage' not in data: data['mileage'] = t
            if re.search(r'\d{1,3}\.\d{3}\s*EUR|€', t) and 'price' not in data: data['price'] = t
            if re.search(r'EZ\s*\d{2}/20\d{2}|Erstzulassung', t) and 'year' not in data: data['year'] = t
        return data if data else None
    except: return None

def scrape_autoscout(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200: return None
        soup = BeautifulSoup(r.text, 'html.parser')
        data = {}
        for s in soup.find_all('script', type='application/ld+json'):
            try:
                obj = json.loads(s.string or '')
                if obj.get('@type') == 'Car':
                    data['make'] = obj.get('brand', {}).get('name', '')
                    data['model'] = obj.get('model', '')
                    data['year'] = str(obj.get('modelDate', ''))
                    km = obj.get('mileageFromOdometer', {}).get('value', '')
                    if km: data['mileage'] = str(km) + ' km'
                    data['title'] = data.get('make','') + ' ' + data.get('model','')
            except: pass
        h1 = soup.find('h1')
        if h1 and 'title' not in data: data['title'] = h1.get_text(strip=True)
        return data if data else None
    except: return None

def scrape_kleinanzeigen(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200: return None
        soup = BeautifulSoup(r.text, 'html.parser')
        data = {}
        title = soup.find('h1', id='viewad-title') or soup.find('h1')
        if title: data['title'] = title.get_text(strip=True)
        price = soup.find(id='viewad-price')
        if price: data['price'] = price.get_text(strip=True)
        for li in soup.find_all('li', class_=re.compile('addetail|detail')):
            t = li.get_text(strip=True)
            if 'km' in t.lower(): data['mileage'] = t
            if re.search(r'20[0-2][0-9]|199[0-9]', t): data['year'] = t
        return data if data else None
    except: return None

def scrape_url(url):
    source = detect_source(url)
    scrapers = {'mobile': scrape_mobile, 'autoscout': scrape_autoscout, 'kleinanzeigen': scrape_kleinanzeigen}
    fn = scrapers.get(source)
    if fn:
        return fn(url), source
    return None, source

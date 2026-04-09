import requests
from bs4 import BeautifulSoup
import re
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'de-DE,de;q=0.9',
}

def detect_source(url):
    if 'mobile.de' in url: return 'mobile'
    if 'autoscout24' in url: return 'autoscout'
    if 'kleinanzeigen' in url or 'ebay-kleinanzeigen' in url: return 'kleinanzeigen'
    return 'unknown'

def try_scrape(url):
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        if 'mobile.de' in url:
            session.get('https://www.mobile.de', timeout=6)
        r = session.get(url, timeout=12)
        if r.status_code != 200: return None
        soup = BeautifulSoup(r.text, 'html.parser')
        data = {}
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                obj = json.loads(script.string or '')
                if isinstance(obj, dict) and obj.get('@type') in ('Car', 'Vehicle', 'Product'):
                    data['title'] = obj.get('name', '')
                    brand = obj.get('brand', {})
                    data['make'] = brand.get('name', '') if isinstance(brand, dict) else str(brand)
                    data['model'] = obj.get('model', '')
                    data['year'] = str(obj.get('modelDate', ''))
                    km = obj.get('mileageFromOdometer', {})
                    if isinstance(km, dict): data['mileage'] = str(km.get('value', '')) + ' km'
                    offers = obj.get('offers', {})
                    if isinstance(offers, dict): data['price'] = str(offers.get('price', '')) + ' EUR'
                    data['fuel'] = obj.get('fuelType', '')
                    if data.get('title'): return data
            except: pass
        h1 = soup.find('h1')
        if h1: data['title'] = h1.get_text(strip=True)
        text = soup.get_text()
        if not data.get('price'):
            m = re.search(r'\d{1,3}\.\d{3}\s*[EUR€]', text)
            if m: data['price'] = m.group(0)
        if not data.get('mileage'):
            m = re.search(r'\d{1,3}\.\d{3}\s*km', text, re.I)
            if m: data['mileage'] = m.group(0)
        return data if (data.get('title') or data.get('make')) else None
    except Exception as e:
        print(f'Scrape error: {e}')
        return None

def scrape_url(url):
    source = detect_source(url)
    data = try_scrape(url)
    return data or {'url': url, 'source': source}, source

import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urlparse, parse_qs

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0',
}

def detect_source(url):
    if 'mobile.de' in url: return 'mobile'
    if 'autoscout24' in url: return 'autoscout'
    if 'kleinanzeigen' in url: return 'kleinanzeigen'
    return 'unknown'

def extract_from_url_params(url):
    """Extract vehicle hints from URL query parameters (works even when scraping is blocked)."""
    data = {}
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        # mobile.de URL params: fr=2010: (from year), ml=:150000 (max km), p=:7000 (max price)
        if 'fr' in params:
            year_range = params['fr'][0]
            year = year_range.replace(':', '').strip()
            if year and year.isdigit():
                data['year_hint'] = year
        if 'ml' in params:
            ml = params['ml'][0].replace(':', '').strip()
            if ml:
                data['mileage_hint'] = ml + ' km'
        if 'p' in params:
            price = params['p'][0].replace(':', '').strip()
            if price:
                data['price_hint'] = price + ' EUR'
        # Extract vehicle ID
        if 'id' in params:
            data['listing_id'] = params['id'][0]
    except:
        pass
    return data

def scrape_mobile(url):
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        # First visit homepage to get cookies
        session.get('https://www.mobile.de', timeout=8)
        r = session.get(url, timeout=12)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, 'html.parser')
        data = {}

        # Try JSON-LD structured data first
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                obj = json.loads(script.string or '')
                if isinstance(obj, dict) and obj.get('@type') in ('Car', 'Vehicle', 'Product'):
                    data['title'] = obj.get('name', '')
                    data['make'] = obj.get('brand', {}).get('name', '') if isinstance(obj.get('brand'), dict) else obj.get('brand', '')
                    data['model'] = obj.get('model', '')
                    data['year'] = str(obj.get('modelDate', obj.get('vehicleModelDate', '')))
                    km = obj.get('mileageFromOdometer', {})
                    if isinstance(km, dict):
                        data['mileage'] = str(km.get('value', '')) + ' km'
                    price = obj.get('offers', {})
                    if isinstance(price, dict):
                        data['price'] = str(price.get('price', '')) + ' ' + str(price.get('priceCurrency', 'EUR'))
            except:
                pass
        
        if data.get('title'):
            return data

        # Fallback: parse HTML
        h1 = soup.find('h1')
        if h1:
            data['title'] = h1.get_text(strip=True)
        
        # Look for price patterns
        price_patterns = [r'\d{1,3}\.\d{3}\s*€', r'\d{1,3}\.\d{3}\s*EUR', r'€\s*\d{1,3}\.\d{3}']
        text = soup.get_text()
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                data['price'] = match.group(0)
                break
        
        # Look for km
        km_match = re.search(r'\d{1,3}\.\d{3}\s*km', text, re.IGNORECASE)
        if km_match:
            data['mileage'] = km_match.group(0)

        return data if data else None
    except Exception as e:
        print(f'mobile.de scrape error: {e}')
        return None

def scrape_autoscout(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, 'html.parser')
        data = {}
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                obj = json.loads(script.string or '')
                if obj.get('@type') == 'Car':
                    data['make'] = obj.get('brand', {}).get('name', '')
                    data['model'] = obj.get('model', '')
                    data['year'] = str(obj.get('modelDate', ''))
                    km = obj.get('mileageFromOdometer', {}).get('value', '')
                    if km: data['mileage'] = str(km) + ' km'
                    data['title'] = data.get('make', '') + ' ' + data.get('model', '')
            except:
                pass
        h1 = soup.find('h1')
        if h1 and not data.get('title'):
            data['title'] = h1.get_text(strip=True)
        price = soup.find(class_=re.compile('price|Price'))
        if price:
            data['price'] = price.get_text(strip=True)
        return data if data else None
    except Exception as e:
        print(f'autoscout scrape error: {e}')
        return None

def scrape_kleinanzeigen(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return None
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
    except Exception as e:
        print(f'kleinanzeigen scrape error: {e}')
        return None

def scrape_url(url):
    source = detect_source(url)
    scrapers = {
        'mobile': scrape_mobile,
        'autoscout': scrape_autoscout,
        'kleinanzeigen': scrape_kleinanzeigen
    }
    fn = scrapers.get(source)
    if fn:
        data = fn(url)
        if data:
            return data, source
    
    # Fallback: extract hints from URL params
    url_hints = extract_from_url_params(url)
    if url_hints:
        return {'title': f'Fahrzeug von {source}', **url_hints, '_scraped': False}, source
    
    return None, source

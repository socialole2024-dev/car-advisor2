import re

SUPPORTED_DOMAINS = [
    'mobile.de',
    'autoscout24.de',
    'autoscout24.com',
    'kleinanzeigen.de',
    'ebay-kleinanzeigen.de',
]

def extract_url(raw_input):
    """Extract a clean URL from raw text input (e.g. WhatsApp forwards with prefix text)."""
    raw = raw_input.strip()
    
    # Already a clean URL?
    if raw.startswith('http://') or raw.startswith('https://'):
        return raw.split()[0]  # Take first word in case of trailing text
    
    # Find any URL in the text
    urls = re.findall(r'https?://[^s'"<>]+', raw)
    if urls:
        return urls[0]
    
    # No http prefix but contains known domain?
    for domain in SUPPORTED_DOMAINS:
        if domain in raw:
            match = re.search(r'(?:www.)?' + re.escape(domain) + r'[^s'"<>]*', raw)
            if match:
                return 'https://' + match.group(0)
    
    return raw  # Return as-is, let scraper handle error

def is_supported_url(url):
    return any(domain in url for domain in SUPPORTED_DOMAINS)

import asyncio
import json
import re
from playwright.async_api import async_playwright

async def scrape_with_browser(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox','--disable-setuid-sandbox','--disable-dev-shm-usage','--no-zygote','--disable-gpu']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800},
            locale='de-DE'
        )
        page = await context.new_page()
        data = {}
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=20000)
            await page.wait_for_timeout(2500)
            json_ld = await page.evaluate("""() => {
                const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                const results = [];
                scripts.forEach(s => { try { results.push(JSON.parse(s.textContent)); } catch(e) {} });
                return results;
            }""")
            for obj in json_ld:
                if isinstance(obj, dict) and obj.get('@type') in ('Car', 'Vehicle', 'Product'):
                    data['title'] = obj.get('name', '')
                    brand = obj.get('brand', {})
                    data['make'] = brand.get('name', '') if isinstance(brand, dict) else str(brand)
                    data['model'] = obj.get('model', '')
                    data['year'] = str(obj.get('modelDate', obj.get('vehicleModelDate', '')))
                    km = obj.get('mileageFromOdometer', {})
                    if isinstance(km, dict): data['mileage'] = str(km.get('value', '')) + ' km'
                    offers = obj.get('offers', {})
                    if isinstance(offers, dict): data['price'] = str(offers.get('price', '')) + ' ' + str(offers.get('priceCurrency', 'EUR'))
                    data['fuel'] = obj.get('fuelType', '')
                    if data.get('title') or data.get('make'): break
            if not data.get('title'):
                title = await page.title()
                if title: data['title'] = title.split('|')[0].split('-')[0].strip()
                text = await page.evaluate("() => document.body.innerText")
                pm = re.search(r'(\d{1,3}\.\d{3}|\d{3,6})\s*[EUR€]', text)
                if pm: data['price'] = pm.group(0)
                km = re.search(r'(\d{1,3}\.\d{3}|\d{3,6})\s*km', text, re.I)
                if km: data['mileage'] = km.group(0)
                ym = re.search(r'(EZ|Erstzulassung)[:\\s]*(\\d{2}/20\\d{2}|20[0-2]\\d)', text)
                if ym: data['year'] = ym.group(2)
        except Exception as e:
            print(f'Playwright error: {e}')
        finally:
            await browser.close()
        return data if (data.get('title') or data.get('make') or data.get('price')) else None

def scrape_with_playwright(url):
    try:
        return asyncio.run(scrape_with_browser(url))
    except Exception as e:
        print(f'Playwright wrapper error: {e}')
        return None

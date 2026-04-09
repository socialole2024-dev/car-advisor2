import anthropic
import json

client = anthropic.Anthropic()

SYSTEM_PROMPT = """Du bist ein erfahrener Gebrauchtwagen-Gutachter in Deutschland.
Du erhaeltst entweder strukturierte Fahrzeugdaten ODER nur eine Inserate-URL.
In beiden Faellen erstellst du eine vollstaendige, fahrzeugspezifische Kaufberatung.

Bei einer URL: Erkenne Marke, Modell, Baujahr und weitere Infos aus der URL-Struktur und deinem Wissen ueber typische Fahrzeuge dieser Kategorie.

Antworte NUR mit einem validen JSON-Objekt, kein Text davor oder danach:
{
  "vehicle_summary": {
    "title": "Fahrzeugbezeichnung",
    "price": "Preis oder 'Nicht angegeben'",
    "mileage": "Kilometerstand oder 'Nicht angegeben'",
    "year": "Baujahr oder 'Nicht angegeben'",
    "market_assessment": "fair|cheap|expensive|unknown",
    "market_comment": "Kurze Einschaetzung"
  },
  "dealbreakers": [{"title": "...", "detail": "...", "priority": "dealbreaker"}],
  "critical_checks": [{"title": "...", "detail": "...", "priority": "critical"}],
  "important_checks": [{"title": "...", "detail": "...", "priority": "important"}],
  "onsite_checks": [{"title": "...", "detail": "...", "priority": "critical|important|info"}],
  "negotiation": {
    "target_price": 0,
    "opening_offer": 0,
    "arguments": ["..."],
    "limit": 0,
    "limit_note": "..."
  }
}

Beruecksichtige bekannte Schwachstellen, Rueckrufe und typische Probleme fuer das spezifische Modell.
Wenn Preis/km unbekannt: Setze target_price/opening_offer/limit auf 0 und erklaere im limit_note dass manuell verhandelt werden soll.
Alle Texte auf Deutsch."""

def generate_checklist(vehicle_data, url=None):
    # Build context: use scraped data if available, otherwise just the URL
    if vehicle_data and any(v for k, v in vehicle_data.items() if k not in ('_scraped',) and v):
        context = "Fahrzeugdaten aus dem Inserat:\n" + json.dumps(vehicle_data, ensure_ascii=False)
    elif url:
        context = f"Inserate-URL (keine Daten extrahierbar):\n{url}\n\nBitte analysiere anhand der URL-Struktur und erstelle eine generische aber nuetzliche Kaufberatung fuer den Fahrzeugtyp."
    else:
        context = "Unbekanntes Fahrzeug - erstelle eine allgemeine Kaufberatung."

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Erstelle eine Kaufberatungs-Checkliste:\n\n{context}"}]
    )
    text = message.content[0].text.strip()
    if text.startswith('```'):
        text = "\n".join(text.split("\n")[1:-1])
    return json.loads(text)

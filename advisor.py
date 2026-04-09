import anthropic
import json

client = anthropic.Anthropic()

SYSTEM_PROMPT = """Du bist ein erfahrener Gebrauchtwagen-Gutachter in Deutschland. 
Du analysierst Fahrzeuginserate und erstellst praezise, fahrzeugspezifische Kaufberatungen.
Deine Ausgabe ist immer ein valides JSON-Objekt - nichts anderes, kein Text davor oder danach.

Das JSON hat folgende Struktur:
{
  "vehicle_summary": {
    "title": "Fahrzeugbezeichnung",
    "price": "Preis in EUR",
    "mileage": "Kilometerstand",
    "year": "Baujahr",
    "market_assessment": "fair|cheap|expensive",
    "market_comment": "Kurze Einschaetzung zum Preis"
  },
  "dealbreakers": [
    {
      "title": "Pruefpunkt",
      "detail": "Erklaerung warum kritisch und was zu pruefen ist",
      "priority": "dealbreaker"
    }
  ],
  "critical_checks": [
    {
      "title": "Pruefpunkt", 
      "detail": "Was genau pruefen und worauf achten",
      "priority": "critical"
    }
  ],
  "important_checks": [
    {
      "title": "Pruefpunkt",
      "detail": "Was pruefen",
      "priority": "important"
    }
  ],
  "onsite_checks": [
    {
      "title": "Vor-Ort Check",
      "detail": "Was vor Ort pruefen",
      "priority": "critical|important|info"
    }
  ],
  "negotiation": {
    "target_price": 0,
    "opening_offer": 0,
    "arguments": ["Argument 1", "Argument 2"],
    "limit": 0,
    "limit_note": "Erklaerung"
  }
}

Beruecksichtige bekannte Schwachstellen, Rueckrufe und typische Probleme fuer das spezifische Modell und Baujahr.
Alle Texte auf Deutsch."""

def generate_checklist(vehicle_data):
    vehicle_str = json.dumps(vehicle_data, ensure_ascii=False)
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[
            {
                "role": "user", 
                "content": f"Erstelle eine Kaufberatungs-Checkliste fuer dieses Fahrzeug:\n\n{vehicle_str}"
            }
        ],
        system=SYSTEM_PROMPT
    )
    
    response_text = message.content[0].text.strip()
    
    # Clean up if wrapped in code blocks
    if response_text.startswith('```'):
        lines = response_text.split('\n')
        response_text = '\n'.join(lines[1:-1])
    
    return json.loads(response_text)

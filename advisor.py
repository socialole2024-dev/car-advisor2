import anthropic
import json

client = anthropic.Anthropic()

SYSTEM_PROMPT = """Du bist ein erfahrener Gebrauchtwagen-Gutachter in Deutschland. Antworte NUR mit einem validen JSON-Objekt:
{
  "vehicle_summary": {"title": "str", "price": "str", "mileage": "str", "year": "str", "market_assessment": "fair|cheap|expensive", "market_comment": "str"},
  "dealbreakers": [{"title": "str", "detail": "str", "priority": "dealbreaker"}],
  "critical_checks": [{"title": "str", "detail": "str", "priority": "critical"}],
  "important_checks": [{"title": "str", "detail": "str", "priority": "important"}],
  "onsite_checks": [{"title": "str", "detail": "str", "priority": "critical|important|info"}],
  "negotiation": {"target_price": 0, "opening_offer": 0, "arguments": ["str"], "limit": 0, "limit_note": "str"}
}
Beruecksichtige bekannte Schwachstellen und Rueckrufe. Alle Texte Deutsch."""

def generate_checklist(vehicle_data):
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": "Kaufberatung fuer: " + json.dumps(vehicle_data, ensure_ascii=False)}]
    )
    text = msg.content[0].text.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:-1])
    return json.loads(text)

import json

def build_export_html(advices_data):
    """Build offline-capable HTML with tabs for each vehicle, analog to example checklist."""
    
    tabs_html = ""
    pages_html = ""
    
    for i, item in enumerate(advices_data):
        advice = item['advice']
        checklist = item['checklist']
        vs = checklist.get('vehicle_summary', {})
        active = 'active' if i == 0 else ''
        short_title = vs.get('title', advice.get('title', 'Fahrzeug'))[:30]
        price = vs.get('price', '—')
        
        tabs_html += f'''
        <div class="tab {active}" onclick="switchTab('v{i}', this)">
            {short_title}<br><small style="font-size:11px;color:#aaa">{price}</small>
        </div>'''
        
        # Build checks HTML
        checks_html = ""
        for item_data in checklist.get('dealbreakers', []):
            checks_html += f'''
            <div class="check-item"><label>
                <input type="checkbox" onchange="updateProgress()">
                <div class="checkmark"></div>
                <div class="txt">
                    <span class="priority crit">DEALBREAKER</span>
                    <div class="main">{item_data["title"]}</div>
                    <div class="sub">{item_data["detail"]}</div>
                </div>
            </label></div>'''
        
        for item_data in checklist.get('critical_checks', []):
            checks_html += f'''
            <div class="check-item"><label>
                <input type="checkbox" onchange="updateProgress()">
                <div class="checkmark"></div>
                <div class="txt">
                    <span class="priority crit">KRITISCH</span>
                    <div class="main">{item_data["title"]}</div>
                    <div class="sub">{item_data["detail"]}</div>
                </div>
            </label></div>'''
        
        for item_data in checklist.get('important_checks', []):
            checks_html += f'''
            <div class="check-item"><label>
                <input type="checkbox" onchange="updateProgress()">
                <div class="checkmark"></div>
                <div class="txt">
                    <span class="priority warn">WICHTIG</span>
                    <div class="main">{item_data["title"]}</div>
                    <div class="sub">{item_data["detail"]}</div>
                </div>
            </label></div>'''
        
        # Onsite checks
        onsite_html = ""
        for item_data in checklist.get('onsite_checks', []):
            p = item_data.get('priority', 'info')
            badge = 'KRITISCH' if p == 'critical' else ('WICHTIG' if p == 'important' else 'CHECK')
            cls = 'crit' if p == 'critical' else ('warn' if p == 'important' else 'info')
            onsite_html += f'''
            <div class="check-item"><label>
                <input type="checkbox" onchange="updateProgress()">
                <div class="checkmark"></div>
                <div class="txt">
                    <span class="priority {cls}">{badge}</span>
                    <div class="main">{item_data["title"]}</div>
                    <div class="sub">{item_data["detail"]}</div>
                </div>
            </label></div>'''
        
        # Negotiation
        n = checklist.get('negotiation', {})
        args = ''.join([f'&middot; {a}<br>' for a in n.get('arguments', [])])
        neg_html = f'''
        <div class="verhandlung">
            <h3>Zielpreis</h3>
            <div class="price-target">{n.get("target_price", "—")} &euro;</div>
            <p><strong>Einstieg:</strong> {n.get("opening_offer", "—")} &euro;<br><br>
            <strong>Argumente:</strong><br>{args}<br>
            <strong>&#x26A0; Limit: {n.get("limit", "—")} &euro;</strong><br>
            {n.get("limit_note", "")}</p>
        </div>
        <div class="note-area">
            <textarea placeholder="Eindr&uuml;cke, Aussagen des Verk&auml;ufers..."></textarea>
        </div>'''
        
        market_cls = 'ok' if vs.get('market_assessment') == 'fair' else 'warn'
        
        pages_html += f'''
        <div id="page-v{i}" class="page {active}">
            <div class="price-tag">
                <div class="lbl">{vs.get("title", "—")}</div>
                <div class="price">{vs.get("price", "—")}</div>
                <span class="verdict {market_cls}">{vs.get("market_comment", "")}</span>
            </div>
            <div class="stats">
                <div class="stat-row"><span class="stat-label">Kilometer</span><span class="stat-val">{vs.get("mileage", "—")}</span></div>
                <div class="stat-row"><span class="stat-label">Baujahr</span><span class="stat-val">{vs.get("year", "—")}</span></div>
                <div class="stat-row"><span class="stat-label">Quelle</span><span class="stat-val">{advice.get("url", "—")[:60]}...</span></div>
            </div>
            <div class="sub-tabs">
                <div class="sub-tab active" onclick="switchSubTab('v{i}','checks',this)">&#x1F50D; Checks</div>
                <div class="sub-tab" onclick="switchSubTab('v{i}','onsite',this)">&#x1F697; Vor Ort</div>
                <div class="sub-tab" onclick="switchSubTab('v{i}','deal',this)">&#x1F4AC; Verhandlung</div>
            </div>
            <div id="v{i}-checks" class="sub-page active">{checks_html}</div>
            <div id="v{i}-onsite" class="sub-page">{onsite_html}</div>
            <div id="v{i}-deal" class="sub-page">{neg_html}</div>
        </div>'''
    
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>Kaufberatung &mdash; Car Advisor</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f0; color: #1a1a1a; font-size: 16px; padding-bottom: 80px; }}
header {{ background: #1a1a1a; color: #fff; padding: 16px; position: sticky; top: 0; z-index: 100; }}
header h1 {{ font-size: 17px; font-weight: 600; }}
header p {{ font-size: 13px; color: #aaa; margin-top: 2px; }}
.tabs {{ display: flex; background: #fff; border-bottom: 1px solid #e0e0e0; position: sticky; top: 58px; z-index: 99; overflow-x: auto; }}
.tab {{ flex: 1; min-width: 120px; padding: 12px 6px; text-align: center; font-size: 13px; font-weight: 500; border-bottom: 3px solid transparent; color: #888; cursor: pointer; }}
.tab.active {{ color: #1a1a1a; border-bottom-color: #1a1a1a; }}
.page {{ display: none; padding: 12px; }}
.page.active {{ display: block; }}
.sub-tabs {{ display: flex; background: #f0f0f0; border-radius: 10px; padding: 4px; margin-bottom: 12px; gap: 4px; }}
.sub-tab {{ flex: 1; padding: 8px 4px; text-align: center; font-size: 13px; font-weight: 500; border-radius: 8px; color: #888; cursor: pointer; }}
.sub-tab.active {{ background: #fff; color: #1a1a1a; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
.sub-page {{ display: none; }}
.sub-page.active {{ display: block; }}
.price-tag {{ background: #fff; border-radius: 12px; padding: 14px 16px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
.price-tag .lbl {{ font-size: 13px; color: #666; }}
.price-tag .price {{ font-size: 26px; font-weight: 700; margin: 4px 0; }}
.verdict {{ display: inline-block; font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 6px; }}
.verdict.ok {{ background: #FEF3C7; color: #92400E; }}
.verdict.warn {{ background: #FEE2E2; color: #991B1B; }}
.stats {{ background: #fff; border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
.stat-row {{ display: flex; justify-content: space-between; padding: 7px 0; border-bottom: 1px solid #f0f0f0; font-size: 14px; }}
.stat-row:last-child {{ border-bottom: none; }}
.stat-label {{ color: #666; }}
.stat-val {{ font-weight: 600; }}
.check-item {{ background: #fff; border-radius: 12px; margin-bottom: 6px; box-shadow: 0 1px 3px rgba(0,0,0,.08); overflow: hidden; }}
.check-item label {{ display: flex; align-items: flex-start; padding: 13px 14px; gap: 12px; cursor: pointer; }}
.check-item input[type=checkbox] {{ display: none; }}
.checkmark {{ width: 24px; height: 24px; border-radius: 50%; border: 2px solid #ccc; flex-shrink: 0; margin-top: 2px; display: flex; align-items: center; justify-content: center; font-size: 14px; color: transparent; transition: all .15s; }}
.check-item input:checked ~ .checkmark {{ background: #059669; border-color: #059669; color: #fff; }}
.check-item input:checked ~ .checkmark::after {{ content: '\2713'; }}
.check-item input:checked ~ .txt .main {{ color: #aaa; text-decoration: line-through; }}
.txt {{ flex: 1; }}
.priority {{ display: inline-block; font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 4px; margin-bottom: 4px; }}
.priority.crit {{ background: #FEE2E2; color: #991B1B; }}
.priority.warn {{ background: #FEF3C7; color: #92400E; }}
.priority.info {{ background: #DBEAFE; color: #1E40AF; }}
.main {{ font-size: 15px; font-weight: 600; line-height: 1.3; }}
.sub {{ font-size: 13px; color: #777; margin-top: 4px; line-height: 1.45; }}
.verhandlung {{ background: #1a1a1a; color: #fff; border-radius: 12px; padding: 16px; margin-bottom: 6px; }}
.verhandlung h3 {{ font-size: 12px; font-weight: 700; color: #aaa; text-transform: uppercase; letter-spacing: .5px; margin-bottom: 4px; }}
.price-target {{ font-size: 28px; font-weight: 700; color: #4ADE80; margin-bottom: 8px; }}
.verhandlung p {{ font-size: 13px; line-height: 1.6; color: #ccc; }}
.verhandlung strong {{ color: #fff; }}
.note-area {{ background: #fff; border-radius: 12px; padding: 12px 14px; margin-top: 6px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
.note-area textarea {{ width: 100%; border: none; outline: none; font-size: 14px; font-family: inherit; resize: none; min-height: 90px; background: transparent; }}
.progress-bar {{ position: fixed; bottom: 0; left: 0; right: 0; background: #fff; border-top: 1px solid #e0e0e0; padding: 10px 16px 12px; z-index: 200; }}
.progress-label {{ font-size: 13px; color: #666; margin-bottom: 5px; display: flex; justify-content: space-between; }}
.progress-track {{ background: #e0e0e0; border-radius: 4px; height: 7px; }}
.progress-fill {{ height: 100%; background: #059669; border-radius: 4px; transition: width .25s; }}
</style>
</head>
<body>
<header>
    <h1>&#x1F697; Kaufberatung</h1>
    <p>Erstellt mit Car Advisor &mdash; {len(advices_data)} Fahrzeug{'e' if len(advices_data) > 1 else ''}</p>
</header>
<div class="tabs">{tabs_html}</div>
{pages_html}
<div class="progress-bar">
    <div class="progress-label"><span id="pt">Checks erledigt</span><span id="pc">0 / 0</span></div>
    <div class="progress-track"><div class="progress-fill" id="pf" style="width:0%"></div></div>
</div>
<script>
function switchTab(id,el){{document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));el.classList.add('active');document.getElementById('page-'+id).classList.add('active');updateProgress();}}
function switchSubTab(vid,id,el){{var page=document.getElementById('page-'+vid);page.querySelectorAll('.sub-tab').forEach(t=>t.classList.remove('active'));page.querySelectorAll('.sub-page').forEach(p=>p.classList.remove('active'));el.classList.add('active');document.getElementById(vid+'-'+id).classList.add('active');updateProgress();}}
function updateProgress(){{var p=document.querySelector('.sub-page.active');if(!p){{p=document.querySelector('.page.active');}}if(!p)return;var all=p.querySelectorAll('input[type=checkbox]');var done=p.querySelectorAll('input[type=checkbox]:checked');var pct=all.length?Math.round(done.length/all.length*100):0;document.getElementById('pf').style.width=pct+'%';document.getElementById('pc').textContent=done.length+' / '+all.length;document.getElementById('pt').textContent=pct===100?'\u2705 Alles gecheckt!':'Checks erledigt';}}
updateProgress();
</script>
</body>
</html>"""
    return html

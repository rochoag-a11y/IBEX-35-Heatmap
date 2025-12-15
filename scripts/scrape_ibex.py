import json, re, time
import requests
from bs4 import BeautifulSoup

OUT = 'data/ibex35.json'

# -------- Helpers --------
def parse_marketscreener():
    """
    Intenta extraer (name, cap, change%) de MarketScreener IBEX 35 componentes.
    """
    url = "https://es.marketscreener.com/cotizacion/indice/IBEX-35-7629/componentes/"
    html = requests.get(url, timeout=30).text
    soup = BeautifulSoup(html, "lxml")

    rows = []
    # La tabla lista: nombre, capitalización (Capi.), variación diaria, etc.
    # Seleccionamos los bloques de filas que contengan esos campos.
    for tr in soup.select('table tr'):
        tds = [td.get_text(strip=True) for td in tr.select('td')]
        if len(tds) >= 4:
            name = tds[0]
            cap_txt = tds[1]
            chg_txt = tds[2]
            # Capitalización ejemplo: "198 mil M" o "33,69B" dependiendo del site (ES/EN)
            cap = None
            m1 = re.search(r'([0-9]+(?:[\\.,][0-9]+)?)\\s*([MB])', cap_txt)
            m2 = re.search(r'([0-9]+(?:[\\.,][0-9]+)?)\\s*mil\\s*M', cap_txt)
            if m1:
                val = float(m1.group(1).replace('.', '').replace(',', '.'))
                unit = m1.group(2)
                cap = val * (1e9 if unit=='B' else 1e6)
            elif m2:
                # "198 mil M" ~ 198,000 M€ => 198e9
                val = float(m2.group(1).replace(',', '.'))
                cap = val * 1e9
            # Variación diaria ejemplo: "+0,69 %"
            chg = None
            m3 = re.search(r'([+-]?[0-9]+(?:[\\.,][0-9]+)?)\\s*%?', chg_txt)
            if m3:
                chg = float(m3.group(1).replace(',', '.'))

            if cap is not None and chg is not None:
                rows.append({'name': name, 'size': cap, 'change': chg})

    return rows

def backup_caps_from_marketsinsider():
    """
    Lee capitalizaciones por empresa desde Markets Insider.
    """
    url = "https://markets.businessinsider.com/index/market-capitalization/ibex_35"
    html = requests.get(url, timeout=30).text
    soup = BeautifulSoup(html, "lxml")
    out = {}
    for tr in soup.select('table tr'):
        tds = [td.get_text(" ", strip=True) for td in tr.select('td')]
        if len(tds) >= 7:
            name = tds[0]
            cap_txt = tds[-1]
            m = re.search(r'([0-9]+(?:[\\.,][0-9]+)?)\\s*(EUR|USD)', cap_txt)
            if m:
                # Markets Insider suele mostrar cifras en millones (M) → normalizamos a €
                val = float(m.group(1).replace('.', '').replace(',', '.'))
                # Suelen estar en millones; si detectas 'M' en el contexto, ajusta:
                # Aquí asumimos ya millones y convertimos a euros unidades
                out[name.upper()] = val * 1e6
    return out

def backup_changes_from_investing():
    """
    Variación diaria desde Investing.com (tabla de componentes).
    """
    url = "https://www.investing.com/indices/spain-35-components"
    hdrs = {'User-Agent': 'Mozilla/5.0'}
    html = requests.get(url, headers=hdrs, timeout=30).text
    soup = BeautifulSoup(html, "lxml")
    changes = {}
    for tr in soup.select('table tr'):
        tds = [td.get_text(" ", strip=True) for td in tr.select('td')]
        if len(tds) >= 5:
            name = tds[0]
            chg_txt = tds[4]  # "Chg. %"
            m = re.search(r'([+-]?[0-9]+(?:[\\.,][0-9]+)?)%?', chg_txt)
            if m:
                changes[name.upper()] = float(m.group(1).replace(',', '.'))
    return changes

# -------- Build JSON --------
def build_json():
    rows = parse_marketscreener()
    if len(rows) < 30:
        # fallback combinando backups
        caps = backup_caps_from_marketsinsider()
        chgs = backup_changes_from_investing()
        rows = []
        for key, cap in caps.items():
            chg = chgs.get(key)
            if chg is not None:
                rows.append({'name': key.title(), 'size': cap, 'change': chg})

    # Tickers: heurística simple (preferimos nombre corto)
    for r in rows:
        # ejemplo: "INDITEX" -> "ITX"; "IBERDROLA, S.A." -> "IBE"
        # Podrías mapear manualmente si deseas exactitud 100%
        r['ticker'] = re.sub(r'[^A-Z]', '', r['name'].split()[0])[0:4].upper()

    # Normaliza tamaños si faltan o sobran magnitudes
    # (opcional) aquí podrías limitar el ratio para evitar outliers visuales.
    return rows

if __name__ == "__main__":
    data = build_json()
    data = sorted(data, key=lambda d: d['size'], reverse=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"Escrito {OUT} con {len(data)} empresas a las {time.ctime()}")

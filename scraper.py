import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

url = 'https://www.ribaj.com/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.9'
}

rss_items = ""
count = 0
seen_links = set()

try:
    print("Stahuji data z RIBAJ...")
    response = requests.get(url, headers=headers, timeout=15)
    response.encoding = 'utf-8'
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Univerzální funkce pro vkládání nalezených článků do XML
        def add_item(link, title, desc, img_url, meta_info):
            global count, rss_items
            if not link or not title: return
            
            # Doplnění domény, pokud je odkaz relativní
            full_url = link if link.startswith('http') else 'https://www.ribaj.com' + link
            
            # Kontrola duplicit
            if full_url in seen_links: return
            seen_links.add(full_url)
            
            if img_url and not img_url.startswith('http'):
                img_url = 'https://www.ribaj.com' + img_url
                
            # Očištění o případné rozbité znaky
            clean_title = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            # Příprava popisu pro čtečku
            description_html = ""
            if meta_info:
                description_html += f"<p><small>{meta_info}</small></p>"
            if desc:
                description_html += f"<p>{desc}</p>"
                
            # Připojení obrázku v metadatech (pro CommaFeed)
            enclosure_tag = ""
            media_tag = ""
            if img_url:
                clean_img = img_url.replace('&', '&amp;')
                enclosure_tag = f'<enclosure url="{clean_img}" type="image/jpeg" length="1024" />'
                media_tag = f'<media:content url="{clean_img}" medium="image" />'
                
            rss_items += f"""
        <item>
            <title><![CDATA[{clean_title}]]></title>
            <link>{full_url}</link>
            <guid>{full_url}</guid>
            <description><![CDATA[{description_html}]]></description>
            {enclosure_tag}
            {media_tag}
        </item>"""
            count += 1

        # 1. Zpracování velkého karuselu nahoře (Featured cards)
        for card in soup.find_all('div', class_='featured-card'):
            link = card.get('data-link')
            title = card.get('data-title')
            meta_info = card.get('data-tags', '').replace('|', ' | ') # Změní "Datum|Autor" na hezčí "Datum | Autor"
            img_tag = card.find('img')
            img_url = img_tag.get('src') if img_tag else ""
            
            add_item(link, title, "", img_url, meta_info)

        # 2. Zpracování všech ostatních karet (Seznamy, Doporučené, Populární)
        # Pomocí regulárního výrazu najdeme všechny možné třídy odkazů s články
        article_cards = soup.find_all('a', class_=re.compile(r'ribaj-listing-card|suggested-content-card|most-popular-block__item'))
        
        for card in article_cards:
            link = card.get('href')
            
            # Nadpis
            title_tag = card.find(class_=re.compile(r'title|label'))
            title = title_tag.get_text(strip=True) if title_tag else ""
            
            # Perex (popis)
            desc_tag = card.find(class_=re.compile(r'description'))
            desc = desc_tag.get_text(strip=True) if desc_tag else ""
            
            # Datum a autor (často jako více <div> s třídou 'bite')
            bites = card.find_all(class_=re.compile(r'bite|subtitle'))
            meta_info = " | ".join([b.get_text(strip=True) for b in bites])
            
            # Obrázek
            img_tag = card.find('img')
            img_url = img_tag.get('src') if img_tag else ""
            
            add_item(link, title, desc, img_url, meta_info)
            
    else:
        print("Chyba serveru. Status:", response.status_code)

except Exception as e:
    print(f"Kritická chyba: {e}")

# Sestavení finálního XML s podporou Media RSS namespace
rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
<channel>
  <title>RIBA Journal</title>
  <link>{url}</link>
  <description>Royal Institute of British Architects Journal</description>
  <lastBuildDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")}</lastBuildDate>
  {rss_items}
</channel>
</rss>"""

with open('feed.xml', 'w', encoding='utf-8') as f:
    f.write(rss_feed)

print(f"HOTOVO: Úspěšně zpracováno {count} projektů.")

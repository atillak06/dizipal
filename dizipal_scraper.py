import re
import ssl
import cloudscraper
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

urllib3.disable_warnings()

BASE_DOMAIN = "https://dizipal1224.com"
START_URLS = [
    f"{BASE_DOMAIN}/tur/aksiyon?yil=2025"
]

OUTPUT_FILE = "output.m3u"

# 🔥 EN KRİTİK PARÇA
class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False, **kwargs):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=ctx,
        )

class DizipalScraper:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "windows",
                "desktop": True
            }
        )

        # 🔥 SSL ADAPTER ZORLA
        self.scraper.mount("https://", SSLAdapter())
        self.scraper.mount("http://", SSLAdapter())

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "*/*",
            "Referer": BASE_DOMAIN,
            "Origin": BASE_DOMAIN
        }

        self.m3u = ["#EXTM3U"]

    def fetch(self, url):
        print(f"🌐 Sayfa: {url}")
        r = self.scraper.get(
            url,
            headers=self.headers,
            timeout=30
        )
        r.raise_for_status()
        return r.text

    def find_iframe(self, html):
        soup = BeautifulSoup(html, "html.parser")
        iframe = soup.find("iframe")
        if iframe and iframe.get("src"):
            return urljoin(BASE_DOMAIN, iframe["src"])
        return None

    def find_m3u8(self, html):
        match = re.search(r"https?://[^\s'\"<>]+\.m3u8", html)
        return match.group(0) if match else None

    def crawl(self):
        for url in START_URLS:
            html = self.fetch(url)
            soup = BeautifulSoup(html, "html.parser")

            links = []
            for a in soup.select("a[href]"):
                href = a["href"]
                if "/dizi/" in href:
                    links.append(urljoin(BASE_DOMAIN, href))

            print(f"🔗 Bulunan içerik: {len(links)}")

            for link in links[:10]:
                try:
                    page_html = self.fetch(link)

                    iframe_url = self.find_iframe(page_html)
                    if not iframe_url:
                        continue

                    print(f"▶ Iframe: {iframe_url}")
                    iframe_html = self.fetch(iframe_url)

                    m3u8 = self.find_m3u8(iframe_html)
                    if not m3u8:
                        continue

                    title_tag = BeautifulSoup(page_html, "html.parser").title
                    title = title_tag.text.strip() if title_tag else "Dizipal"

                    self.m3u.append(f"#EXTINF:-1,{title}")
                    self.m3u.append(m3u8)

                    print("✅ M3U8 bulundu")

                except Exception as e:
                    print(f"❌ Atlandı: {e}")

        self.save()

    def save(self):
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(self.m3u))
        print(f"\n📁 OLUŞTU: {OUTPUT_FILE}")

if __name__ == "__main__":
    DizipalScraper().crawl()

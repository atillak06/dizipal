import re
import ssl
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_DOMAIN = "https://dizipal1224.com"
START_URLS = [
    f"{BASE_DOMAIN}/tur/aksiyon?yil=2025",
]

OUTPUT_FILE = "output.m3u"

class DizipalScraper:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "windows",
                "desktop": True
            }
        )

        # SSL sorunlarını bypass et
        self.scraper.verify = False
        ssl._create_default_https_context = ssl._create_unverified_context

        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
            "Referer": BASE_DOMAIN,
            "Host": BASE_DOMAIN.replace("https://", "")
        }

        self.m3u_lines = ["#EXTM3U"]

    def fetch(self, url):
        print(f"🌐 Sayfa: {url}")
        r = self.scraper.get(
            url,
            headers=self.headers,
            timeout=20
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
        # Direkt m3u8 araması
        m3u8 = re.findall(r"https?://[^\s'\"]+\.m3u8", html)
        return m3u8[0] if m3u8 else None

    def crawl(self):
        for url in START_URLS:
            html = self.fetch(url)
            soup = BeautifulSoup(html, "html.parser")

            links = []
            for a in soup.select("a"):
                href = a.get("href")
                if href and "/dizi/" in href:
                    links.append(urljoin(BASE_DOMAIN, href))

            print(f"🔗 Bulunan içerik: {len(links)}")

            for link in links[:10]:  # ilk 10
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

                    title = BeautifulSoup(page_html, "html.parser").title.text.strip()

                    self.m3u_lines.append(f"#EXTINF:-1,{title}")
                    self.m3u_lines.append(m3u8)

                    print(f"✅ M3U8 bulundu")

                except Exception as e:
                    print(f"❌ Hata: {e}")

        self.save()

    def save(self):
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(self.m3u_lines))
        print(f"\n📁 KAYDEDİLDİ: {OUTPUT_FILE}")

if __name__ == "__main__":
    DizipalScraper().crawl()

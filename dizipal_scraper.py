#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cloudscraper
import requests
import re
import time
import socket
import ssl
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

# -------------------------------------------------
# SSL / DNS / CERT BYPASS (Python 3.10+ FIX)
# -------------------------------------------------

class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)

# -------------------------------------------------

class DizipalScraper:

    def __init__(self):
        self.base_domain = self.get_current_domain().replace("https://", "").replace("http://", "")
        self.base_url = f"https://{self.base_domain}"
        self.base_ip = self.resolve_ip(self.base_domain)

        print(f"🔗 Domain : {self.base_domain}")
        print(f"🌐 IP     : {self.base_ip}")

        self.scraper = cloudscraper.create_scraper()
        self.scraper.mount("https://", SSLAdapter())
        self.scraper.mount("http://", SSLAdapter())

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "*/*",
            "Accept-Language": "tr-TR,tr;q=0.9",
            "Host": self.base_domain,
            "Referer": self.base_url
        }

        self.years = list(range(2025, 1959, -1))

        # TEST İÇİN AZ TUTTUM – İSTERSEN ARTIR
        self.film_turleri = {
            "aksiyon": "aksiyon",
            "korku": "korku",
            "komedi": "komedi"
        }

    # -------------------------------------------------

    def get_current_domain(self):
        try:
            url = "https://raw.githubusercontent.com/koprulu555/domain-kontrol2/main/dizipaldomain.txt"
            r = requests.get(url, timeout=10)
            for line in r.text.splitlines():
                if line.startswith("guncel_domain="):
                    return line.split("=", 1)[1].strip().rstrip("/")
        except:
            pass
        return "https://dizipal1224.com"

    def resolve_ip(self, domain):
        try:
            return socket.gethostbyname(domain)
        except:
            return None

    # -------------------------------------------------
    # DNS BYPASS FETCH
    # -------------------------------------------------

    def fetch(self, url):
        parsed = urlparse(url)
        ip_url = f"https://{self.base_ip}{parsed.path}"
        if parsed.query:
            ip_url += "?" + parsed.query

        r = self.scraper.get(
            ip_url,
            headers=self.headers,
            timeout=25
        )
        return r.text if r.status_code == 200 else ""

    # -------------------------------------------------
    # IFRAME → M3U8
    # -------------------------------------------------

    def extract_m3u8_from_iframe(self, film_html):
        soup = BeautifulSoup(film_html, "html.parser")
        iframe = soup.find("iframe")
        if not iframe or not iframe.get("src"):
            return None

        iframe_url = iframe["src"]
        if iframe_url.startswith("//"):
            iframe_url = "https:" + iframe_url

        parsed = urlparse(iframe_url)
        iframe_ip = self.resolve_ip(parsed.netloc)
        if not iframe_ip:
            return None

        iframe_headers = self.headers.copy()
        iframe_headers["Host"] = parsed.netloc
        iframe_headers["Referer"] = self.base_url

        iframe_ip_url = f"https://{iframe_ip}{parsed.path}"
        if parsed.query:
            iframe_ip_url += "?" + parsed.query

        r = self.scraper.get(
            iframe_ip_url,
            headers=iframe_headers,
            timeout=25
        )

        html = r.text
        m3u8 = re.findall(r'https?://[^"\']+\.m3u8[^"\']*', html)
        return m3u8[0] if m3u8 else None

    # -------------------------------------------------
    # MAIN
    # -------------------------------------------------

    def crawl(self):
        m3u = ["#EXTM3U"]

        for tur, slug in self.film_turleri.items():
            print(f"\n🎬 {tur.upper()}")

            for year in self.years:
                url = f"{self.base_url}/tur/{slug}?yil={year}"
                html = self.fetch(url)
                if not html:
                    break

                soup = BeautifulSoup(html, "html.parser")
                films = soup.select("article.type2 ul li a[href*='/film/']")
                if not films:
                    break

                for a in films:
                    film_url = urljoin(self.base_url, a["href"])
                    film_html = self.fetch(film_url)
                    if not film_html:
                        continue

                    soup2 = BeautifulSoup(film_html, "html.parser")
                    title = soup2.title.text.split(" İzle")[0].strip()

                    poster = ""
                    og = soup2.find("meta", property="og:image")
                    if og:
                        poster = og.get("content", "")

                    m3u8 = self.extract_m3u8_from_iframe(film_html)
                    if not m3u8:
                        continue

                    m3u.append(
                        f'#EXTINF:-1 tvg-name="{title}" tvg-logo="{poster}" group-title="Film - {tur.upper()}",{title}'
                    )
                    m3u.append(m3u8)

                    print(f"  ✅ {title}")

                time.sleep(1)

        with open("dizipal_filmler.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u))

        print("\n✅ TAMAMLANDI → dizipal_filmler.m3u")

# -------------------------------------------------

if __name__ == "__main__":
    DizipalScraper().crawl()

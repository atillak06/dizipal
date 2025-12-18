#!/usr/bin/env python3
"""
DİZİPAL M3U SCRAPER - Tam M3U formatında, kategorilere ayrılmış
"""

import cloudscraper
import requests
import re
import time
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup

class DizipalScraper:
    def __init__(self):
        self.base_url = self.get_current_domain()
        print(f"🔗 Domain: {self.base_url}")
        self.scraper = cloudscraper.create_scraper()
        self.scraper.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': self.base_url
        })
        
        # CloudStream kodundaki kategori yapılarını kullanıyoruz
        self.film_turleri = {
            'aile': 'aile',
            'aksiyon': 'aksiyon',
            'animasyon': 'animasyon',
            'anime': 'anime',
            'belgesel': 'belgesel',
            'bilimkurgu': 'bilimkurgu',
            'biyografi': 'biyografi',
            'dram': 'dram',
            'editorun-sectikleri': 'editorun-sectikleri',
            'erotik': 'erotik',
            'fantastik': 'fantastik',
            'gerilim': 'gerilim',
            'gizem': 'gizem',
            'komedi': 'komedi',
            'korku': 'korku',
            'macera': 'macera',
            'mubi': 'mubi',
            'muzik': 'muzik',
            'romantik': 'romantik',
            'savas': 'savas',
            'spor': 'spor',
            'suc': 'suc',
            'tarih': 'tarih',
            'western': 'western',
            'yerli': 'yerli'
        }
        
        self.dizi_turleri = {
            'aile': 1,
            'aksiyon': 2,
            'animasyon': 3,
            'belgesel': 4,
            'bilimkurgu': 5,
            'biyografi': 6,
            'dram': 7,
            'fantastik': 8,
            'gerilim': 9,
            'gizem': 10,
            'komedi': 11,
            'korku': 12,
            'macera': 13,
            'muzik': 14,
            'romantik': 16,
            'savas': 17,
            'spor': 18,
            'suc': 19,
            'tarih': 20,
            'western': 21,
            'yerli': 24,
            'erotik': 25,
            'anime': 26
        }
        
        self.platform_type = {
            'asya-dizileri': 1,
            'netflix': 2,
            'exxen': 3,
            'blutv': 4,
            'gain': 5,
            'disney': 6,
            'amazon-prime': 7,
            'tod-bein': 8
        }
        
        self.platform_koleksiyon = {
            'netflix': 'netflix',
            'exxen': 'exxen',
            'blutv': 'blutv',
            'disney': 'disney',
            'amazon-prime': 'amazon-prime',
            'tod-bein': 'tod-bein',
            'gain': 'gain',
            'mubi': 'mubi',
            'asya-dizileri': 'asya-dizileri'
        }
        
        # Toplanan tüm içerikler
        self.all_content = []

    def get_current_domain(self):
        """GitHub'dan güncel domain'i al"""
        try:
            url = "https://raw.githubusercontent.com/koprulu555/domain-kontrol2/refs/heads/main/dizipaldomain.txt"
            r = requests.get(url, timeout=10)
            for line in r.text.split('\n'):
                if line.startswith('guncel_domain='):
                    domain = line.split('=', 1)[1].strip()
                    if domain:
                        return domain.rstrip('/')
        except:
            pass
        return "https://dizipal1222.com"

    def crawl_category(self, base_url, category_name, group_title, is_dizi=False):
        """Bir kategoriyi sayfalandırma ile tara"""
        print(f"\n📂 {category_name} taranıyor...")
        page = 1
        all_items = []
        
        while True:
            if '?' in base_url:
                url = f"{base_url}&sayfa={page}"
            else:
                url = f"{base_url}?sayfa={page}" if page > 1 else base_url
            
            try:
                print(f"   Sayfa {page}: {url}")
                r = self.scraper.get(url, timeout=30)
                
                # CloudFlare koruması kontrolü
                if r.status_code == 403 or "Cloudflare" in r.text:
                    print("   ⚠️  Cloudflare engeli, bekleniyor...")
                    time.sleep(5)
                    continue
                    
                soup = BeautifulSoup(r.content, 'html.parser')
                
                # İçerikleri bul
                items = []
                
                # Film/Dizi grid yapısı
                items = soup.select('article.type2 ul li')
                if not items:
                    # Son bölümler yapısı
                    items = soup.select('div.episode-item')
                
                if not items:
                    print(f"   ⏹️  Sayfa {page}: içerik bulunamadı, durduruluyor...")
                    break
                
                found_count = 0
                for item in items:
                    content_info = self.extract_content_info(item, is_dizi)
                    if content_info:
                        content_info['group_title'] = group_title
                        if content_info not in all_items:
                            all_items.append(content_info)
                            found_count += 1
                
                print(f"   ✅ Sayfa {page}: {found_count} içerik bulundu")
                
                # Sonraki sayfa kontrolü
                next_page = soup.select_one('a[rel="next"]')
                if not next_page:
                    break
                    
                page += 1
                time.sleep(2)  # Sunucu yükünü azalt
                
            except Exception as e:
                print(f"   ❌ Sayfa {page} hatası: {e}")
                break
        
        print(f"   📊 Toplam: {len(all_items)} içerik")
        return all_items

    def extract_content_info(self, item, is_dizi=False):
        """HTML öğesinden içerik bilgilerini çıkar"""
        try:
            # Bağlantıyı bul
            link = item.select_one('a')
            if not link:
                return None
                
            href = link.get('href', '')
            if not href or ('/dizi/' not in href and '/film/' not in href):
                return None
            
            full_url = urljoin(self.base_url, href)
            
            # Poster/logo URL'sini bul
            img = item.select_one('img')
            poster_url = urljoin(self.base_url, img.get('src', '')) if img else ''
            
            # İsim bilgisini bul
            name = None
            if is_dizi:
                # Dizi bölümü için
                name_div = item.select_one('div.name')
                episode_div = item.select_one('div.episode')
                if name_div and episode_div:
                    name = f"{name_div.text.strip()} {episode_div.text.strip()}"
                else:
                    # Normal dizi/film grid'i
                    title_span = item.select_one('span.title')
                    if title_span:
                        name = title_span.text.strip()
            else:
                # Film için
                title_span = item.select_one('span.title')
                if title_span:
                    name = title_span.text.strip()
            
            if not name:
                # URL'den isim çıkar
                name = self.extract_name_from_url(full_url)
            
            # TVG ID oluştur (URL'den güvenli bir versiyon)
            tvg_id = re.sub(r'[^a-zA-Z0-9]', '_', full_url.replace(self.base_url, ''))
            
            return {
                'name': name,
                'url': full_url,
                'poster': poster_url,
                'tvg_id': tvg_id[:50],  # 50 karakterle sınırla
                'type': 'dizi' if '/dizi/' in full_url else 'film'
            }
            
        except Exception as e:
            print(f"    ⚠️  İçerik çıkarım hatası: {e}")
            return None

    def get_all_episodes(self, dizi_url):
        """Bir dizinin tüm sezon ve bölümlerini çek"""
        episodes = []
        try:
            print(f"    🔍 Bölümler taranıyor: {dizi_url}")
            r = self.scraper.get(dizi_url, timeout=30)
            soup = BeautifulSoup(r.content, 'html.parser')
            
            # Sezon listesini bul
            sezon_select = soup.select_one('select[name="sezon"]')
            if sezon_select:
                sezon_options = sezon_select.select('option')
                sezon_nolar = [opt['value'] for opt in sezon_options if opt['value'].isdigit()]
                
                for sezon_no in sezon_nolar:
                    sezon_url = f"{dizi_url}/sezon-{sezon_no}"
                    try:
                        r2 = self.scraper.get(sezon_url, timeout=30)
                        soup2 = BeautifulSoup(r2.content, 'html.parser')
                        
                        # Bölüm linklerini bul
                        bolum_items = soup2.select('div.episode-item')
                        for item in bolum_items:
                            content_info = self.extract_content_info(item, True)
                            if content_info:
                                episodes.append(content_info)
                        
                        time.sleep(1)
                    except:
                        continue
            else:
                # Direkt bölüm listesi
                bolum_items = soup.select('div.episode-item')
                for item in bolum_items:
                    content_info = self.extract_content_info(item, True)
                    if content_info:
                        episodes.append(content_info)
            
        except Exception as e:
            print(f"    ❌ Bölüm çekme hatası: {e}")
        
        return episodes

    def crawl_films(self):
        """Filmleri türlere ve yıllara göre tara"""
        print("\n" + "="*60)
        print("🎬 FİLMLER taranıyor")
        print("="*60)
        
        # Yıllar (2025'ten 1960'a)
        years = list(range(2025, 1959, -1))
        
        for tur_adi in self.film_turleri.keys():
            print(f"\n   🎞️  {tur_adi.upper()} filmleri:")
            
            for year in years:
                # Film URL yapısı: /tur/{tur_adi}?genre=%2Ftur%2F{tur_adi}%3F&yil={yil}&kelime=
                encoded_tur = quote(f"/tur/{tur_adi}?", safe='')
                url = f"{self.base_url}/tur/{tur_adi}?genre={encoded_tur}&yil={year}&kelime="
                
                films = self.crawl_category(url, f"{tur_adi} {year}", f"Film - {tur_adi.upper()}")
                
                for film in films:
                    if film not in self.all_content:
                        self.all_content.append(film)
                
                if not films:
                    # Bu yılda film yoksa diğer yıla geç
                    continue
                
                time.sleep(3)

    def crawl_series(self):
        """Dizileri türlere ve platformlara göre tara"""
        print("\n" + "="*60)
        print("📺 DİZİLER taranıyor")
        print("="*60)
        
        # 1. Dizi türlerine göre
        for tur_adi, tur_no in self.dizi_turleri.items():
            print(f"\n   📺 {tur_adi.upper()} dizileri:")
            url = f"{self.base_url}/diziler?kelime=&durum=&tur={tur_no}&type=&siralama="
            
            series = self.crawl_category(url, tur_adi, f"Dizi - {tur_adi.upper()}", True)
            
            # Her dizinin bölümlerini çek
            for series_item in series:
                if series_item['type'] == 'dizi' and '/sezon-' not in series_item['url']:
                    episodes = self.get_all_episodes(series_item['url'])
                    for episode in episodes:
                        episode['group_title'] = series_item['group_title']
                        if episode not in self.all_content:
                            self.all_content.append(episode)
            
            time.sleep(3)
        
        # 2. Platform dizileri (type parametresi ile)
        for platform_adi, type_no in self.platform_type.items():
            print(f"\n   🏢 {platform_adi.upper()} dizileri (type):")
            url = f"{self.base_url}/diziler?kelime=&durum=&tur=&type={type_no}&siralama="
            
            series = self.crawl_category(url, platform_adi, f"Platform - {platform_adi.upper()}", True)
            
            for series_item in series:
                if series_item['type'] == 'dizi' and '/sezon-' not in series_item['url']:
                    episodes = self.get_all_episodes(series_item['url'])
                    for episode in episodes:
                        episode['group_title'] = series_item['group_title']
                        if episode not in self.all_content:
                            self.all_content.append(episode)
            
            time.sleep(3)
        
        # 3. Koleksiyon linkleri ile platform içerikleri
        for platform_adi in self.platform_koleksiyon.keys():
            print(f"\n   🏢 {platform_adi.upper()} koleksiyonu:")
            url = f"{self.base_url}/koleksiyon/{platform_adi}"
            
            series = self.crawl_category(url, platform_adi, f"Koleksiyon - {platform_adi.upper()}", True)
            
            for series_item in series:
                if series_item['type'] == 'dizi' and '/sezon-' not in series_item['url']:
                    episodes = self.get_all_episodes(series_item['url'])
                    for episode in episodes:
                        episode['group_title'] = series_item['group_title']
                        if episode not in self.all_content:
                            self.all_content.append(episode)
            
            time.sleep(3)

    def crawl_special_categories(self):
        """Özel kategorileri tara"""
        print("\n" + "="*60)
        print("⭐ ÖZEL KATEGORİLER taranıyor")
        print("="*60)
        
        # Son bölümler
        print("\n   📅 Son Bölümler:")
        url = f"{self.base_url}/diziler/son-bolumler"
        son_bolumler = self.crawl_category(url, "Son Bölümler", "Son Bölümler", True)
        self.all_content.extend(son_bolumler)
        
        # Seri filmler
        print("\n   🎞️  Seri Filmler:")
        url = f"{self.base_url}/seri-filmler"
        seri_filmler = self.crawl_category(url, "Seri Filmler", "Seri Filmler", False)
        self.all_content.extend(seri_filmler)
        
        # Tüm diziler
        print("\n   📺 Tüm Diziler:")
        url = f"{self.base_url}/diziler"
        tum_diziler = self.crawl_category(url, "Tüm Diziler", "Tüm Diziler", True)
        
        for dizi in tum_diziler:
            if dizi['type'] == 'dizi' and '/sezon-' not in dizi['url']:
                episodes = self.get_all_episodes(dizi['url'])
                for episode in episodes:
                    episode['group_title'] = dizi['group_title']
                    if episode not in self.all_content:
                        self.all_content.append(episode)
        
        # Tüm filmler
        print("\n   🎬 Tüm Filmler:")
        url = f"{self.base_url}/filmler"
        tum_filmler = self.crawl_category(url, "Tüm Filmler", "Tüm Filmler", False)
        self.all_content.extend(tum_filmler)

    def extract_name_from_url(self, url):
        """URL'den isim çıkar"""
        match = re.search(r'/(dizi|film)/([^/]+)', url)
        if match:
            name = match.group(2).replace('-', ' ').title()
            
            season_match = re.search(r'/sezon-(\d+)', url)
            episode_match = re.search(r'/bolum-(\d+)', url)
            
            if season_match and episode_match:
                return f"{name} S{season_match.group(1).zfill(2)}E{episode_match.group(1).zfill(2)}"
            return name
        return "İsimsiz İçerik"

    def generate_m3u(self):
        """Tam M3U formatında dosya oluştur"""
        print("\n📝 M3U dosyası oluşturuluyor...")
        
        m3u_lines = ['#EXTM3U']
        
        # İçerikleri group_title'e göre grupla
        grouped_content = {}
        for content in self.all_content:
            group = content.get('group_title', 'Diğer')
            if group not in grouped_content:
                grouped_content[group] = []
            grouped_content[group].append(content)
        
        # Her grup için
        for group_title, contents in sorted(grouped_content.items()):
            m3u_lines.append(f'\n# GROUP-TITLE: "{group_title}"')
            
            # İçerikleri sırala
            sorted_contents = sorted(contents, key=lambda x: x['name'])
            
            for content in sorted_contents:
                # TVG parametreleri
                tvg_id = content.get('tvg_id', '')
                tvg_name = content['name'].replace('"', "'")
                tvg_logo = content.get('poster', '')
                
                # M3U satırı
                m3u_line = f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{tvg_name}" tvg-logo="{tvg_logo}" group-title="{group_title}",{content["name"]}'
                m3u_lines.append(m3u_line)
                m3u_lines.append(content['url'])
        
        return '\n'.join(m3u_lines)

    def run(self):
        """Ana fonksiyon"""
        print("=" * 60)
        print("🚀 DİZİPAL M3U SCRAPER BAŞLIYOR")
        print("=" * 60)
        
        # 1. Filmleri tara
        self.crawl_films()
        
        # 2. Dizileri tara
        self.crawl_series()
        
        # 3. Özel kategorileri tara
        self.crawl_special_categories()
        
        # 4. İstatistikler
        print("\n" + "=" * 60)
        print("📊 İSTATİSTİKLER:")
        print("=" * 60)
        
        total = len(self.all_content)
        film_count = sum(1 for c in self.all_content if c['type'] == 'film')
        dizi_count = sum(1 for c in self.all_content if c['type'] == 'dizi')
        
        print(f"   Toplam İçerik: {total}")
        print(f"   Film Sayısı: {film_count}")
        print(f"   Dizi Bölümü Sayısı: {dizi_count}")
        
        # Grup başına içerik sayısı
        groups = {}
        for content in self.all_content:
            group = content.get('group_title', 'Diğer')
            groups[group] = groups.get(group, 0) + 1
        
        print("\n   Gruplar:")
        for group, count in sorted(groups.items()):
            print(f"     - {group}: {count} içerik")
        
        # 5. M3U oluştur
        m3u_content = self.generate_m3u()
        
        # 6. Dosyaya yaz
        with open('dizipal.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        
        print("\n" + "=" * 60)
        print(f"✅ BAŞARIYLA TAMAMLANDI!")
        print(f"📁 Çıktı: dizipal.m3u ({len(m3u_content.splitlines())} satır)")
        print("=" * 60)

if __name__ == "__main__":
    scraper = DizipalScraper()
    scraper.run()

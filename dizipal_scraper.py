#!/usr/bin/env python3
"""
DÜZGÜN DİZİPAL M3U SCRAPER - Tam Sürüm
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
        self.all_links = set()
        self.content_data = []
        
        # Yıl aralığı (2025'ten 1960'a kadar)
        self.years = list(range(2025, 1959, -1))
        
        # DİZİ TÜRLERİ (CloudStream yapısına göre)
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
        
        # FİLM TÜRLERİ (HTML'den aldığımız kategoriler)
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
        
        # PLATFORMLAR (Düzenlenmiş hali)
        self.platformlar = {
            'netflix': {'name': 'NETFLİX', 'url': '/koleksiyon/netflix', 'has_year': False},
            'exxen': {'name': 'EXXEN', 'url': '/koleksiyon/exxen', 'has_year': False},
            'blutv': {'name': 'BluTV', 'url': '/koleksiyon/blutv', 'has_year': False},
            'disney': {'name': 'Disney+', 'url': '/koleksiyon/disney', 'has_year': False},
            'amazon-prime': {'name': 'Amazon Prime', 'url': '/koleksiyon/amazon-prime', 'has_year': False},
            'tod-bein': {'name': 'TOD', 'url': '/koleksiyon/tod-bein', 'has_year': False},
            'gain': {'name': 'GAIN', 'url': '/koleksiyon/gain', 'has_year': False},
            'mubi': {'name': 'MUBI', 'url': '/tur/mubi', 'has_year': True}
        }

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

    def get_dizi_title_and_logo(self, dizi_url):
        """Dizi sayfasından gerçek başlığı ve logosunu al"""
        try:
            r = self.scraper.get(dizi_url, timeout=30)
            soup = BeautifulSoup(r.content, 'html.parser')
            
            title_tag = soup.find('h5')
            title = title_tag.text.strip() if title_tag else "Bilinmeyen Dizi"
            
            logo_div = soup.find('div', class_='cover')
            if logo_div and 'style' in logo_div.attrs:
                style = logo_div['style']
                logo_match = re.search(r'url\((https://[^)]+)\)', style)
                logo = logo_match.group(1) if logo_match else ""
            else:
                logo = ""
            
            return title, logo
        except Exception as e:
            print(f"    ❌ Başlık/logo alınamadı {dizi_url}: {e}")
            return "Bilinmeyen Dizi", ""

    def get_episodes_from_dizi_page(self, dizi_url, tur_name, platform_name=None):
        """Dizi sayfasından tüm bölümleri çek"""
        print(f"    📺 Bölümler taranıyor: {dizi_url}")
        
        try:
            r = self.scraper.get(dizi_url, timeout=30)
            soup = BeautifulSoup(r.content, 'html.parser')
            
            dizi_title, dizi_logo = self.get_dizi_title_and_logo(dizi_url)
            
            episodes = []
            episode_items = soup.find_all('div', class_='episode-item')
            
            for item in episode_items:
                link = item.find('a')
                if link and 'href' in link.attrs:
                    episode_url = urljoin(self.base_url, link['href'])
                    
                    name_div = item.find('div', class_='name')
                    episode_name = name_div.text.strip() if name_div else ""
                    
                    season_match = re.search(r'/sezon-(\d+)', episode_url)
                    episode_match = re.search(r'/bolum-(\d+)', episode_url)
                    
                    if season_match and episode_match:
                        season = season_match.group(1)
                        episode = episode_match.group(1)
                        
                        display_name = f"{dizi_title} S{season.zfill(2)}E{episode.zfill(2)}"
                        if episode_name and episode_name != f"{episode}. Bölüm":
                            display_name = f"{dizi_title} S{season.zfill(2)}E{episode.zfill(2)} - {episode_name}"
                        
                        clean_title = re.sub(r'[^\w\s-]', '', dizi_title.lower()).replace(' ', '_')
                        tvg_id = f"{clean_title}_s{season.zfill(2)}e{episode.zfill(2)}"
                        
                        if platform_name:
                            group_title = f"{platform_name}"
                        else:
                            group_title = f"Dizi - {tur_name.upper()}"
                        
                        episodes.append({
                            'url': episode_url,
                            'title': display_name,
                            'tvg_id': tvg_id,
                            'logo': dizi_logo,
                            'group_title': group_title,
                            'type': 'dizi'
                        })
            
            return episodes
            
        except Exception as e:
            print(f"    ❌ Bölüm çekme hatası {dizi_url}: {e}")
            return []

    def crawl_dizi_category(self, tur_name, tur_id):
        """Bir dizi kategorisindeki tüm dizileri ve bölümlerini çek"""
        print(f"\n📂 DİZİ KATEGORİSİ: {tur_name.upper()} (ID: {tur_id})")
        
        base_url = f"{self.base_url}/diziler?kelime=&durum=&tur={tur_id}&type=&siralama="
        page = 1
        all_episodes = []
        
        while True:
            url = f"{base_url}&sayfa={page}"
            print(f"   📄 Sayfa {page}")
            
            try:
                r = self.scraper.get(url, timeout=30)
                soup = BeautifulSoup(r.content, 'html.parser')
                
                # Sayfada içerik var mı kontrol et
                no_results = soup.find('div', class_='no-results')
                if no_results:
                    print(f"   ⚠️  {tur_name} kategorisi için daha fazla içerik bulunamadı")
                    break
                
                dizi_links = []
                items = soup.select('article.type2 ul li a')
                
                for item in items:
                    href = item.get('href', '')
                    if href and '/dizi/' in href and '/sezon-' not in href:
                        full_url = urljoin(self.base_url, href)
                        if full_url not in dizi_links:
                            dizi_links.append(full_url)
                
                print(f"   ✅ Sayfa {page}: {len(dizi_links)} dizi bulundu")
                
                if not dizi_links:
                    break
                
                for dizi_url in dizi_links:
                    episodes = self.get_episodes_from_dizi_page(dizi_url, tur_name)
                    all_episodes.extend(episodes)
                    time.sleep(0.3)
                
                next_page = soup.select_one('a[rel="next"]')
                if not next_page:
                    break
                    
                page += 1
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ Sayfa {page} hatası: {e}")
                break
        
        print(f"   📊 Toplam bölüm: {len(all_episodes)}")
        return all_episodes

    def crawl_film_category(self, tur_name, tur_slug):
        """Bir film kategorisindeki tüm filmleri çek"""
        print(f"\n🎬 FİLM KATEGORİSİ: {tur_name.upper()} (Slug: {tur_slug})")
        
        all_films = []
        
        # Her yıl için ayrı ayrı tarama yap
        for year in self.years:
            print(f"   📅 Yıl: {year}")
            
            encoded_genre = quote(f'/tur/{tur_slug}?', safe='')
            base_url = f"{self.base_url}/tur/{tur_slug}?genre={encoded_genre}&yil={year}&kelime="
            page = 1
            year_films_count = 0
            
            while True:
                url = f"{base_url}&sayfa={page}"
                print(f"      📄 Sayfa {page}")
                
                try:
                    r = self.scraper.get(url, timeout=30)
                    soup = BeautifulSoup(r.content, 'html.parser')
                    
                    # Sayfada içerik var mı kontrol et
                    no_results = soup.find('div', class_='no-results')
                    if no_results:
                        if page == 1:
                            print(f"      ⚠️  {year} yılı için içerik bulunamadı")
                        break
                    
                    film_links = []
                    items = soup.select('article.type2 ul li a')
                    
                    for item in items:
                        href = item.get('href', '')
                        if href and '/film/' in href:
                            full_url = urljoin(self.base_url, href)
                            if full_url not in film_links:
                                film_links.append(full_url)
                    
                    print(f"      ✅ {len(film_links)} film bulundu")
                    
                    if not film_links:
                        break
                    
                    for film_url in film_links:
                        try:
                            r2 = self.scraper.get(film_url, timeout=30)
                            soup2 = BeautifulSoup(r2.content, 'html.parser')
                            
                            # Film başlığını al
                            title_tag = soup2.find('title')
                            if title_tag:
                                title_text = title_tag.text
                                film_title = title_text.split(' İzle')[0].split('|')[0].strip()
                            else:
                                film_title = "Bilinmeyen Film"
                            
                            # Logoyu al
                            meta_image = soup2.find('meta', property='og:image')
                            logo = meta_image['content'] if meta_image else ""
                            
                            # tvg-id oluştur
                            clean_title = re.sub(r'[^\w\s-]', '', film_title.lower()).replace(' ', '_')
                            tvg_id = f"{clean_title}_{year}"
                            
                            all_films.append({
                                'url': film_url,
                                'title': f"{film_title} ({year})",
                                'tvg_id': tvg_id,
                                'logo': logo,
                                'group_title': f"Film - {tur_name.upper()}",
                                'type': 'film'
                            })
                            year_films_count += 1
                            
                        except Exception as e:
                            print(f"         ❌ Film bilgisi alınamadı {film_url}: {e}")
                    
                    # Sonraki sayfa var mı kontrol et
                    next_page = soup.select_one('a[rel="next"]')
                    if not next_page:
                        break
                        
                    page += 1
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"      ❌ {year} - Sayfa {page} hatası: {e}")
                    break
            
            print(f"      📊 {year} yılı: {year_films_count} film")
            
            # Her yıl arasında bekle
            time.sleep(0.5)
        
        print(f"   📊 Toplam film: {len(all_films)}")
        return all_films

    def crawl_platform(self, platform_key, platform_info):
        """Bir platformdaki tüm içerikleri çek"""
        platform_name = platform_info['name']
        platform_url = platform_info['url']
        has_year = platform_info['has_year']
        
        print(f"\n🏢 PLATFORM: {platform_name}")
        
        all_content = []
        
        # Yıl parametresi olan platformlar için yıl döngüsü
        if has_year:
            years_to_crawl = self.years
        else:
            years_to_crawl = [None]  # Yıl parametresi yoksa tek sefer çek
        
        for year in years_to_crawl:
            if year:
                print(f"   📅 Yıl: {year}")
            
            # MUBI için özel URL yapısı
            if platform_key == 'mubi' and year:
                encoded_genre = quote(f'/tur/mubi?', safe='')
                base_url = f"{self.base_url}{platform_url}?genre={encoded_genre}&yil={year}&kelime="
            # Exxen için özel URL yapısı
            elif platform_key == 'exxen':
                base_url = f"{self.base_url}{platform_url}?kelime=&durum=&tur=&siralama="
            else:
                base_url = f"{self.base_url}{platform_url}"
            
            page = 1
            year_content_count = 0
            
            while True:
                if platform_key == 'exxen' or (platform_key == 'mubi' and year):
                    url = f"{base_url}&sayfa={page}" if page > 1 else base_url
                else:
                    url = f"{base_url}?sayfa={page}" if page > 1 else base_url
                
                print(f"      📄 Sayfa {page}")
                
                try:
                    r = self.scraper.get(url, timeout=30)
                    soup = BeautifulSoup(r.content, 'html.parser')
                    
                    # Sayfada içerik var mı kontrol et
                    no_results = soup.find('div', class_='no-results')
                    if no_results:
                        if page == 1:
                            print(f"      ⚠️  İçerik bulunamadı")
                        break
                    
                    content_links = []
                    items = soup.select('article.type2 ul li a')
                    
                    for item in items:
                        href = item.get('href', '')
                        if href:
                            full_url = urljoin(self.base_url, href)
                            if full_url not in content_links:
                                content_links.append(full_url)
                    
                    print(f"      ✅ {len(content_links)} içerik bulundu")
                    
                    if not content_links:
                        break
                    
                    for content_url in content_links:
                        if '/dizi/' in content_url and '/sezon-' not in content_url:
                            episodes = self.get_episodes_from_dizi_page(content_url, platform_name, platform_name)
                            all_content.extend(episodes)
                            year_content_count += len(episodes)
                        elif '/film/' in content_url:
                            try:
                                r2 = self.scraper.get(content_url, timeout=30)
                                soup2 = BeautifulSoup(r2.content, 'html.parser')
                                
                                # Film başlığını al
                                title_tag = soup2.find('title')
                                if title_tag:
                                    title_text = title_tag.text
                                    film_title = title_text.split(' İzle')[0].split('|')[0].strip()
                                else:
                                    film_title = "Bilinmeyen Film"
                                
                                # Yılı belirle
                                film_year = year if year else "2024"
                                
                                # Logoyu al
                                meta_image = soup2.find('meta', property='og:image')
                                logo = meta_image['content'] if meta_image else ""
                                
                                clean_title = re.sub(r'[^\w\s-]', '', film_title.lower()).replace(' ', '_')
                                tvg_id = f"{clean_title}_{platform_key}_{film_year}"
                                
                                all_content.append({
                                    'url': content_url,
                                    'title': f"{film_title} ({film_year})",
                                    'tvg_id': tvg_id,
                                    'logo': logo,
                                    'group_title': f"{platform_name}",
                                    'type': 'film'
                                })
                                year_content_count += 1
                                
                            except Exception as e:
                                print(f"         ❌ Film bilgisi alınamadı {content_url}: {e}")
                        
                        time.sleep(0.3)
                    
                    # Sonraki sayfa var mı kontrol et
                    next_page = soup.select_one('a[rel="next"]')
                    if not next_page:
                        break
                        
                    page += 1
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"      ❌ Sayfa {page} hatası: {e}")
                    break
            
            if year:
                print(f"      📊 {year} yılı: {year_content_count} içerik")
            else:
                print(f"      📊 Toplam: {year_content_count} içerik")
            
            # Her yıl arasında bekle
            if has_year:
                time.sleep(0.5)
        
        print(f"   📊 Platform toplam: {len(all_content)} içerik")
        return all_content

    def run(self):
        """Ana çalıştırma fonksiyonu"""
        print("=" * 60)
        print("🚀 DÜZGÜN DİZİPAL SCRAPER BAŞLIYOR (TAM SÜRÜM)")
        print("=" * 60)
        
        self.content_data = []
        
        # 1. DİZİ KATEGORİLERİNİ ÇEK (tüm kategoriler)
        print("\n" + "=" * 60)
        print("📺 DİZİ KATEGORİLERİ ÇEKİLİYOR")
        print("=" * 60)
        
        for tur_name, tur_id in self.dizi_turleri.items():
            episodes = self.crawl_dizi_category(tur_name, tur_id)
            self.content_data.extend(episodes)
            time.sleep(1)
        
        # 2. FİLM KATEGORİLERİNİ ÇEK (tüm kategoriler)
        print("\n" + "=" * 60)
        print("🎬 FİLM KATEGORİLERİ ÇEKİLİYOR")
        print("=" * 60)
        
        for tur_name, tur_slug in self.film_turleri.items():
            films = self.crawl_film_category(tur_name, tur_slug)
            self.content_data.extend(films)
            time.sleep(1)
        
        # 3. PLATFORMLARI ÇEK (tüm platformlar)
        print("\n" + "=" * 60)
        print("🏢 PLATFORMLAR ÇEKİLİYOR")
        print("=" * 60)
        
        for platform_key, platform_info in self.platformlar.items():
            platform_content = self.crawl_platform(platform_key, platform_info)
            self.content_data.extend(platform_content)
            time.sleep(1)
        
        # 4. TEKİLLEŞTİRME
        print("\n" + "=" * 60)
        print("🧹 TEKİLLEŞTİRME YAPILIYOR")
        print("=" * 60)
        
        unique_data = []
        seen_urls = set()
        
        for item in self.content_data:
            if item['url'] not in seen_urls:
                seen_urls.add(item['url'])
                unique_data.append(item)
        
        print(f"   Çift kayıtlar kaldırıldı: {len(self.content_data)} -> {len(unique_data)}")
        self.content_data = unique_data
        
        # 5. M3U DOSYASINI OLUŞTUR
        print("\n" + "=" * 60)
        print("📝 M3U DOSYASI OLUŞTURULUYOR")
        print("=" * 60)
        
        m3u_content = self.generate_m3u()
        
        # 6. DOSYAYA YAZ
        with open('dizipal.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        
        print("\n" + "=" * 60)
        print(f"✅ BAŞARIYLA TAMAMLANDI!")
        print(f"📁 Çıktı: dizipal.m3u ({len(m3u_content.splitlines())} satır)")
        
        # İstatistikler
        print("\n📊 İSTATİSTİKLER:")
        dizi_count = sum(1 for item in self.content_data if item['type'] == 'dizi')
        film_count = sum(1 for item in self.content_data if item['type'] == 'film')
        print(f"   Toplam Dizi Bölümü: {dizi_count}")
        print(f"   Toplam Film: {film_count}")
        print(f"   GENEL TOPLAM: {len(self.content_data)}")
        print("=" * 60)

    def generate_m3u(self):
        """Düzgün formatlı M3U içeriği oluştur"""
        m3u_lines = ['#EXTM3U x-tvg-url="https://github.com/botallen/epg/releases/download/latest/epg.xml"']
        
        # İçerikleri gruplara ayır
        grouped_content = {}
        for item in self.content_data:
            group = item['group_title']
            if group not in grouped_content:
                grouped_content[group] = []
            grouped_content[group].append(item)
        
        # Her grup için M3U satırlarını oluştur
        for group_title, items in sorted(grouped_content.items()):
            m3u_lines.append(f'\n# GROUP-TITLE: "{group_title}"')
            
            for item in sorted(items, key=lambda x: x['title']):
                m3u_lines.append(f'#EXTINF:-1 tvg-id="{item["tvg_id"]}" tvg-name="{item["title"]}" tvg-logo="{item["logo"]}" group-title="{group_title}", {item["title"]}')
                m3u_lines.append(item['url'])
        
        return '\n'.join(m3u_lines)

if __name__ == "__main__":
    scraper = DizipalScraper()
    scraper.run()

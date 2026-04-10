import time
import re
import os
import datetime
import math
import random
import pytz
import pandas as pd
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from dotenv import load_dotenv
from sqlalchemy import create_engine
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    InvalidSessionIdException,
    WebDriverException,
    TimeoutException
)

load_dotenv()
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")

class ScraperZap:

    def __init__(self, transacao='aluguel', tipo='apartamentos', local='rj+rio-de-janeiro',zona=None, precomin = 0, precomax = 999999999):
        self.base_url = 'https://www.zapimoveis.com.br'
        self.transacao = transacao
        self.tipo = tipo
        self.local = local
        self.zona = zona
        self.precomin = precomin
        self.precomax = precomax

        self.timestamp_now = datetime.datetime.now(
            tz=pytz.timezone('America/Sao_Paulo')
        )

        self.driver = self._get_driver()
        self.engine = create_engine(
        f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}",
        pool_pre_ping=True
        )
        print(f"[*] Initialized Scraper for: {tipo} | {transacao} | {local} | {zona} | {precomin} - {precomax}")

    # =========================
    # LOGGER
    # =========================

    def execution(self, total, saved, et):

        df= {
            'tipo': self.tipo,
            'transacao': self.transacao,
            'local': self.local,
            'zona': self.zona,
            'preco_min': self.precomin,
            'preco_max': self.precomax,
            'total_listings': total,
            'saved_listings': saved,
            'elapsed_time': et
        }

        return df
    
    # =========================
    # DRIVER
    # =========================

    def _get_driver(self, headless=False):
        options = uc.ChromeOptions()

        if headless:
            options.add_argument('--headless=new')

        width = random.randint(1200, 1920)
        height = random.randint(800, 1080)
        options.add_argument(f'--window-size={width},{height}')

        options.add_argument('--disable-blink-features=AutomationControlled')

        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument("--start-minimized")

        prefs = {
            "profile.managed_default_content_settings.images": 2
        }
        options.add_experimental_option("prefs", prefs)

        driver = uc.Chrome(
            options=options,
            version_main=146,
            use_subprocess=True
        )

        driver.minimize_window()

        time.sleep(random.uniform(1, 3))

        return driver
    
    def safe_get(self, url, retries=3):
        for attempt in range(retries):
            try:
                self.driver.get(url)
                return

            except WebDriverException as e:
                if "ERR_NAME_NOT_RESOLVED" in str(e):
                    print(f"[!] DNS error (attempt {attempt+1})")

                    time.sleep(random.uniform(2, 5))

                    try:
                        self.safe_quit()
                    except:
                        pass
                    self.driver = self._get_driver()

                else:
                    raise

        raise Exception("Failed to load page after retries")

    def safe_quit(self):
        try:
            if self.driver:
                self.driver.quit()
        except Exception as e:
            print(f"[!] Ignored quit error: {e}")
        finally:
            self.driver = None

    # =========================
    # PAGINATION
    # =========================

    def get_total_listings(self):
        for _ in range(5):
            try:

                url = f'{self.base_url}/{self.transacao}/apartamentos/{self.local}+{self.zona}/?pagina=1&tipos={self.tipo}&precoMinimo={self.precomin}&precoMaximo={self.precomax}&ordem=LOWEST_PRICE'

                if self.zona == None:
                    url = f'{self.base_url}/{self.transacao}/apartamentos/{self.local}/?pagina=1&tipos={self.tipo}&precoMinimo={self.precomin}&precoMaximo={self.precomax}&ordem=LOWEST_PRICE'

                self.safe_get(url)

                wait = WebDriverWait(self.driver, 10)
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

                for _ in range(3):
                    try:
                        el = self.driver.find_element(By.TAG_NAME, "h1")
                        text = el.text
                        break
                    except StaleElementReferenceException:
                        time.sleep(1)
                else:
                    raise Exception("Failed to get stable element")

                numbers = re.findall(r'\d+', text.replace('.', '').replace(',', ''))
                total = int(numbers[0]) if numbers else 0

                if total == 0:
                    print("[!] No listings found")
                    return 0
            
                print(f"[*] Found {total} listings")
                return total

            except InvalidSessionIdException:
                self.safe_quit()
                print("[!] Driver died, restarting in 30 seconds...")
                time.sleep(30)
                self.driver = self._get_driver()

        raise Exception("Failed after retries")
    
    # =========================
    # FETCH
    # =========================
    
 
    def fetch_page(self, page):
        for _ in range(5):
            try:

                url = f'{self.base_url}/{self.transacao}/apartamentos/{self.local}+{self.zona}/?pagina={page}&tipos={self.tipo}&precoMinimo={self.precomin}&precoMaximo={self.precomax}&ordem=LOWEST_PRICE'

                if self.zona == None:
                    url = f'{self.base_url}/{self.transacao}/apartamentos/{self.local}/?pagina={page}&tipos={self.tipo}&precoMinimo={self.precomin}&precoMaximo={self.precomax}&ordem=LOWEST_PRICE'

                self.safe_get(url)

                wait = WebDriverWait(self.driver, 15)

                try:
                    wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-cy='rp-property-cd']"))
                    )
                except TimeoutException:
                    print("[!] No listings on this page")
                    return None

                time.sleep(random.uniform(0.5, 2))

                for i in range(1, 5):
                    self.driver.execute_script(
                        f"window.scrollTo(0, document.body.scrollHeight * {i/4});"
                    )
                    time.sleep(0.25)

                return self.driver.page_source

            except InvalidSessionIdException:
                self.safe_quit()
                print("[!] Driver died, restarting in 30 seconds...")
                time.sleep(30)
                self.driver = self._get_driver()

        raise Exception("Failed after retries")
    
    # =========================
    # PARSE
    # =========================

    def parse_page(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.find_all(True, {"data-cy": "rp-property-cd"})

        results = []

        for card in cards:
            try:
                link_tag = card.find('a')
                url = link_tag.get('href') if link_tag else None

                id_match = re.search(r'id-(\d+)', url or "")
                imo_id = id_match.group(1) if id_match else None

                if not imo_id:
                    continue

                descricao = self._get_text(card, 'h2', 'rp-cardProperty-location-txt')
                bairro, cidade = self. _extract_bairro_cidade(card)
                endereco = self._get_text(card, 'p', 'rp-cardProperty-street-txt')

                preco, periodo_aluguel = self._extract_price_and_period(card, 'rp-cardProperty-price-txt')

                condominio, iptu = self._extract_cond_iptu(card)


                results.append({
                    'id': imo_id,
                    'url': url,
                    'transacao': self.transacao,
                    'descricao': descricao,
                    'tipo': self.tipo,
                    'zona': self.zona,
                    'bairro': bairro,
                    'cidade': cidade,
                    'endereco': endereco,
                    'area': self._extract_feature(card, 'rp-cardProperty-propertyArea-txt'),
                    'quartos': self._extract_feature(card, 'rp-cardProperty-bedroomQuantity-txt'),
                    'banheiros': self._extract_feature(card, 'rp-cardProperty-bathroomQuantity-txt'),
                    'garagens': self._extract_feature(card, 'rp-cardProperty-parkingSpacesQuantity-txt'),
                    'preco': preco,
                    'periodo_aluguel': periodo_aluguel,
                    'condominio': condominio,
                    'iptu': iptu
                })

            except Exception as e:
                print(f"[!] Parse error: {e}")
                continue

        return results

    # =========================
    # HELPERS
    # =========================

    def _get_text(self, card, tag, data_cy):
        el = card.find(tag, {"data-cy": data_cy})
        return el.text.strip() if el else None
        
    def _extract_bairro_cidade(self, card):
        try:
            h2 = card.find('h2', {"data-cy": "rp-cardProperty-location-txt"})
            if not h2:
                return None, None

            # Remove span (description)
            span = h2.find('span')
            if span:
                span.extract()

            # Now only location remains
            text = h2.get_text(strip=True)

            # Example: "Três Poços, Volta Redonda"
            parts = [p.strip() for p in text.split(",")]

            bairro = parts[0] if len(parts) > 0 else None
            cidade = parts[1] if len(parts) > 1 else None

            return bairro, cidade

        except:
            return None, None
        
    def _extract_price_and_period(self, card, data_cy):
        el = card.find('div', {"data-cy": data_cy})
        if not el:
            return 0.0, None

        text = el.get_text(" ", strip=True).lower()

        # price
        match = re.search(r'r\$\s*([\d\.]+)', text)
        price = float(match.group(1).replace('.', '')) if match else 0.0

        # period
        if 'mês' in text:
            period = 'mensal'
        elif 'dia' in text:
            period = 'diario'
        else:
            period = 'unknown'

        return price, period
    
    def _extract_cond_iptu(self, card):
        try:
            text = card.get_text(" ", strip=True).lower()

            cond = 0.0
            iptu = 0.0

            # Condominio
            cond_match = re.search(r'cond\.\s*r\$\s*([\d\.]+)', text)
            if cond_match:
                cond = float(cond_match.group(1).replace('.', ''))

            # IPTU
            iptu_match = re.search(r'iptu\s*r\$\s*([\d\.]+)', text)
            if iptu_match:
                iptu = float(iptu_match.group(1).replace('.', ''))

            return cond, iptu

        except:
            return 0.0, 0.0
        
    def _extract_feature(self, card, data_cy):
        try:
            el = card.find('li', {"data-cy": data_cy})
            if not el:
                return 0.0

            text = el.get_text(strip=True)

            # extract number from text (e.g. "106 m²" or "3")
            match = re.search(r'\d+', text)
            return float(match.group()) if match else 0.0

        except:
            return 0.0
            
    def _p98_price(self, listings):
        prices = sorted(
            item["preco"] for item in listings 
            if item.get("preco") is not None
        )

        if not prices:
            return 0

        index = int(0.98 * len(prices)) - 1
        return prices[max(index, 0)]

    # =========================
    # TRANSFORM
    # =========================

    def build_dataframe(self, data, time):
        df = pd.DataFrame(data)

        df['data'] = time.strftime("%Y-%m-%d %H:%M:%S")
        df['ano'] = time.strftime("%Y")
        df['mes'] = time.strftime("%m")
        df['dia'] = time.strftime("%d")

        return df

    # =========================
    # DB
    # =========================

    def save_to_db(self, df, table_name='dados_imoveis_raw'):

        if df.empty:
            print("[!] Empty dataframe, skipping save")
            return
        
        engine = self.engine
        
        df.to_sql(
            table_name,
            engine,
            if_exists='append',
            index=False,
            chunksize=1000,
            method='multi'
        )

        engine.dispose()
        print("[V] Saved to DB")

    # =========================
    # PARQUET
    # =========================

    def save_parquet(self, df):
        path = os.path.join(os.getcwd(), 'data', 'bronze')
        os.makedirs(path, exist_ok=True)

        df.to_parquet(
            os.path.join(path, 'dados_imoveis_raw.parquet'),
            partition_cols=['ano', 'mes', 'dia'],
            index=False
        )

        print("[V] Saved parquet")

    # =========================
    # MAIN PIPELINE
    # =========================

    def run(self):

        remaning = 501

        while remaning > 500:

            start = datetime.datetime.now()
            remaning = self.get_total_listings()

            print(f"[*] Scrapping from {self.precomin} - {self.precomax}. {remaning} listings remaining | start: {start.strftime('%Y-%m-%d %H:%M:%S')}")
            all_data = []

            pages = min(math.ceil(remaning / 28), 50)

            for page in range(1, pages + 1):
                print(f"[*] Page {page}/{pages}")
                html = self.fetch_page(page)

                if html is None:
                    print("[*] No more pages — stopping pagination")
                    break

                parsed = self.parse_page(html)
                all_data.extend(parsed)

            saved = len(all_data)
            df = self.build_dataframe(all_data,start)

            self.save_to_db(df)
            self.save_parquet(df)

            end = datetime.datetime.now()
            et = (end - start).total_seconds()

            log = self.execution(remaning,saved,et)
            df_log = self.build_dataframe([log],start)
            self.save_to_db(df_log, table_name='execution_logs_raw')

            max_price = self._p98_price(all_data)

            if max_price <= self.precomin:
                max_price = max_price*1.02

            self.precomin = int(max_price)

        self.safe_quit()
        
        return df

if __name__ == "__main__":
    scraper = ScraperZap(local='rj+rio-de-janeiro')
    df = scraper.run()




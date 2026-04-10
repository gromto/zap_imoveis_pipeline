import os
import time
from sqlalchemy import create_engine
from dotenv import load_dotenv
from psycopg2.extras import execute_values
import pandas as pd
from geopy.geocoders import Nominatim
import googlemaps
import random

load_dotenv()
api_key = os.getenv("GOOGLE_MAPS_API_KEY")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")


class GeoCoder:

    # =========================
    # Geocoding
    # =========================

    def __init__(self):
        self.geolocator = Nominatim(user_agent="rj-analise")
        key = api_key

        if not key:
            raise ValueError("GOOGLE_MAPS_API_KEY not found in environment")
        
        self.gmaps = googlemaps.Client(key=key)
        self.engine = create_engine(
        f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}",
        pool_pre_ping=True
        )
        self.cache = {}

    def get_addresses(self):
        query = """
            SELECT DISTINCT
            i.cidade,
            i.bairro,
            i.endereco,
            g.latitude,
            g.longitude
            FROM stg_imoveis i

            LEFT JOIN enderecos_geocodados g ON i.cidade = g.cidade AND i.bairro = g.bairro AND i.endereco = g.endereco

            WHERE g.source = 'nominatim'
        """
        return pd.read_sql(query, self.engine)
    
    def geocode_address(self, address, retries=3):

        if address in self.cache:
            return self.cache[address]

        # # =====================
        # # 1. NOMINATIM
        # # =====================
        for i in range(retries):
            try:
                location = self.geolocator.geocode(address, timeout=10)

                if location:
                    result = (location.latitude, location.longitude, "nominatim")
                    self.cache[address] = result
                    return result
                
                print(f"[Nominatim retry {i}/{retries}]")

            except Exception as e:
                print(f"[Nominatim error] - {type(e).__name__}: {e}")

            time.sleep(1 + random.uniform(0, 0.3))

        # =====================
        # 2. GOOGLE (FALLBACK)
        # =====================
        for i in range(retries):
            try:
                lat, lon = self.geocode_google(address)

                if lat and lon:
                    result = (lat, lon, "google")
                    self.cache[address] = result
                    return result
                
            except Exception:
                print(f"[Google retry {i}/{retries}]")
                time.sleep(1 * i+1)

        return None, None, 'failed'
    
    def geocode_google(self, address):
        try:
            result = self.gmaps.geocode(address)

            if result:
                location = result[0]["geometry"]["location"]
                return location["lat"], location["lng"]

        except Exception as e:
            print(f"[Google ERROR] {e}")

        return None, None
    
    def get_coordinates(self, df):
        results = []

        for i, (_, row) in enumerate(df.iterrows()):

            address = f"{row['endereco']}, {row['bairro']}, {row['cidade']}, Brazil"

            lat, lon, source = self.geocode_address(address)

            print(f"{i}: {row['endereco']}, {row['bairro']}, {row['cidade']}, Brazil - Lat: {lat}, Lon: {lon} | Source: {source}")

            results.append({
                "cidade": row["cidade"],
                "bairro": row["bairro"],
                "endereco": row["endereco"],
                "latitude": lat,
                "longitude": lon,
                "source":source
            })

            if i % 200 == 0 and i > 0:
                self.save_to_db(pd.DataFrame(results))
                results = []

            time.sleep(random.uniform(0.010, 0.015))

        if results:
            self.save_to_db(pd.DataFrame(results))

        return pd.DataFrame(results)
    
    # =========================
    # DB
    # =========================

    def save_to_db(self, df):
        if df.empty:
            return

        tuples = [
            (
                row.cidade,
                row.bairro,
                row.endereco,
                row.latitude,
                row.longitude,
                row.source
            )
            for _, row in df.iterrows()
        ]

        query = """
            INSERT INTO enderecos_geocodados
            (cidade, bairro, endereco, latitude, longitude, source)
            VALUES %s
            ON CONFLICT (cidade, bairro, endereco)
            DO UPDATE SET
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                source = EXCLUDED.source;
        """

        with self.engine.raw_connection() as conn:
            with conn.cursor() as cur:
                execute_values(cur, query, tuples)
            conn.commit()

if __name__ == "__main__":
   geocoder = GeoCoder()
   addresses = geocoder.get_addresses()
   geocoder.get_coordinates(addresses)


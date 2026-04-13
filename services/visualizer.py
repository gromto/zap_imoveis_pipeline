import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import json
from pathlib import Path
import pandas as pd

load_dotenv()
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")


class VisualMap:

    def __init__(self):
        self.engine = create_engine(
        f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}",
        pool_pre_ping=True
        )

    def generate_geojson(self):

        sql_path = Path(__file__).parent.parent / "sql" / "features_table_creation.sql"

        with open(sql_path, encoding="utf-8") as f:
            sql = f.read()
            with self.engine.begin() as conn:
                conn.exec_driver_sql(sql)

        query = """
            SELECT jsonb_build_object(
            'type', 'FeatureCollection',
            'features', jsonb_agg(feature)
        )
        FROM (
            SELECT jsonb_build_object(
                'type', 'Feature',
                'geometry', ST_AsGeoJSON(geom)::jsonb,
                'properties', jsonb_build_object(
                    'n', TO_CHAR(n_listings, 'FM999G999G999'),

                    'top_endereco', top_endereco,
                    'top_bairro', top_bairro,

                    'median_price', TO_CHAR(median_price, 'FM999G999G999'),
                    'median_area', TO_CHAR(median_area, 'FM999G999'),

                    'avg_banheiros', TO_CHAR(avg_banheiros, '0D9'),
                    'avg_quartos', TO_CHAR(avg_quartos, '0D9'),
                    'avg_garagens', TO_CHAR(avg_garagens, '0D9'),

                    -- numérico (cor)
                    'value', avg_price_m2,

                    -- formatado (tooltip)
                    'avg_price_m2',  TO_CHAR(avg_price_m2, 'FM999G999G999')
                )
            ) AS feature
            FROM grid_stats
        ) t;
        """

        with self.engine.connect() as conn:
            geojson = conn.execute(text(query)).scalar()

        if not geojson or not geojson.get("features"):
            raise ValueError("GeoJSON vazio")

        return geojson
    
    def get_df(self):
        query = """
            SELECT endereco, bairro, zona_corrigida, total_anuncios, avg_preco_m2, median_preco, median_area, avg_quartos, avg_banheiros, avg_garagens
            FROM agg_ruas_venda
            WHERE total_anuncios >= 5
        """

        with self.engine.connect() as conn:
            df = pd.read_sql(text(query), conn)

        if df.empty:
            raise ValueError("DataFrame vazio")

        return df


if __name__ == "__main__":
    visual = VisualMap()
    geojson = visual.generate_geojson()
    with open("streamlit/data/data.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson, f)
    datajson = visual.get_df()
    with open("streamlit/data/data.json", "w", encoding="utf-8") as f:
        json.dump(datajson.to_dict(orient="records"), f)
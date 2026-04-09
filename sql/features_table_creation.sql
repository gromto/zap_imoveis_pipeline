-- =========================
-- EXTENSÃO
-- =========================
CREATE EXTENSION IF NOT EXISTS postgis;

-- =========================
-- ÍNDICES BASE
-- =========================
DROP INDEX IF EXISTS idx_imoveis_filtro;

CREATE INDEX idx_imoveis_filtro
ON stg_imoveis (cidade, bairro, endereco, tipo_clean, transacao);

-- =========================
-- 1. JOIN + GEO
-- =========================
DROP TABLE IF EXISTS imoveis_geo;

CREATE TABLE imoveis_geo AS
SELECT
    i.*,
    g.latitude,
    g.longitude
FROM stg_imoveis i
JOIN (
    SELECT DISTINCT ON (cidade, bairro, endereco)
           cidade, bairro, endereco, latitude, longitude
    FROM enderecos_geocodados
) g
  ON i.cidade = g.cidade
 AND i.bairro = g.bairro
 AND i.endereco = g.endereco
WHERE
    g.latitude IS NOT NULL
    AND i.transacao = 'venda'
    AND i.preco BETWEEN 50000 AND 5000000
    AND i.area BETWEEN 15 AND 2000
    AND latitude < -22.6
    AND longitude > -44;

-- =========================
-- GEOMETRIA (WGS84 + UTM)
-- =========================

ALTER TABLE imoveis_geo
ADD COLUMN geom geometry(Point, 4326);

UPDATE imoveis_geo
SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326);

CREATE INDEX idx_geom ON imoveis_geo USING GIST (geom);

ALTER TABLE imoveis_geo
ADD COLUMN geom_utm geometry(Point, 31983);

UPDATE imoveis_geo
SET geom_utm = ST_Transform(geom, 31983);

CREATE INDEX idx_geom_utm ON imoveis_geo USING GIST (geom_utm);

-- =========================
-- HEX GRID (UTM)
-- =========================
DROP TABLE IF EXISTS grid;

WITH bbox AS (
  SELECT ST_Envelope(ST_Collect(geom_utm)) AS geom
  FROM imoveis_geo
)
SELECT (ST_HexagonGrid(250, geom)).*
INTO grid
FROM bbox;

CREATE INDEX idx_grid ON grid USING GIST (geom);

-- =========================
-- AGREGAÇÃO
-- =========================
DROP TABLE IF EXISTS grid_stats;

CREATE TABLE grid_stats AS
WITH base AS (
  SELECT
    g.geom AS geom_utm,
    i.preco,
    i.area,
    i.banheiros,
    i.quartos,
    i.garagens,
    i.endereco,
    i.bairro
  FROM grid g
  JOIN imoveis_geo i
    ON g.geom && i.geom_utm
   AND ST_Contains(g.geom, i.geom_utm)
),

-- moda consistente (endereco + bairro)
ranked AS (
  SELECT
    geom_utm,
    endereco,
    bairro,
    COUNT(*) AS cnt,
    ROW_NUMBER() OVER (
      PARTITION BY geom_utm
      ORDER BY COUNT(*) DESC
    ) AS rn
  FROM base
  GROUP BY geom_utm, endereco, bairro
),

agg AS (
  SELECT
    geom_utm,
    COUNT(*) AS n_listings,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY preco) AS median_price,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY area) AS median_area,
    AVG(preco / NULLIF(area, 0)) AS avg_price_m2,
    AVG(banheiros) AS avg_banheiros,
    AVG(quartos) AS avg_quartos,
    AVG(garagens) AS avg_garagens
  FROM base
  GROUP BY geom_utm
  HAVING COUNT(*) >= 5
)

SELECT
  a.*,
  r.endereco AS top_endereco,
  r.bairro AS top_bairro
FROM agg a
LEFT JOIN ranked r
  ON a.geom_utm = r.geom_utm AND r.rn = 1;

-- =========================
-- CONVERTER PARA WGS84 (MAPA)
-- =========================

ALTER TABLE grid_stats
ADD COLUMN geom geometry(Polygon, 4326);

UPDATE grid_stats
SET geom = ST_Transform(geom_utm, 4326);

CREATE INDEX idx_grid_stats_geom ON grid_stats USING GIST (geom);
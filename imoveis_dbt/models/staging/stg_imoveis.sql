{{ config(materialized='table') }}

WITH deduplicated AS (
    SELECT *
    FROM (
        SELECT
            *,
            ROW_NUMBER() OVER (PARTITION BY id ORDER BY data DESC) AS rn
        FROM dados_imoveis_raw
        WHERE area <> 0
    ) t
    WHERE rn = 1
),

cleaned AS (
    SELECT
        *,
        CASE
            WHEN LOWER(descricao) LIKE '%apartamento%'
                OR LOWER(descricao) LIKE '%duplex%' 
                OR LOWER(descricao) LIKE '%triplex%' THEN 'apartamento'
            WHEN LOWER(descricao) LIKE '%casa%' 
                OR LOWER(descricao) LIKE '%térrea%' THEN 'casa'
            WHEN LOWER(descricao) LIKE '%cobertura%' THEN 'cobertura'
            WHEN LOWER(descricao) LIKE '%kitnet%' 
              OR LOWER(descricao) LIKE '%conjugado%' THEN 'kitnet'
            WHEN LOWER(descricao) LIKE '%studio%' 
              OR LOWER(descricao) LIKE '%imóvel%' THEN 'studio'
            WHEN LOWER(descricao) LIKE '%casa de condomínio%' THEN 'casa de condominio'
            WHEN LOWER(descricao) LIKE '%casa de vila%' THEN 'casa de vila'
            WHEN LOWER(descricao) LIKE '%sobrado%' THEN 'sobrado'
            WHEN LOWER(descricao) LIKE '%flat%' THEN 'flat'
            WHEN LOWER(descricao) LIKE '%loft%' THEN 'loft'
            WHEN LOWER(descricao) LIKE '%lote%' 
              OR LOWER(descricao) LIKE '%terreno%' THEN 'lote/terreno'
            WHEN LOWER(descricao) LIKE '%fazenda%' 
              OR LOWER(descricao) LIKE '%sítio%' 
              OR LOWER(descricao) LIKE '%sitio%' 
              OR LOWER(descricao) LIKE '%chácara%' 
              OR LOWER(descricao) LIKE '%chacara%' THEN 'fazenda/sítio/chacara'
            ELSE 'outros'
        END AS tipo_clean,
        preco / area AS preco_m2
    FROM deduplicated
    WHERE cidade = 'Rio de Janeiro'
    AND endereco <> ''
    AND preco < 100000000
),

percentiles AS (
    SELECT
        bairro,
        transacao,

        -- price
        PERCENTILE_CONT(0.01) WITHIN GROUP (ORDER BY preco) AS p01_preco,
        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY preco) AS p99_preco,

        -- area
        PERCENTILE_CONT(0.01) WITHIN GROUP (ORDER BY area) AS p01_area,
        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY area) AS p99_area,

        COUNT(*) as n
    FROM cleaned
    GROUP BY bairro, transacao
),

filtered AS (
    SELECT c.*
    FROM cleaned c
    JOIN percentiles p 
        ON c.bairro = p.bairro
       AND c.transacao = p.transacao
    WHERE c.preco BETWEEN p.p01_preco AND p.p99_preco
      AND c.area  BETWEEN p.p01_area  AND p.p99_area
)

SELECT *
FROM filtered
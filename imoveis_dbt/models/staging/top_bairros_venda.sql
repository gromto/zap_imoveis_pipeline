SELECT  bairro
        ,zona_corrigida
       ,COUNT(*)       AS total_anuncios
       ,AVG(preco_m2)  AS avg_preco_m2
       ,PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY preco_m2) AS median_preco_m2
       ,AVG(preco)     AS avg_preco
       ,PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY preco) AS median_preco
       ,AVG(area)      AS avg_area
       ,PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY area) AS median_area
       ,AVG(quartos)   AS avg_quartos
       ,AVG(banheiros) AS avg_banheiros
       ,AVG(garagens)  AS avg_garagens

FROM {{ref('stg_imoveis')}}

WHERE bairro IS NOT NULL AND transacao = 'venda'

GROUP BY bairro, zona_corrigida

ORDER BY avg_preco_m2 DESC
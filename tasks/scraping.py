from prefect import task, get_run_logger
from services.scraper import ScraperZap

@task(retries=2, retry_delay_seconds=30)
def scrape_data():
    logger = get_run_logger()

    for zona in ['zona-sul','zona-norte','zona-oeste','zona-central']:
        for transacao in ['venda', 'aluguel']:

            scraper = ScraperZap(
                transacao=f"{transacao}",
                local="rj+rio-de-janeiro",
                zona=f"{zona}",
                tipo="condominio_residencial," \
                "apartamento_residencial," \
                "studio_residencial," \
                "kitnet_residencial," \
                "casa_residencial," \
                "casa-vila_residencial," \
                "cobertura_residencial," \
                "flat_residencial," \
                "loft_residencial," \
                "lote-terreno_residencial," \
                "sobrado_residencial," \
                "granja_residencial"
            )

            df = scraper.run()

            logger.info(f"Scraped {len(df)} rows")

    return 
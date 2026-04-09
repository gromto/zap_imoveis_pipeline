from prefect import task, get_run_logger
from services.geocoder import GeoCoder

@task(retries=3, retry_delay_seconds=10)
def geocode_data():
    logger = get_run_logger()

    geocoder = GeoCoder()

    df = geocoder.get_addresses()
    logger.info(f"{len(df)} addresses to process")

    geocoder.get_coordinates(df)

    logger.info("Geocoding completed")
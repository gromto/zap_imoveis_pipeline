from prefect import flow

from tasks.scraping import scrape_data
from tasks.geocoding import geocode_data
from tasks.visualize import generate_map

@flow(name="real-estate-pipeline")
def real_estate_pipeline():

    scrape = scrape_data()

    geocode = geocode_data(wait_for=[scrape])

    generate_map(wait_for=[geocode])


if __name__ == "__main__":
    real_estate_pipeline()
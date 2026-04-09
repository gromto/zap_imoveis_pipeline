from prefect import flow

from tasks.geocoding import geocode_data
from tasks.visualize import generate_map

@flow(name="real-estate-heatmap")
def real_estate_heatmap():

    geocode = geocode_data()

    generate_map(wait_for=[geocode])


if __name__ == "__main__":
    real_estate_heatmap()
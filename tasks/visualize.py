from prefect import task, get_run_logger
from services.visualizer import VisualMap
import json 

@task
def generate_map():
    logger = get_run_logger()

    visual = VisualMap()
    geojson = visual.generate_geojson()

    with open("data.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson, f)

    logger.info("GeoJSON salvo com sucesso!")
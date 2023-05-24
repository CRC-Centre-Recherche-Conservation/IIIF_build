import click
import pandas as pd

from src.data import DataAnnotations
from src.iiif import Annotation
from src.forms import Rectangle


# https://gitlab.huma-num.fr/jpressac/niiif-niiif

# plan

# recuperer manifest existant + metadonnées
# garder seulement les images interessantes
# ajouter les annotations
# ajouter autres collections d'images pour faire des calques
# donc besoin d'upload sur nakala -> pour image iiif

@click.command()
def build_manifest():
    data = DataAnnotations("data/ms59_annotation_iiif.csv", delimiter=";")
    row = data.get_row('Mvis_03')
    annotation = Annotation.data_annotation(row=row)
    for uri in data:
        print(uri)


if __name__ == "__main__":
    build_manifest()

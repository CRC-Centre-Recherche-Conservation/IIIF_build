import click
import pandas as pd

from src.data import DataAnnotations
from src.iiif import Annotation, ManifestIIIF, IIIF
from src.forms import Rectangle


# https://gitlab.huma-num.fr/jpressac/niiif-niiif

# plan

# recuperer manifest existant + metadonnées
# garder seulement les images interessantes
# ajouter les annotations
# ajouter autres collections d'images pour faire des calques
# donc besoin d'upload sur nakala -> pour image iiif

@click.command()
@click.option("--config", "config", type=click.Path(exists=True, dir_okay=False, file_okay=True),
              help="To get the YAML file configuration.")
def build_manifest(**kwargs):
    data = DataAnnotations("data/ms59_annotation_iiif.csv", delimiter=";")

    # build manifest
    manifest = ManifestIIIF('https://emmsm.unicaen.fr/manifests/Avranches_BM_59.json')
    manifest.get_preconfig('/home/maxime/Bureau/projet_crc/IIIF_builder/config_example.yaml')

    # build annotation and canvas
    for uri, values in data:
        for value in values:
            row = data.get_row(uri, value)
            annotation = Annotation.data_annotation(row=row)
            canvas = manifest.get_canvas(uri)



if __name__ == "__main__":
    build_manifest()

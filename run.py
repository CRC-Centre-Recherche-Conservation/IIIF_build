import click
import pandas as pd

from src.opt.variables import USEFULL_CSV

from src.annotation import Rectangle

# https://gitlab.huma-num.fr/jpressac/niiif-niiif

# plan

# recuperer manifest existant + metadonnées
# garder seulement les images interessantes
# ajouter les annotations
# ajouter autres collections d'images pour faire des calques
# donc besoin d'upload sur nakala -> pour image iiif

@click.command()
def build_manifest():
    df = pd.read_csv("data/ms59_annotation_iiif.csv", delimiter=";")
    df = df.drop(columns=USEFULL_CSV)
    df.groupby('Reference.1')['Name'].apply(list)


if __name__ == "__main__":
    build_manifest()

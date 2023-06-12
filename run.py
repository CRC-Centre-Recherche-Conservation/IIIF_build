import click

from src.data import DataAnnotations
from src.iiif import Annotation, ManifestIIIF
from src.opt.data_variables import LANGUAGES
from src.opt.variables import URI_CRC

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
@click.option("-l", "--language", "language", type=click.Choice(LANGUAGES), multiple=False, default='fr',
              help="Choose your languages manifest with ISO 639-1.")
@click.option("--server", type=str, default=URI_CRC, help="Put the schema, the authority and the path part of the URI of your server. For example, if you want a manifest in this address : https://data.crc.fr/iiif/manifests/ms_59_Avranches.json \
                                                                          you need to inquire the url : https://data.crc.fr/iiif/. The path manifests is automaticaly adding by the script.")
def build_manifest(**kwargs):
    data = DataAnnotations("data/ms59_annotation_iiif.csv", delimiter=";")

    # build manifest
    manifest = ManifestIIIF('https://emmsm.unicaen.fr/manifests/Avranches_BM_59.json')
    manifest.get_preconfig('/home/maxime/Bureau/projet_crc/IIIF_builder/config_example.yaml')
    manifest.build_manifest()

    # build annotation and canvas
    for uri, values in data:
        for value in values:
            row = data.get_row(uri, value)
            csv_anno = Annotation.data_annotation(row=row)

            manifest.get_canvas(uri)

    """for canvas in manifest.canvases:
        manifest.manifes"""

    manifest.build_thumbnail()
    print(manifest._print_json())


if __name__ == "__main__":
    build_manifest()

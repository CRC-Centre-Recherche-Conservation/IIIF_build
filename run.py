import sys
import os
import http.server
import socketserver
import click
from iiif_prezi3 import Canvas, ResourceItem, AnnotationPage, Annotation

from src.data import DataAnnotations
from src.iiif import AnnotationIIIF, ManifestIIIF
from src.opt.data_variables import LANGUAGES
from src.opt.variables import URI_CRC


# https://gitlab.huma-num.fr/jpressac/niiif-niiif

# plan

# recuperer manifest existant + metadonnées
# garder seulement les images interessantes
# ajouter les annotations
# ajouter autres collections d'images pour faire des calques
# donc besoin d'upload sur nakala -> pour image iiif

# pour l'intant, ne lit que les API Presentation 2.0

# to check https://github.com/IIIF/presentation-validator

@click.group()
def run_manifest():
    pass


@run_manifest.command()
@click.option("--config", "config", type=click.Path(exists=True, dir_okay=False, file_okay=True),
              help="To get the YAML file configuration.")
@click.option("-l", "--language", "language", type=click.Choice(LANGUAGES), multiple=False, default='fr',
              help="Choose your languages manifest with ISO 639-1.")
@click.option("--server", "server", type=str, default=URI_CRC, help="Put the schema, the authority and the path part of the URI of your server. For example, if you want a manifest in this address : https://data.crc.fr/iiif/manifests/ms_59_Avranches.json \
                                                                          you need to inquire the url : https://data.crc.fr/iiif/. The path manifests is automaticaly adding by the script.")
@click.option("--usage-memory", "usage_memory", type=bool, default=False, is_flag=True, help="To see usage of RAM")
def build_manifest(*args, **kwargs):
    """
    Build manifest IIIF with standard API Presentation 3.0
    :param args:
    :param kwargs:
    :return: Manifest API Presentation 3.0
    """
    data = DataAnnotations("data/ms59_annotation_iiif.csv", delimiter=";")

    # build manifest
    manifest = ManifestIIIF('https://emmsm.unicaen.fr/manifests/Avranches_BM_59.json')
    manifest.get_preconfig('/home/maxime/Bureau/projet_crc/IIIF_builder/config/config_example.yaml')
    manifest.build_manifest()

    # Get annotation and canvas
    for uri, values in data:
        manifest.get_canvas(uri)
        list_anno = []
        for value in values:
            row = data.get_row(uri, value)
            list_anno.append(AnnotationIIIF.data_annotation(row=row))
        manifest.annotation[uri] = list_anno

    for n_canvas, uri_canvas in enumerate(manifest.canvases):
        #get original data
        canvas = manifest.canvases[uri_canvas]

        # Canvas entities
        canvas_img = Canvas(id=canvas['@id'],
                            width=canvas['width'],
                            height=canvas['height'])

        # Ressource image entities for canvas
        ressource_img = ResourceItem(id=canvas['images'][0]['resource']['@id'],
                                     type=canvas['images'][0]['resource']['@type'],
                                     format=canvas['images'][0]['resource']['format'],
                                     height=canvas['images'][0]['resource']['height'],
                                     width=canvas['images'][0]['resource']['width'])

        # Annotation for add ressource image in canvas
        anno_img = Annotation(id=URI_CRC + f"/annotation/p{str(n_canvas)}-image",
                              motivation="painting",
                              body=ressource_img,
                              target=canvas_img.id)

        #Add service to image
        anno_img.make_service(id=canvas['images'][0]['resource']['service']['@id'],
                              type="ImageService3",
                              profile="level2")

        #Page annotation for canvas
        anno_page = AnnotationPage(id=URI_CRC + f"/page/p{str(n_canvas)}/1")
        anno_page.add_item(anno_img)


        for n_anno, data_anno in enumerate(manifest.annotation[uri_canvas]):
            AnnotationIIIF(canvas=canvas, data=data_anno, uri=uri_canvas, n=(n_canvas, n_anno), **kwargs)

        #Add annotation by canvas
        canvas_img.add_item(anno_page)
        #Add cavas in manifest
        manifest.manifest.add_item(canvas_img)

    if kwargs['usage_memory']:
        print("The size of the manifest.canvases is:", sys.getsizeof(manifest.canvases), "bytes.")
        print("The size of the annotation is:", sys.getsizeof(manifest.annotation), "bytes.")
        print("The size of the manifest is:", sys.getsizeof(manifest.manifest), "bytes.")

    manifest.build_thumbnail()
    print(manifest._print_json())

    with open('output/manifest.json', 'w') as outfile:
        outfile.write(manifest.manifest.json(indent=2, ensure_ascii=False))


@run_manifest.command()
def server_manifest():
    class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
        def _set_headers(self):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

        def do_HEAD(self):
            self._set_headers()

        def do_GET(self):
            # self._set_headers()

            if self.path == '/':
                self.path = 'output/'

            for file in os.listdir('output/'):
                if self.path == f'/{file}':
                    self.path = f'output/{file}'

            return http.server.SimpleHTTPRequestHandler.do_GET(self)

    # Create an object of the above class
    handler_object = MyHttpRequestHandler

    PORT = 8000
    try:
        my_server = socketserver.TCPServer(("", PORT), handler_object)
    except OSError:
        PORT = PORT + 1
        my_server = socketserver.TCPServer(("", PORT), handler_object)
    print('Listening on http://localhost:%s' % PORT)
    # Star the server
    try:
        my_server.serve_forever()
    except KeyboardInterrupt:
        my_server.server_close()
        print("Server Closed")


if __name__ == "__main__":
    run_manifest()

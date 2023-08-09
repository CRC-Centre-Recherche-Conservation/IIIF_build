import sys
import socketserver
import click
from collections import namedtuple
from iiif_prezi3 import Canvas, ResourceItem, AnnotationPage, Annotation

from src.data import DataAnnotations
from src.iiif import AnnotationIIIF, ManifestIIIF, ServicesIIIF, CanvasIIIF, SequenceIIIF
from src.opt.data_variables import LANGUAGES
from src.opt.variables import URI_CRC, ENDPOINT_MANIFEST
from src.srv.localhost import MyHttpRequestHandler
from src.srv.sftp import Sftp
from src.opt.tools import get_default_project


@click.group()
def run_manifest():
    pass


@run_manifest.command()
@click.option("-p", "--project", "project", type=str, default=get_default_project(), help="")
@click.option("--config", "config", type=click.Path(exists=True, dir_okay=False, file_okay=True),
              help="To get the YAML file configuration.")
@click.option("-l", "--language", "language", type=click.Choice(LANGUAGES), multiple=False, default='fr',
              help="Choose your languages manifest with ISO 639-1.")
@click.option("--server", "server", type=str, default=URI_CRC, help="Put the schema, the authority and the path part "
                                                                    "of the URI of your server. For example, "
                                                                    "if you want a manifest in this address : "
                                                                    "https://data.crc.fr/iiif/manifests"
                                                                    "/ms_59_Avranches.json you need to inquire the "
                                                                    "url : https://data.crc.fr/iiif/. The path "
                                                                    "manifests is automaticaly adding by the script.")
@click.option("--usage-memory", "usage_memory", type=bool, default=False, is_flag=True, help="To see usage of RAM")
@click.option("-v", "--verbose", "verbose", type=bool, is_flag=True, help="Get more verbosity")
def build_manifest(*args, **kwargs):
    """
    Build manifest IIIF with standard API Presentation 3.0
    :param args:
    :param kwargs:
    :return: Manifest API Presentation 3.0
    """
    data = DataAnnotations("data/data_annotations/ms59_annotation_iiif.csv", delimiter=";")

    ########################### Build Principal Manifest #####################################

    # manifest = ManifestIIIF('https://emmsm.unicaen.fr/manifests/Avranches_BM_59.json')
    manifest = ManifestIIIF(
        'https://crc-centre-recherche-conservation.github.io/iiif/iiif/manifest/Avranches_BM_59.json')
    manifest.get_preconfig('/home/maxime/Bureau/projet_crc/IIIF_builder/config/config_example.yaml')
    manifest.build_manifest()

    ############## Make Canvas ##############
    # Get annotation and canvas
    for uri, values in data:
        manifest.get_canvas(uri)
        list_anno = []
        for value in values:
            row = data.get_row(uri, value)
            list_anno.append(AnnotationIIIF.data_annotation(row=row))
        manifest.annotation[uri] = list_anno
    for n_canvas, uri_canvas in enumerate(manifest.canvases):
        # get original data
        canvas = manifest.canvases[uri_canvas]

        # Canvas entities
        canvas_img = Canvas(id=canvas['@id'],
                            label=canvas['label'],
                            width=canvas['width'],
                            height=canvas['height'])

        # Service Image
        uri_info = canvas['images'][0]['on']
        # get info services
        service = ServicesIIIF(uri_info)
        # Get canvas parameters
        url_image = canvas['images'][0]['resource']['@id']
        canvas_api = CanvasIIIF(url_image, verbose=kwargs['verbose'])
        # verify api parameters and format
        url_image = canvas_api.check_size(service.api)
        _format = canvas_api.build_format()

        # Resource image entities for canvas
        resource_img = ResourceItem(id=url_image,
                                    type=canvas['images'][0]['resource']['@type'],
                                    format=_format if _format is not None else canvas['images'][0]['resource'][
                                        'format'],  # To get correct format, but if error you got original format
                                    height=canvas['images'][0]['resource']['height'],
                                    width=canvas['images'][0]['resource']['width'])
        # Add service to image
        ## API Presentation 2.0 - 2.1
        if manifest.api < 3.0:
            service_info = service.get_info_image()
            # build service
            resource_img.make_service(id=uri_info.replace('/info.json', ''),
                                      type=service_info.type,
                                      profile=service_info.profile)  # maybe level1
        ## For Presentation API 3.0
        else:
            resource_img.make_service(id=canvas['items'][0]['items'][0]['service'][0]['@id'],
                                      type=canvas['items'][0]['items'][0]['service'][0]['type'],
                                      profile=canvas['items'][0]['items'][0]['service'][0]['profile'])  # maybe level1

        # Annotation for add resource image in canvas
        anno_img = Annotation(id=kwargs['server'] + f"annotation/p{n_canvas:05}-image",
                              motivation="painting",
                              body=resource_img,
                              target=canvas_img.id)

        # clean variable
        del url_image, resource_img, service, service_info, canvas_api, _format

        # Page annotation for canvas
        anno_page = AnnotationPage(id=kwargs['server'] + f"page/p{str(n_canvas)}/1")
        anno_page.add_item(anno_img)

        ############## Write Annotations ##############
        for n_anno, data_anno in enumerate(manifest.annotation[uri_canvas]):
            annotation = AnnotationIIIF(canvas=canvas, data=data_anno, uri=uri_canvas, **kwargs)

            forms = annotation.make_forms()
            if n_anno > 10:
                form_anno = Annotation(id=kwargs['server'] + f"annotation/p{n_canvas:05}-image/anno_{n_anno:01}-svg",
                                       motivation="commenting",  # maybe other
                                       body={"type": "TextualBody",
                                             "language": "fr",
                                             "format": "text/html",
                                             "value": f"""<p><b>Type d'analyse:</b> {data_anno['Type_analysis']}</p>"""},
                                       target={"type": "SpecificResource",
                                               "source": canvas_img.id,
                                               "selector": {"type": "SvgSelector", "value": forms}
                                               })

                canvas_img.add_annotation(form_anno, anno_page_id=kwargs['server'] + f"page/p{str(n_canvas)}/2")

            # Add tags
            try:
                for n_tag, tag in enumerate(annotation.data['Tags']):
                    anno_tag = Annotation(
                        id=kwargs['server'] + f"annotation/p{n_canvas:05}-image/anno_{n_anno:01}/tags/{n_tag:01}",
                        motivation="tagging",
                        body={"type": "TextualBody",
                              "language": "fr",
                              "format": "text/plain",
                              "value": f"{tag}"},
                        target=canvas_img.id + f"#xywh={str(annotation.xywh)}")
                    canvas_img.add_annotation(anno_tag, anno_page_id=kwargs['server'] + f"page/p{str(n_canvas)}/3")
            # If None value for tag
            except TypeError:
                pass

        # Add annotation by canvas
        canvas_img.add_item(anno_page)
        # Add canvas in manifest
        manifest.manifest.add_item(canvas_img)

    # build thumbnail manifest
    manifest.build_thumbnail()
    # print(manifest._print_json())

    ########################### Build Collections #####################################

    ############## Make Scanners Manifest's ##############
    # Upload files
    list_img = Sftp.prepare_images()
    for img in list_img:
        Sftp.upload_images(kwargs['project'], id_=img, imgs=list_img[img], **kwargs)

    # Get list of resources to srv
    list_img = Sftp.get_list_dir(kwargs['project'])

    Error = namedtuple('Error', ['n', 'list_id'])
    error = Error(n=0, list_id=[])

    # Iter on analysis
    for analysis in ['sXRF', 'HS_SWIR', 'HS_VNIR']:

        manifest = ManifestIIIF(
            'https://crc-centre-recherche-conservation.github.io/iiif/iiif/manifest/Avranches_BM_59.json', **kwargs)
        manifest.get_preconfig('/home/maxime/Bureau/projet_crc/IIIF_builder/config/config_example.yaml')
        manifest.build_manifest(url=kwargs['server']+ENDPOINT_MANIFEST+)

        # Get and iter on rows by analysis type
        list_analysis = data.get_type_analysis(_type=analysis)
        for index, row in list_analysis.iterrows():
            label_id = row['Name']
            img_url_1 = row['Reference.1']

            ##### Build 1st Canvas and Image #####
            canvas = manifest.canvases[img_url_1]
            # Canvas entities
            canvas_img = Canvas(id=canvas['@id'],
                                label=canvas['label'],
                                width=canvas['width'],
                                height=canvas['height'])

            # Service Image
            uri_info = canvas['images'][0]['on']
            # get info services
            service = ServicesIIIF(uri_info, **kwargs)
            # Get canvas parameters
            url_image = canvas['images'][0]['resource']['@id']
            canvas_api = CanvasIIIF(url_image, verbose=kwargs['verbose'])
            # verify api parameters and format
            url_image = canvas_api.check_size(service.api)
            _format = canvas_api.build_format()
            resource_principal_img = ResourceItem(id=url_image,
                                                   type=canvas['images'][0]['resource']['@type'],
                                                   format=_format if _format is not None else
                                                   canvas['images'][0]['resource']['format'],
                                                   # To get correct format, but if error you got original format
                                                   height=canvas['images'][0]['resource']['height'],
                                                   width=canvas['images'][0]['resource']['width'])

            # Add service to image
            ## API Presentation 2.0 - 2.1 (related to original manifest)
            if manifest.api < 3.0:
                service_info = service.get_info_image()
                # build service
                resource_principal_img.make_service(id=uri_info.replace('/info.json', ''),
                                                     type=service_info.type,
                                                     profile='level1')  # maybe level1
            ## For Presentation API 3.0
            else:
                resource_principal_img.make_service(id=canvas['items'][0]['items'][0]['service'][0]['@id'],
                                                     type=canvas['items'][0]['items'][0]['service'][0]['type'],
                                                     profile='level1')

            # Annotation for add resource image in canvas
            anno_principal_img = Annotation(id=kwargs['server'] + f"annotation/{label_id}-main-images",
                                            motivation="painting",
                                            body=resource_principal_img,
                                            target=canvas_img.id)

            ##### Build others Images (Scans) #####
            idx_img = list(filter(lambda x: x.startswith(row['Name']), list(list_img.keys())))
            # Check if id is empty
            if len(idx_img) == 0:
                error.n += 1
                error.list_id.append(row['Name'])

            for img in idx_img:
                sequence_img = SequenceIIIF(kwargs['project'], img, verbose=kwargs['verbose'])

                ressource_scan = ResourceItem(id=sequence_img.build_url_V3(),
                                              type='dctypes:Image',
                                              format=_format if _format is not None else 'image/jpeg',
                                              height=list_img[img].height,
                                              width=list_img[img].width)

                # Add label
                ressource_scan.add_label('test: ' + analysis + ', ' + row['Name'], language='fr')

                # Services
                ressource_scan.make_service(id=sequence_img.build_uri(),
                                            type='ImageService3',
                                            profile='level1')

                # Add to annotation
                anno_principal_img = Annotation(id=kwargs['server'] + f"annotation/{label_id}-main-images",
                                                motivation="painting",
                                                body=ressource_scan,
                                                target=canvas_img.id)

    if error.n > 0:
        print(f"Error identifying images from the following identifiers: {', '.join(error.list_id)}.")
        print(f"Please check the integrity of the 'data_files' folder.")
        exit(0)

    # https://iiif-prezi.github.io/iiif-prezi3/recipes/0230-navdate/#example-3-collection_1

    # Pour multispectral suivre -> https://iiif.io/api/cookbook/recipe/0033-choice/

    if kwargs['usage_memory']:
        print("The size of the manifest.canvases is:", sys.getsizeof(manifest.canvases), "bytes.")
        print("The size of the annotation is:", sys.getsizeof(manifest.annotation), "bytes.")
        print("The size of the manifest is:", sys.getsizeof(manifest.manifest), "bytes.")

    with open('output/manifest_MS_59_CRC.json', 'w') as outfile:
        outfile.write(manifest.manifest.json(indent=2, ensure_ascii=False))


@run_manifest.command()
def server_manifest():
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

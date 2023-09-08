import os
import sys
import socketserver
import click
from collections import namedtuple
from iiif_prezi3 import Canvas, ResourceItem, AnnotationPage, Annotation

from src.data import DataAnnotations
from src.iiif import AnnotationIIIF, ManifestIIIF, ServicesIIIF, CanvasIIIF, SequenceIIIF
from src.opt.data_variables import LANGUAGES
from src.opt.variables import URI_CRC, ENDPOINT_MANIFEST, SCANNERS, ENDPOINT_BASE
from src.srv.localhost import MyHttpRequestHandler
from src.srv.sftp import Sftp
from src.opt.tools import get_default_project
from path import CURRENT_PATH


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
@click.option("-N", "--NO-SSH", "no_ssh", type=bool, is_flag=True, help="To disable data transfer via SSH to the IIIF server. For example, if you want to run certain tests or if files have already been uploaded.")
@click.option("-v", "--verbose", "verbose", type=bool, is_flag=True, help="Get more verbosity")
def build_manifest(*args, project, **kwargs):
    """
    Build manifest IIIF with standard API Presentation 3.0
    :param project:
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
        anno_page = AnnotationPage(
            id=kwargs['server'] + ENDPOINT_BASE + manifest.uri_basename + '&' + f"page/p{str(n_canvas)}/1")
        anno_page.add_item(anno_img)

        ############## Write Annotations ##############
        for n_anno, data_anno in enumerate(manifest.annotation[uri_canvas]):
            annotation = AnnotationIIIF(canvas=canvas, data=data_anno, uri=uri_canvas, **kwargs)

            forms = annotation.make_forms()
            if n_anno > 10:
                form_anno = Annotation(id=kwargs[
                                              'server'] + ENDPOINT_BASE + manifest.uri_basename + '&' + f"annotation/p{n_canvas:05}-image/anno_{n_anno:01}-svg",
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
    with open(os.path.join(CURRENT_PATH, 'output', f'{manifest.uri_basename}.json'), 'w') as outfile:
        outfile.write(manifest.manifest.json(indent=2, ensure_ascii=False))

    if kwargs['usage_memory']:
        print("The size of the manifest.canvases is:", sys.getsizeof(manifest.canvases), "bytes.")
        print("The size of the annotation is:", sys.getsizeof(manifest.annotation), "bytes.")
        print("The size of the manifest is:", sys.getsizeof(manifest.manifest), "bytes.")
    # Remove Manifest
    del manifest

    ########################### Build Collections #####################################

    ############## Make Scanners Manifest's ##############
    # Upload files
    if kwargs['no_ssh'] is False:
        list_img = Sftp.prepare_images()
        for img in list_img:
            Sftp.upload_images(project=project, id_=img, imgs=list_img[img], verbose=kwargs['verbose'])

    # Get list of resources to srv
    list_img = Sftp.get_list_dir(project)

    Error = namedtuple('Error', ['n', 'list_id'])
    error = Error(n=0, list_id=[])

    # Iter on analysis
    for n, analysis in enumerate(SCANNERS):
        manifest_scan = ManifestIIIF(
            'https://crc-centre-recherche-conservation.github.io/iiif/iiif/manifest/Avranches_BM_59.json', **kwargs)
        manifest_scan.uri_basename = manifest_scan.uri_manifest.split('/')[-1].replace('.json', f'_{analysis}')
        manifest_scan.build_manifest(url=manifest_scan.uri_manifest.replace('.json', f'_{analysis}.json'))

        # Hyperspectral and XRF
        if analysis != 'MSP':
            # Get and iter on rows by analysis type
            list_analysis = data.get_type_analysis(_type=analysis)

            canvas_images = {}

            #print(list_analysis)
            for index, row in list_analysis.sort_values(by='Reference.1').iterrows():

                # Page annotation for canvas
                anno_page_scan = AnnotationPage(
                    id=kwargs['server'] + ENDPOINT_BASE + manifest_scan.uri_basename + '&' + f"page/p{str(index)}/1")


                label_id = row['Name']
                img_url_1 = row['Reference.1']

                ##### Build 1st Canvas and Image #####
                canvas = manifest_scan.canvases[img_url_1]
                # Canvas entities

                if img_url_1 not in canvas_images:
                    # New canvas
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
                    if manifest_scan.api < 3.0:
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

                    # Add annotation to anno page
                    anno_page_scan.add_item(anno_principal_img)

                    # Add new canvas to dict
                    canvas_images[img_url_1] = canvas_img

                else:
                    canvas_img = canvas_images[img_url_1]


                ##### Build others Images (Scans) #####
                idx_img = list(filter(lambda x: x.startswith(row['Name']), list(list_img.keys())))
                # Check if id is empty
                if len(idx_img) == 0:
                    error.n += 1
                    error.list_id.append(row['Name'])

                for img in idx_img:
                    sequence_img = SequenceIIIF(project=project, filename=img, **kwargs)

                    resource_scan = ResourceItem(id=sequence_img.build_url_V3(),
                                                 type='dctypes:Image',
                                                 format=sequence_img.format if sequence_img.format is not None else 'image/jpeg',
                                                 height=list_img[img][1],
                                                 width=list_img[img][0])

                    # Add label
                    resource_scan.add_label('test: ' + analysis + ', ' + row['Name'], language='fr')

                    # Services
                    resource_scan.make_service(id=sequence_img.build_uri(),
                                               type='ImageService3',
                                               profile='level2')


                    # Add to annotation
                    anno_img_scan = Annotation(id=kwargs['server'] + f"annotation/{label_id}-main-images",
                                               motivation="painting",
                                               body=resource_scan,
                                               # list_img -> correspond to dict parsing files sftp
                                               target=canvas_img.id + '#' + sequence_img.get_xwyh(canvas=canvas_img,
                                                                                                  row=row,
                                                                                                  image_size=list_img[img]))
                    # Add annotation to anno page
                    anno_page_scan.add_item(anno_img_scan)

                # Add annotation by canvas
                canvas_img.add_item(anno_page_scan)
                # Add update canvas
                canvas_images[img_url_1] = canvas_img
            # Add canvas in manifest
            for url_base in canvas_images:
                manifest_scan.manifest.add_item(canvas_images[url_base])

        # Multispectral
        elif analysis == 'MSP':
            pass


        with open(os.path.join(CURRENT_PATH, 'output', f'{manifest_scan.uri_basename}.json'), 'w') as outfile:
            outfile.write(manifest_scan.manifest.json(indent=2, ensure_ascii=False))

    if error.n > 0:
        print(f"Error identifying images from the following identifiers: {', '.join(error.list_id)}.")
        print(f"Please check the integrity of the 'data_files' folder.")
        exit(0)

    # https://iiif-prezi.github.io/iiif-prezi3/recipes/0230-navdate/#example-3-collection_1

    # Pour multispectral suivre -> https://iiif.io/api/cookbook/recipe/0033-choice/


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

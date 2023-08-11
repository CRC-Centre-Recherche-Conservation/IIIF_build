import pandas as pd
import requests
import yaml
from collections import namedtuple
from yaml.loader import SafeLoader
from iiif_prezi3 import Manifest, KeyValueString, config, ExternalItem, ResourceItem

from src.opt.variables import DOMAIN_IIIF_HTTPS, ENDPOINT_API_IMG_3, ENDPOINT_API_IMG_2, ENDPOINT_MANIFEST
from .forms import Rectangle, Marker


# https://iiif-prezi.github.io/iiif-prezi3/recipes/0019-html-in-annotations/
# https://github.com/dasch-swiss/daschiiify/blob/main/test/daschiiify-alpha.py


class IIIF(object):
    canvases = {}
    manifest = Manifest
    annotation = {}

    def __init__(self, uri, request=True, **kwargs):
        self.uri = uri
        # Get json
        if request:
            self.json = self._get_manifest()
            # Get api level
            self.api = self.get_api()
        # options
        self.verbose = kwargs.get('verbose')
        self.lang = kwargs.get('language', 'fr')
        self.server = kwargs.get('server')
        config.configs['helpers.auto_fields.AutoLang'].auto_lang = self.lang

    def _get_manifest(self):
        """
        Request http of API Manifest
        :return:json request
        """
        iiif = requests.get(self.uri, allow_redirects=True)
        if 200 <= iiif.status_code < 400:
            return iiif.json()
        else:
            print('Impossible to connect to server. Check URL validity.')
            print(f'Code error : {iiif.status_code}).')
            exit(0)

    def get_api(self) -> float:
        """
        Function to determine level api in the original manifest
        :return:
        """
        if self.json['@context'] == 'http://iiif.io/api/presentation/2/context.json':
            return 2.1
        elif self.json['@context'] == 'http://iiif.io/api/presentation/3/context.json':
            return 3.0
        else:
            raise ValueError(
                'Impossible to get the level API Presentation of your manifest. Please, check the manifest and its validity.')


class ManifestIIIF(IIIF):
    rights = ['Etalab 2.0', "https://spdx.org/licenses/etalab-2.0.html"]
    institution = [("Centre de la Recherche sur la Conservation", "https://crc.mnhn.fr/fr")]
    attribution = KeyValueString(label="Attribution",
                                 value="<span>Centre de la Recherche sur la Conservation. <a href=\"https://spdx.org/licenses/etalab-2.0.html\">OPEN LICENCE 2.0</a> <a href=\"https://spdx.org/licenses/etalab-2.0.html\" title\"Etalab 2.0\"><img src=\"https://www.etalab.gouv.fr/wp-content/uploads/2011/10/licence-ouverte-open-licence.gif\"/></a></span>")
    description = 'None'
    metadata = []
    seealso = []

    def __init__(self, uri, **kwargs):
        """
        :param uri: str url, Original manifest
        :param kwargs: verbose
        """
        super().__init__(
            uri=uri, **kwargs)
        self.label = self._build_label()
        # Variable for new manifest
        self.uri_basename = self._build_uri_basename()
        self.uri_manifest = self._build_uri()

    def _print_json(self):
        return self.manifest.json(indent=2, ensure_ascii=False)

    def _build_label(self):
        return self.json['label'] + ", analyses physico-chimique @CRC"

    def _build_uri_basename(self):
        return str(self.uri.split('/')[-1].replace('.json', '') + '_CRC')

    def _build_uri(self):
        return DOMAIN_IIIF_HTTPS + ENDPOINT_MANIFEST + self.uri_basename + '.json'

    def get_metadata(self):
        if self.verbose:
            print("Getting metadata!")
        return self.json['metadata']

    def get_canvas(self, url_image: list):
        for canvas in self.json['sequences'][0]['canvases']:
            if canvas['images'][0]['resource']['@id'] == url_image:
                self.canvases[canvas['images'][0]['resource']['@id']] = canvas

    def get_preconfig(self, filename):
        if self.verbose:
            print("""//////////////////////YAML GENERATION IN PROGRESS//////////////////////""")
        with open(filename) as f:
            config_yaml = yaml.load(f, Loader=SafeLoader)

            # Label
            if config_yaml['label'].upper() != "DEFAULT":
                self.label = config_yaml['label']
                if self.verbose:
                    print(self.label)

            if config_yaml['manifest'].upper() != "DEFAULT":
                self.uri_basename = config_yaml['manifest'].replace(' ', '_')
                self.uri_manifest = DOMAIN_IIIF_HTTPS + ENDPOINT_MANIFEST + config_yaml['manifest'].replace(' ', '_') + '.json'
                if self.verbose:
                    print(self.uri_manifest)

            # Description
            if config_yaml['description'].upper() != 'NONE':
                self.description = config_yaml['description']
                if self.verbose:
                    print(self.description)

            # Licence
            if config_yaml['licence']['label'].upper() != 'DEFAULT':
                self.rights[0] = config_yaml['licence']['label']
                # https link is better but well ...
                if config_yaml['licence']['link'].startswith('http') and config_yaml['licence']['link'] is not None:
                    self.rights[1] = config_yaml['licence']['link']
                else:
                    raise ValueError(
                        "You need to indicate an URI of your licence. Need to start by http or https protocols")
                if config_yaml['licence']['attribution'].upper() != 'NONE':
                    self.attribution = KeyValueString(label="Attribution", value=config_yaml['licence']['attribution'])

            if self.verbose:
                print(self.rights[0], self.rights[1])

            # Institution
            institution = []
            for i in config_yaml['Institution']:
                if i['label'].upper() != "DEFAULT":
                    institution.append(i['label'])
                else:
                    institution = self.institution[0][0]
            self.metadata.append(
                KeyValueString(label="Institutions", value=', '.join(institution))
            )
            del institution

            # Metadata
            for n, data in enumerate(config_yaml['metadata']['data-source']):
                if data['url'] is not None:
                    self.metadata.append(KeyValueString(label=f"Sources des données {str(n)}", value=data['url']))

            tech = []
            for technique in config_yaml['metadata']['technique']:
                if technique['label'] is not None:
                    tech.append(technique['label'])
            self.metadata.append(KeyValueString(label="Techniques utilisées", value=', '.join(tech)))
            del tech

            # Authors
            for n, author in enumerate(config_yaml['authors']):
                if n == 1:
                    self.metadata.append(
                        KeyValueString(label='Responsable Scientifique', value=author['name'].upper() + " " +
                                                                               author['forename'] if author[
                                                                                                         'forename'].upper() != 'NONE' else 'n.c.' + ", " +
                                                                                                                                            author[
                                                                                                                                                'role'] if
                        author['role'].upper() != 'NONE' else 'n.c.'))
                else:
                    self.metadata.append(
                        KeyValueString(label=f'Responsable Scientifique {str(n)}', value=author['name'].upper() + " " +
                                                                                         author['forename'] if author[
                                                                                                                   'forename'].upper() != 'NONE' else 'n.c.' +
                                                                                                                                                      ", " +
                                                                                                                                                      author[
                                                                                                                                                          'role'] if
                        author['role'].upper() != 'NONE' else 'n.c.'))

    def build_manifest(self, url=None):
        """
        Function to build manifest IIIF Presentation among API 3.0
        :url: str, Custom URL for MANIFEST URI
        :return:
        """

        # Check if we registered any metadata complementary
        if len(self.metadata) < 1:
            self.metadata = None
        # Option personalisation url
        if url is None:
            url = self.uri_manifest

        # Build Manifest
        self.manifest = Manifest(
            id=url,
            label=self.label,
            rights=self.rights[1],
            behavior=["paged"],
            viewingDirection=self.json['viewingDirection'],
            summary=self.description,
            metadata=self.metadata,
            requiredStatement=self.attribution,
            seeAlso=[ExternalItem(id=self.json['@id'], format="application/ld+json", type="Manifest",
                                  label=self.json['label'])]
        )

    def build_thumbnail(self):
        """
        Get first canvas in the processing manifest to convert it in thumbnail for the manifest.
        :return: None
        """
        # Get first canvas
        canvas_1 = list(self.canvases.keys())[0]
        canvas_1 = self.canvases[canvas_1]

        # build thumbnail
        thumbnail = ResourceItem(id=canvas_1['images'][0]['resource']['@id'],
                                 type="Image",
                                 format=canvas_1['images'][0]['resource']['format'],
                                 width=200,
                                 height=300)

        # API service among level API presentation of the manifest
        if self.api < 3.0:
            uri_info = canvas_1['images'][0]['on']
            # get info services
            service = ServicesIIIF(uri_info)
            service_info = service.get_info_image()
            # build service
            thumbnail.make_service(id=uri_info,
                                   type=service_info.type,
                                   profile=service_info.profile)
        # For Presentation API 3.0
        else:
            thumbnail.make_service(id=canvas_1['images'][0]['resource']['service']['@id'],
                                   type=canvas_1['images'][0]['resource']['service']['type'],
                                   profile=canvas_1['images'][0]['resource']['service']['profile'])
        # add thumbnail in manifest
        self.manifest.thumbnail = [thumbnail]


class CanvasIIIF:
    format = {'jpg': 'image/jpeg',
              'jpeg': 'image/jpeg',
              'tif': ' image/tiff',
              'tiff': 'image/tiff',
              'png': ' image/png',
              'gif': 'image/gif',
              'jp2': 'image/gjp2',
              'webp': 'image/webp',
              'pdf': 'application/pdf'}

    def __init__(self, url: str, **kwargs):
        """
        Class to check and modify information in CANVAS and its resources.
        :param url: str, url of api image
        :param kwargs: verbose (bool)
        """
        self.url = url
        self.url_dir = url.split('/')
        self.verbose = kwargs.get('verbose', False)

    def check_size(self, level_api: float) -> str:
        """
        Parse url and identify if the size parameters correspond to the level API Image
        :param level_api: float, level of API Image
        :return:
        """
        # API image 2.0 or 2.1.1
        if level_api < 3.0:
            if self.url_dir[-3] == 'full':
                return self.url
            else:
                if self.verbose:
                    print("Incompatibility API image 2.0")
                    print("Image api URL modification : add 'full' parameters in directory url")
                return '/'.join(self.url_dir)
        # API image 3.0
        else:
            if self.url_dir[-3] == 'max':
                return self.url
            else:
                if self.verbose:
                    print("Incompatibility API image 3.0")
                    print("Image api URL modification : add 'max' parameters in directory url")
                self.url_dir[-3] = 'max'
                return '/'.join(self.url_dir)

    def build_format(self) -> str or None:
        """
        Parse url and determine MIME type image among extension url
        :return: str, MIME type or None if the script don't find extension. In case of None response, get the original value in your manifest.
        """
        _format = self.url_dir[-1].split('.')
        try:
            return self.format[_format[-1].lower()]
        except KeyError:
            return None


class ServicesIIIF(IIIF):
    def __init__(self, uri: str, **kwargs):
        """
        Works for only service image resource (!= API search, auth, etc.)
        :param uri: str, URI of the service linked to your ressource image.
        :param kwargs: verbose, server (see class IIIF)
        """
        if not uri.endswith('info.json'):
            uri = uri + '/info.json'
        try:
            super().__init__(uri=uri, **kwargs)
            self.get_api()
        except RuntimeError:
            print(('Impossible to access to the API image service.'))

    def get_info_image(self) -> namedtuple:
        """
        Get info service for api image.
        {
            "id": self.uri,
            "type": Info.type,
            "profile": Info.profile
        }
        :return: namedtuple(type, profile)
        """
        Info = namedtuple('Info', ['type', 'profile'])
        return Info(type=self.json['type'], profile=self.json['profile'])

    def get_api(self):
        """
        Get level API image with the service
        """
        api_service = self.json['@context']
        if api_service == "http://iiif.io/api/image/3/context.json" or api_service == "https://iiif.io/api/image/3/context.json":
            self.api = 3.0
        elif api_service == "http://iiif.io/api/image/2/context.json" or api_service == "https://iiif.io/api/image/2/context.json":
            self.api = 2.0
        else:
            raise ValueError('Impossible to get level API Image')


class AnnotationIIIF:
    xywh = None

    def __init__(self, canvas: dict, data: dict, uri: str, **kwargs):
        """

        :param canvas:
        :param data:
        :param uri:
        :param n:
        :param kwargs:
        """
        self.data = data
        self.uri = uri
        self.canvas = canvas
        self.verbose = kwargs['verbose']

    def make_forms(self) -> str:
        """
        Function to get <svg> balise content for annotation iiif
        :param json: manifest iiif serialized
        :return: str, <svg> html
        """
        if isinstance(self.data['Type'], str):
            # RECTANGLE
            if self.data['Type'].upper() == 'RECTANGLE':
                rectangle = Rectangle(_id=self.data['Name'], image_url=self.uri, x=self.data['Coordinates']['x'],
                                      y=self.data['Coordinates']['y'], w=self.data['Coordinates']['w'],
                                      h=self.data['Coordinates']['h'], verbose=self.verbose)
                # check dimension image and form
                rectangle.check_dim_manifest(canvas_h=self.canvas['images'][0]['resource']['height'],
                                             canvas_w=self.canvas['images'][0]['resource']['width'])
                dimension = rectangle.dim_img_origin if rectangle.dim_img_origin is not None else rectangle.image_size
                # fit dimension
                tag = rectangle.get_svg()
                # get xywh dimension
                self.xywh = str(rectangle.x) + ',' + str(rectangle.y) + ',' + str(rectangle.w) + ',' + str(rectangle.h)

            # MARKER
            elif self.data['Type'].upper() == 'MARKER':
                marker = Marker(_id=self.data['Name'], image_url=self.uri, x=self.data['Coordinates']['x'],
                                y=self.data['Coordinates']['y'], verbose=self.verbose)
                # check dimension image and form
                marker.check_dim_manifest(canvas_h=self.canvas['images'][0]['resource']['height'],
                                          canvas_w=self.canvas['images'][0]['resource']['width'])
                dimension = marker.dim_img_origin if marker.dim_img_origin is not None else marker.image_size
                # fit dimension
                tag = marker.get_svg()
                # get xywh dimension
                self.xywh = str(marker.x) + ',' + str(marker.y) + ',' + str(marker.w) + ',' + str(marker.h)
            else:
                raise ValueError("The data annotation type need to be 'rectangle' or 'marker'")
            return f"""<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{str(dimension[0])}" height="{str(dimension[1])}" xmlns:xlink="http://www.w3.org/1999/xlink">{tag}</svg>"""
        else:
            raise TypeError('The data annotation type need to be string.')

    @classmethod
    def data_annotation(cls, row: pd.DataFrame) -> dict:
        """
        Function to get data and build annotation object
        :param row:
        :return: dict
        """
        try:
            tags = [tag.strip() for tag in row['Tags'].values[0].split(',')]
        except (IndexError, AttributeError) as err:
            print("!Error : " + row['Name'].values[0], ", " + str(err) + "!")
            tags = None
            pass
        try:
            return {
                'Name': row['Name'].values[0],
                'Type': row['Type'].values[0],
                'Type_analysis': row['Character'].values[0],
                'Tags': tags,
                'Dimensions': {
                    'width': row['Dimensions'].values[0].split('x')[0].strip(),
                    'height': row['Dimensions'].values[0].split('x')[1].strip(),
                },
                'Identifier': row['Identifier'].values[0],
                'Coordinates':
                    {'x': row['X'].values[0], 'y': row['Y'].values[0], 'w': row['W'].values[0],
                     'h': row['H'].values[0]},
                'Value': row['Value'].values[0],
                'URI': row['Reference.1'].values[0]
            }
        except Exception as err:
            print(err)


class SequenceIIIF:
    formats = {'jpg': 'image/jpeg',
               'jpeg': 'image/jpeg',
               'tif': ' image/tiff',
               'tiff': 'image/tiff',
               'png': ' image/png',
               'gif': 'image/gif',
               'jp2': 'image/gjp2',
               'webp': 'image/webp',
               'pdf': 'application/pdf'}

    def __init__(self, project: str, filename: str, **kwargs):
        self.filename = filename
        self.project = project
        self.verbose = kwargs['verbose']
        self.format, self.extension = self.build_format()

    def build_uri(self):
        """
        Build URI Images
        {https}://{domain}/{endpoint}/{levelAPI}/{project}2%F{id_image}
        :return: str, uri
        """
        return DOMAIN_IIIF_HTTPS + ENDPOINT_API_IMG_3 + self.project + '%2F' + self.filename

    def build_uri_info(self):
        """
        Build URI info.json
        {https}://{domain}/{endpoint}/{levelAPI}/{project}2%F{id_image}/info.json
        :return: str, uri
        """
        return DOMAIN_IIIF_HTTPS + ENDPOINT_API_IMG_3 + self.project + '%2F' + self.filename + '/info.json'

    def build_url_V3(self):
        """
        Build standard URL API Image 3.0
        {https}://{domain}/{endpoint}/{levelAPI}/{project}2%F{id_image}/{region}/{size}/{rotation}/{quality}.{format}
        :return: str, uri
        """
        api_url = '/full/max/0/default.jpg'
        if self.format not in ['.jpeg', '.jpg'] and self.format is not None:
            api_url = api_url.replace('.jpg', '.' + self.extension)
        return DOMAIN_IIIF_HTTPS + ENDPOINT_API_IMG_3 + self.project + '%2F' + self.filename + api_url

    def build_url_V2(self):
        """
        Build standard URL API Image 2.0
        {https}://{domain}/{endpoint}/{levelAPI}/{project}2%F{id_image}/{region}/{size}/{rotation}/{quality}.{format}
        :return: str, uri
        """
        api_url = '/full/max/0/default.jpg'
        if self.extension not in ['jpeg', 'jpg'] and self.extension is not None:
            api_url = api_url.replace('.jpg', '.' + self.extension)
        return DOMAIN_IIIF_HTTPS + ENDPOINT_API_IMG_2 + self.project + '%2F' + self.filename + api_url

    def build_format(self) -> str or None:
        """
        Parse url and determine MIME type image among extension url
        :return: str, MIME type and extension or None if the script don't find extension. In case of None response, get the original value in your manifest.
        """
        _format = self.filename.split('.')
        try:
            return self.formats[_format[-1].lower()], _format[-1].lower()
        except KeyError:
            return None, None

    def get_xwyh(self, canvas, row, image_size):
        """

        :param canvas: Canvas, canvas image configuration
        :param row: Dataframe, row selected of value
        :param image_size: tuple, (width, height)
        :return: str, w,x,y,h
        """

        rectangle = Rectangle(_id=row['Name'], x=row['X'], y=row['Y'],
                              w=row['W'], h=row['H'], verbose=self.verbose)
        rectangle.image_size = ()
        # check dimension image and form and fit
        rectangle.check_dim_manifest(canvas_h=canvas.height,
                                     canvas_w=canvas.width,
                                     image_size=image_size)
        # get xywh dimension
        return str(rectangle.x) + ',' + str(rectangle.y) + ',' + str(rectangle.w) + ',' + str(rectangle.h)

# pour xrf et hyperspectra
# https://iiif.io/api/cookbook/recipe/0033-choice/


# https://iiif.io/api/cookbook/recipe/0036-composition-from-multiple-images/ annotation pour les photos de miscroscopiues
# "target": "https://iiif.io/api/cookbook/recipe/0036-composition-from-multiple-images/canvas/p1#xywh=3949,994,1091,1232" -> en gros selection via xywh

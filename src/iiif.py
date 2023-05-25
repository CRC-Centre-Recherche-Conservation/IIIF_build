import pandas as pd
import requests
import yaml
from yaml.loader import SafeLoader
from iiif_prezi3 import Manifest, KeyValueString, config


# peut etre un decorateur pour faire une recuperation spetiale du code json ?
# https://iiif-prezi.github.io/iiif-prezi3/recipes/0019-html-in-annotations/

# strategie on prend le manifest initiale et on le reconstruir depuis zero

class IIIF(object):
    canvas = {}

    def __init__(self, uri, **kwargs):
        self.uri = uri
        self.json = self._get_manifest()
        self.verbose = kwargs.get('verbose', False)

    def _get_manifest(self):
        return requests.get(self.uri, allow_redirects=True).json()

    def get_canvas(self, url_image: list):
        for canvas in self.json['sequences'][0]['canvases']:
            if canvas['images'][0]['resource']['@id'] == url_image:
                self.canvas[canvas['images'][0]['resource']['@id']] = canvas


class ManifestIIIF(IIIF):
    rights = ['Etalab 2.0', "https://spdx.org/licenses/etalab-2.0.html"]
    homepage = "https://crc.mnhn.fr/fr"
    requiredStatement = KeyValueString(label="Attribution", value="<span>Centre de la Recherche sur la Conservation. <a href=\"https://spdx.org/licenses/etalab-2.0.html\">OPEN LICENCE 2.0</a> <a href=\"https://spdx.org/licenses/etalab-2.0.html\" title\"Etalab 2.0\"><img src=\"https://www.etalab.gouv.fr/wp-content/uploads/2011/10/licence-ouverte-open-licence.gif\"/></a></span>")
    description = None
    metadata = []

    def __init__(self, uri, **kwargs):
        super().__init__(
            uri=uri, **kwargs)
        self.label = self._build_label()

    def _build_label(self):
        return self.json['label'] + ", analyses physico-chimique @CRC"

    def _build_metadata(self):
        return self.json['metadata']

    def get_preconfig(self, filename):
        with open(filename) as f:
            config_yaml = yaml.load(f, Loader=SafeLoader)
            if config_yaml['label'].upper() != "DEFAULT":
                self.label = config_yaml['label']
                print(self.label)
            if config_yaml['description'] != 'None':
                self.description = config_yaml['description']
                print(self.description)
            if config_yaml['licence']['label'] != 'DEFAULT':
                self.rights[0] = config_yaml['licence']['label']
                # https link is better but well ...
                if config_yaml['licence']['link'].startswith('http'):
                    self.rights[1] = config_yaml['licence']['link']
                else:
                    raise ValueError("You need to indicate an URI of your licence. Need to start by http or https protocols")



    def build_manifest(self):
        config.configs['helpers.auto_fields.AutoLang'].auto_lang = 'fr'

        if len(self.metadata) < 1:
            self.metadata = None

        return Manifest(
            id=self.uri,
            label=self.label,
            rights=self.rights,
            homepage=self.homepage,
            behavior=["paged"],
            viewingDirection=self.json['viewingDirection'],
            description=self.description,
            metadata=self.metadata
        )


class CanvasIIIF(IIIF):
    pass


class SequenceIIIF(IIIF):
    class XRF:
        pass

    class HyperSpectral:
        pass


class Annotation(IIIF):
    scheme = {
        'Name': str,
        'Tags': list,
        'Dimensions': {
            'width': int,
            'height': int,
        },
        'Identifier': str,
        'Coordinates':
            {'x': float, 'y': float, 'w': float, 'h': float},
        'Value': str,
        'URI': str
    }

    @classmethod
    def data_annotation(cls, row: pd.DataFrame):
        try:
            tags = [tag.strip() for tag in row['Tags'].values[0].split(',')]
        except (IndexError, AttributeError) as err:
            print("!Error : " + row['Name'].values[0], ", " + str(err) + "!")
            tags = None
            pass
        try:
            return {
                'Name': row['Name'].values[0],
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

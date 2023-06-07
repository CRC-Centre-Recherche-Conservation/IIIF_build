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
    institution = [("Centre de la Recherche sur la Conservation", "https://crc.mnhn.fr/fr")]
    requiredStatement = KeyValueString(label="Attribution", value="<span>Centre de la Recherche sur la Conservation. <a href=\"https://spdx.org/licenses/etalab-2.0.html\">OPEN LICENCE 2.0</a> <a href=\"https://spdx.org/licenses/etalab-2.0.html\" title\"Etalab 2.0\"><img src=\"https://www.etalab.gouv.fr/wp-content/uploads/2011/10/licence-ouverte-open-licence.gif\"/></a></span>")
    description = 'None'
    metadata = ([], [])
    authors = None

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

            # Label
            if config_yaml['label'].upper() != "DEFAULT":
                self.label = config_yaml['label']
                print(self.label)

            # Description
            if config_yaml['description'].upper() != 'NONE':
                self.description = config_yaml['description']
                print(self.description)

            # Licence
            if config_yaml['licence']['label'] != 'DEFAULT':
                self.rights[0] = config_yaml['licence']['label']
                # https link is better but well ...
                if config_yaml['licence']['link'].startswith('http') and config_yaml['licence']['link'] is not None:
                    self.rights[1] = config_yaml['licence']['link']
                else:
                    raise ValueError("You need to indicate an URI of your licence. Need to start by http or https protocols")
            print(self.rights[0], self.rights[1])

            # Institution
            if len(config_yaml['Institution']) > 1:
                self.institution.pop(0)
                for i in config_yaml['Institution']:
                    if i['label'].upper() != "DEFAULT":
                        label = i['label']
                    if i['homepage'].upper() != "DEFAULT":
                        if i['homepage'].startswith('http'):
                            homepage = i['homepage']
                        elif i['homepage'].upper() == "NONE":
                            homepage = 'n.c.'
                        else:
                            raise ValueError(i['homepage'],
                                "You need to indicate a web link of your homepage. Need to start by http or https protocols")
                    self.institution.append((label, homepage))
            else:
                if config_yaml['Institution'][0]['label'].upper() != "DEFAULT":
                    label = config_yaml['Institution'][0]['label']
                if config_yaml['Institution'][0]['homepage'].upper() != "DEFAULT":
                    if config_yaml['Institution'][0]['homepage'].startswith('http'):
                        homepage = config_yaml['Institution'][0]['homepage']
                    elif config_yaml['Institution'][0]['homepage'].upper() == "NONE":
                        homepage = 'n.c.'
                    else:
                        raise ValueError(config_yaml['Institution'][0]['homepage'],
                            "You need to indicate a web link of your homepage. Need to start by http or https protocols")
                self.institution[0] = (str(label), str(homepage))
            print(self.institution)

            # Metadata
            for data in config_yaml['metadata']['data-source']:
                if data['url'] is not None:
                    self.metadata[0].append(data['url'])
            for technique in config_yaml['metadata']['technique']:
                if technique['label'] is not None:
                    self.metadata[1].append(technique['label'])
            print(self.metadata)

            # Authors
            self.authors = [(author['name'] if author['name'].upper() != 'NONE' else 'n.c.',
                             author['forename'] if author['forename'].upper() != 'NONE' else 'n.c.',
                             author['role']if author['role'].upper() != 'NONE' else 'n.c.')
                            for author in config_yaml['authors']]
            print(self.authors)







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

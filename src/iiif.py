import pandas as pd
import requests
import yaml
from yaml.loader import SafeLoader
from iiif_prezi3 import Manifest, KeyValueString, config, ExternalItem, ResourceItem, Annotation

from src.opt.variables import URI_CRC, SCHEME_DATA_ANNOTATION
from .forms import Rectangle, Marker


# https://iiif-prezi.github.io/iiif-prezi3/recipes/0019-html-in-annotations/
# https://github.com/dasch-swiss/daschiiify/blob/main/test/daschiiify-alpha.py


class IIIF(object):
    canvases = {}
    manifest = Manifest

    def __init__(self, uri, **kwargs):
        self.uri = uri
        self.json = self._get_manifest()
        self.verbose = kwargs.get('verbose', False)
        self.lang = kwargs.get('language', 'fr')
        self.server = kwargs.get('server', URI_CRC)
        config.configs['helpers.auto_fields.AutoLang'].auto_lang = self.lang

    def _get_manifest(self):
        return requests.get(self.uri, allow_redirects=True).json()

    def get_canvas(self, url_image: list):
        for canvas in self.json['sequences'][0]['canvases']:
            if canvas['images'][0]['resource']['@id'] == url_image:
                self.canvases[canvas['images'][0]['resource']['@id']] = canvas


class ManifestIIIF(IIIF):
    rights = ['Etalab 2.0', "https://spdx.org/licenses/etalab-2.0.html"]
    institution = [("Centre de la Recherche sur la Conservation", "https://crc.mnhn.fr/fr")]
    attribution = KeyValueString(label="Attribution", value="<span>Centre de la Recherche sur la Conservation. <a href=\"https://spdx.org/licenses/etalab-2.0.html\">OPEN LICENCE 2.0</a> <a href=\"https://spdx.org/licenses/etalab-2.0.html\" title\"Etalab 2.0\"><img src=\"https://www.etalab.gouv.fr/wp-content/uploads/2011/10/licence-ouverte-open-licence.gif\"/></a></span>")
    description = 'None'
    metadata = []
    seealso = []

    def __init__(self, uri, **kwargs):
        super().__init__(
            uri=uri, **kwargs)
        self.label = self._build_label()

    def _print_json(self):
        return self.manifest.json(indent=2, ensure_ascii=False)

    def _build_label(self):
        return self.json['label'] + ", analyses physico-chimique @CRC"

    def get_metadata(self):
        return self.json['metadata']

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
                    raise ValueError("You need to indicate an URI of your licence. Need to start by http or https protocols")
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
                    self.metadata.append(KeyValueString(label='Responsable Scientifique', value=author['name'].upper() + " " +
                                                                                 author['forename'] if author['forename'].upper() != 'NONE' else 'n.c.' + ", " +
                                                                                 author['role']if author['role'].upper() != 'NONE' else 'n.c.'))
                else:
                    self.metadata.append(
                        KeyValueString(label=f'Responsable Scientifique {str(n)}', value=author['name'].upper() + " " +
                                                                               author['forename'] if author['forename'].upper() != 'NONE' else 'n.c.' + ", " +
                                                                               author['role'] if author['role'].upper() != 'NONE' else 'n.c.'))

    def build_manifest(self):

        if len(self.metadata) < 1:
            self.metadata = None
        self.manifest = Manifest(
            id=self.server + 'manifests/' + self.uri.split('/')[-1],
            label=self.label,
            rights=self.rights[1],
            behavior=["paged"],
            viewingDirection=self.json['viewingDirection'],
            summary=self.description,
            metadata=self.metadata,
            requiredStatement=self.attribution,
            seeAlso=[ExternalItem(id=self.json['@id'], format="application/ld+json", type="Manifest", label=self.json['label'])]
        )

    def build_thumbnail(self):
        canvas_1 = list(self.canvases.keys())[0]
        canvas_1 = self.canvases[canvas_1]

        thumbnail = ResourceItem(id=canvas_1['images'][0]['resource']['@id'],
                                 type="Image",
                                 format=canvas_1['images'][0]['resource']['format'],
                                 width=200,
                                 height=300)

        thumbnail.make_service(id=canvas_1['images'][0]['resource']['service']['@id'],
                               type="ImageService3",
                               profile="level2")

        self.manifest.thumbnail = [thumbnail]

    def add_canvas(self, canvas):
        pass


class CanvasIIIF:
    pass


class SequenceIIIF(IIIF):
    class XRF:
        pass

    class HyperSpectral:
        pass


class AnnotationIIIF:
    resize = False

    #self init:
    #annotationPage = AnnotationPage(id=anno_page_id) -> creer un id pour la page en automatique
    #ajouter l'annotation dans la page annotationPage.add_item(annotation)
    #canvas.add_item(annotationPage)

    #make_annotation()

    def check_dimension(self, data_anno: SCHEME_DATA_ANNOTATION, canvas):
        if data_anno['Dimensions']['width'] != canvas['images'][0]['resource']['width']:
            self.resize = True
        elif data_anno['Dimensions']['height'] != canvas['images'][0]['resource']['height']:
            self.resize = True

    def make_annotation(self):
        if self.resize:
            pass
        else:
            pass


    def make_forms(self, data_anno: SCHEME_DATA_ANNOTATION):
        if isinstance(data_anno['Type'], str):
            if data_anno['Type'].upper() == 'RECTANGLE':
                pass
            elif data_anno['Type'].upper() == 'MARKER':
                pass
            else:
                raise ValueError("The data annotation type need to be 'rectangle' or 'marker'")
        else:
            raise TypeError('The data annotation type need to be string.')


    @classmethod
    def data_annotation(cls, row: pd.DataFrame) -> SCHEME_DATA_ANNOTATION:
        """
        Function to get data and build annotation object
        :param row:
        :return:
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


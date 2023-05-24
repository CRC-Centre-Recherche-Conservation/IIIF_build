from collections import namedtuple
import requests
from PIL import Image
from io import BytesIO


class FormSVG:
    def __init__(self, debug: bool = False, verbose=False):
        self.debug = debug
        self.verbose = verbose
        pass

    @staticmethod
    def get_dim_request(url):
        """
        To get
        :param url:
        :return:
        """
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        return img.size

    @staticmethod
    def get_dim_manifest(img_url: str) -> namedtuple:
        Size = namedtuple('Size', ['w', 'h'])

        json = requests.get(img_url).json()

        for page in json['sequences'][0]['canvases']:
            if page['images'][0]['resource']['@id'] == img_url:
                return Size(h=page['images'][0]['resource']['height'], w=page['images'][0]['resource']['width'])

    def fit(self):
        pass

    def export_annotation(self):
        pass


class Rectangle(FormSVG):
    def __init__(self, x, y, w, h, **kwargs):
        super().__init__(debug=kwargs['debug'], verbose=kwargs['verbose'])
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def find_dimension(self):
        pass

    @staticmethod
    def get_dimension_image(width, height) -> tuple:
        """
        image in dimensions to return ration
        """
        ratio = width / height
        return ratio

    def fit(self):
        pass


class Marker(FormSVG):
    def __init__(self, x, y, w, h, **kwargs ):
        super().__init__(debug=kwargs['debug'], verbose=kwargs['verbose'])
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    @staticmethod
    def get_dimension_image(x, y):
        """
        image
        """
        pass

    def fit(self):
        pass
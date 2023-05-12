from collections import namedtuple
import requests
from PIL import Image
from io import BytesIO


class FormSVG:
    def __init__(self, debug: bool = False):
        pass

    def get_dim_request(url):
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        return img.size

    def get_dim_manifest(manifest: str, img_url: str) -> namedtuple:
        Size = namedtuple('Size', ['w', 'h'])

        json = requests.get(url).json()

        for page in json['sequences'][0]['canvases']:
            if page['images'][0]['resource']['@id'] == img_url:
                return Size(h=page['images'][0]['resource']['height'], w=page['images'][0]['resource']['width'])

    def fit(self):
        pass


class Rectangle(FormSVG):
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    @staticmethod
    def get_dimension_image(width, height) -> tuple:
        """
        image in dimensions to return ration
        """
        ratio = width / height
        return ratio

    def fit(self, image):
        pass


class Marker(FormSVG):
    def __init__(self, debug: bool = False):
        pass

    @staticmethod
    def get_dimension_image(x, y):
        """
        image
        """
        pass

    def fit(self):
        pass
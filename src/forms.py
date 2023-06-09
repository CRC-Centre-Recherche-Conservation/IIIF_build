from collections import namedtuple
import requests
import json
from PIL import Image
from io import BytesIO

from src.opt.tools import Color

class FormSVG:
    redimension = False
    # Ratio is None or tuple (width, height)
    ratio = None
    dim_img_origin = None

    def __init__(self, _id: str, type: str, image_url: str, debug: bool = False, verbose: bool = False):
        if image_url.startswith('https://') or image_url.startswith('http://'):
            self.id = _id
            self.type = type
            self.image_url = image_url
            self.debug = debug
            self.verbose = verbose
            self.image_size = self.get_dim_img()
        else:
            raise ValueError("You need to indicate an URI of your licence. Need to start by http or https protocols")

    @property
    def redimension(self) -> bool:
        return self.redimension

    @redimension.setter
    def redimension(self, statut):
        if statut is True:
            self.redimension = True
            self.ratio = self.get_ratio(self.dim_img_origin[0], self.dim_img_origin[1])

    def get_dim_img(self) -> namedtuple:
        """
        To get image API dimension
        :param url: str, url image
        :return: tuple with width, height
        """
        response = requests.get(self.image_url)
        img = Image.open(BytesIO(response.content))
        return img.size[0], img.size[1]

    @staticmethod
    def get_dim_manifest(manifest_url: str, img_w: int or float, img_h: int or float) -> bool or tuple:
        """
        To get dimension of original image.
        :param img_w:
        :param manifest_url:
        :return:
        """

        img_manifest = None
        Size = namedtuple('Size', ['w', 'h'])

        json = requests.get(manifest_url).json()

        for page in json['sequences'][0]['canvases']:
            if page['images'][0]['resource']['@id'] == manifest_url:
                img_manifest = Size(h=page['images'][0]['resource']['height'], w=page['images'][0]['resource']['width'])

        assert isinstance(img_manifest, Size), "We can't get the dimension of the canvas of original image in the manifest."

        if img_w != img_manifest.w or img_h != img_manifest.h:
            return True, (img_manifest.w, img_manifest.h)
        else:
            return False, None

    def get_ratio(self, width, height):
        """
        Get dimension ratio of original image in manifest
        :param width:
        :param height:
        :return:
        """
        assert isinstance(width, (float, int)), "Your change status of redimension, but the script can't get the good values [width] of original images."
        assert isinstance(height, (float, int)), "Your change status of redimension, but the script can't get the good values [height] of original images."
        ratio_w = width / self.image_size[0]
        ratio_h = height / self.image_size[1]
        return ratio_w, ratio_h

    def get_colors(self):
        list_colors = {}

        with open("config/Manuscript.json") as f:
            js = json.load(f)
            for ent in js['taxonomy']['descriptors']:
                list_colors[ent['targetName']] = ent['targetColor']

        if self.type not in list(list_colors):
            return Color(list(list_colors.values())).get_new_color()
        else:
            return list_colors[self.type]



class Rectangle(FormSVG):
    def __init__(self, _id, image_url, _type, x, y, w, h, **kwargs):
        super().__init__(_id=_id, image_url=image_url, type=_type, **kwargs)
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def fit(self):
        if self.redimension is False:
            assert isinstance(self.ratio, tuple), "Ratio attribute is None. You need to get a tuple (width, height)"
            self.x *= self.ratio[0]
            self.w *= self.ratio[0]
            self.y *= self.ratio[1]
            self.h *= self.ratio[1]
        return f"""<rect id="{str(self.id)}" x="{str(self.x)}" y="{str(self.y)}" width="{str(self.w)}" height="{str(self.h)}" stroke="{str("color")}" rx="20" ry="20" fill-opacity=0 stroke-width="2px"/>"""


class Marker(FormSVG):
    def __init__(self, _id, image_url, _type, x, y, **kwargs):
        super().__init__(_id=_id, image_url=image_url, type=_type, **kwargs)
        self.x = x
        self.y = y
        self.w = 5
        self.h = 5

    def fit(self):
        if self.redimension is False:
            assert isinstance(self.ratio, tuple), "Ratio attribute is None. You need to get a tuple (width, height)"
            self.x *= self.ratio[0]
            self.y *= self.ratio[1]
        return f"""<path d="M{str(self.x)},{str(self.y)}c0,-3.0303 1.51515,-6.06061 4.54545,-9.09091c0,-2.51039 -2.03507,-4.54545 -4.54545,-4.54545c-2.51039,0 -4.54545,2.03507 -4.54545,4.54545c3.0303,3.0303 4.54545,6.06061 4.54545,9.09091z" id="{self.id}" fill-opacity="0" fill="#00f000" stroke="{str("color")}" stroke-width="2" stroke-linecap="butt" stroke-linejoin="miter" stroke-miterlimit="10"/>"""
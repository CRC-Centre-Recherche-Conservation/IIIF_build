import os

import requests
import json
from collections import namedtuple
from PIL import Image
from io import BytesIO

from src.opt.tools import Color
from path import CONFIG_PATH


class FormSVG(object):
    # Ratio is None or tuple (width, height)
    ratio = None
    dim_img_origin = None

    def __init__(self, _id: str, type: str, image_url: str, debug: bool = False, **kwargs):
        self.redimension = False
        if image_url.startswith('https://') or image_url.startswith('http://'):
            # col 'Name' in csv
            self.id = _id
            # col Type
            self.type = type
            # col References -> API image
            self.image_url = image_url

            # Other
            self.debug = debug
            self.verbose = kwargs['verbose']
            self.image_size = self.get_dim_img()
        else:
            raise ValueError("You need to indicate an URI of your licence. Need to start by http or https protocols")

    @property
    def redimension(self) -> bool:
        return self._redimension

    @redimension.setter
    def redimension(self, statut):
        """
        Property function to return a ratio when image API dimension not correspond to the image dimension in the manifest.
        :param statut: bool
        :return: None
        """
        if statut is True:
            self._redimension = True
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

    def get_dim_manifest(self, _json, img_w: int or float, img_h: int or float) -> None or tuple:
        """
        To get dimension of original image.
        :param _json: the json request of your manifest iiif
        :param img_h: height image's
        :param img_w: width image's
        :return: Bool, tuple(width, height) or None. The boolean is to change
        """

        img_manifest = None
        Size = namedtuple('Size', ['w', 'h'])

        for page in _json['sequences'][0]['canvases']:
            if page['images'][0]['resource']['@id'] == self.image_url:
                img_manifest = Size(h=page['images'][0]['resource']['height'], w=page['images'][0]['resource']['width'])

        assert isinstance(img_manifest,
                          Size), "We can't get the dimension of the canvas of original image in the manifest."

        if img_w != img_manifest.w or img_h != img_manifest.h:
            self.redimension = True
            return img_manifest.w, img_manifest.h
        else:
            return None

    def get_ratio(self, width: float or int, height: float or int) -> float or int:
        """
        Get dimension ratio of original image in manifest
        :param width:
        :param height:
        :return:
        """
        assert isinstance(width, (float,
                                  int)), "Your change status of redimension, but the script can't get the good values [width] of original images."
        assert isinstance(height, (float,
                                   int)), "Your change status of redimension, but the script can't get the good values [height] of original images."
        ratio_w = width / self.image_size[0]
        ratio_h = height / self.image_size[1]
        return ratio_w, ratio_h

    def get_colors(self, list_colors: dict):
        """
        Function to get colors in 'manuscript.json' in config file
        :list_colors:
        :return:
        """

        for file in os.listdir(CONFIG_PATH):
            if file.lower() == 'manuscript.json':
                if self.verbose:
                    print("Parsing config file colors 'manuscript.json'.")
                with open("config/Manuscript.json") as f:
                    js = json.load(f)
                for ent in js['taxonomy']['descriptors']:
                    list_colors[ent['targetName']] = ent['targetColor']

                # if add new type of analysis not in the scheme, but it's better to respect the scheme -> update in config
                if self.type not in list(list_colors):
                    print(f"We don't find the type '{self.type}' in the config file 'manuscript.json'")
                    return Color(list(list_colors.values())).get_new_color()
                else:
                    return list_colors[self.type]

            # If the script don't find 'manuscript.json file in config folder
            else:
                print("We cannot find config file 'manuscript.json' in the config folder")
                print("Generation of color index")
                return Color(list(list_colors.values())).get_new_color()


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

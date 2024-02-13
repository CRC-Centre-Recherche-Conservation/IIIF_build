import requests
from collections import namedtuple
from PIL import Image
from io import BytesIO


class FormSVG(object):
    # Ratio is None or tuple (width, height)
    ratio = None
    dim_img_origin = None

    def __init__(self, _id: str, image_url, **kwargs):
        """
        General initalisation of form class to svg.
        :param _id: Id of your annotation.
        :param type: Type of analysis in your annotation
        :param image_url: str, URI of API image
        :param kwargs: verbose
        """
        self.redimension = False
        # col 'Name' in csv
        self.id = _id
        # Check with Size with request
        self.verbose = kwargs['verbose']
        if image_url is not None:
            assert isinstance(image_url, str), "Variable [image_url] must be of type string to be used."
            if image_url.startswith('https://') or image_url.startswith('http://'):
                # col References -> API image
                self.image_url = image_url
                # tuple (width, height)
                self.image_size = self._get_iiif_dim()
            else:
                raise ValueError("You need to indicate an URI of your licence. "
                                 "Need to start by http or https protocols")

    @property
    def redimension(self) -> bool:
        return self._redimension

    @redimension.setter
    def redimension(self, statut):
        """
        Property function to return a ratio when image API dimension not correspond to the image
        dimension in the manifest.
        :param statut: bool
        :return: None
        """
        if statut is True:
            self._redimension = True
            if self.dim_img_origin is None:
                raise ValueError("Attribute class 'dim_img_origin' don't be none value ")
            else:
                if self.verbose:
                    print(f'Redimension of image {str(self.id)}')
                self.ratio = self._get_ratio(self.dim_img_origin[0], self.dim_img_origin[1])
                print(self.ratio)
                self.fit()

    def _get_dim_img(self) -> namedtuple:
        """
        To get image API dimension with PIL
        :param url: str, url image
        :return: tuple with width, height
        """
        print('WARNING: DEPRECATED !')
        response = requests.get(self.image_url)
        img = Image.open(BytesIO(response.content))
        return img.size[0], img.size[1]

    def _get_iiif_dim(self) -> namedtuple:
        """
        To get image API info dimension
        :param url: str, url image
        :return: tuple with width, height
        """
        info_url = '/'.join(self.image_url.split('/')[:-4]) + '/info.json'
        json_resp = requests.get(info_url).json()
        return json_resp['width'], json_resp['height']

    def _get_ratio(self, width: float or int, height: float or int) -> float or int:
        """
        Get dimension ratio of original image in manifest
        :param width:
        :param height:
        :return:
        """
        assert isinstance(width, (float,
                                  int)), ("Your change status of redimension, but the script can't get the good values "
                                          "[width] of original images.")
        assert isinstance(height, (float,
                                   int)), ("Your change status of redimension, but the script can't get the good values "
                                           "[height] of original images.")
        ratio_w = width / self.image_size[0]
        ratio_h = height / self.image_size[1]
        return ratio_w, ratio_h

    def check_dim_manifest(self, canvas_w: int, canvas_h: int):
        """
        To get dimension of original image.
        :param canvas_w: int, canvas width
        :param canvas_h: int, canvas height
        :param image_size: tuple,
        :return: None
        """
        if self.image_size != (canvas_w, canvas_h):
            # get tuple with original dimension
            self.dim_img_origin = (canvas_w, canvas_h)
            # Indication of change status -> run property function
            self.redimension = True

    def fit(self):
        pass


class Rectangle(FormSVG):
    def __init__(self, _id, x, y, w, h, image_url=None, **kwargs):
        """
        class for rectangle form.
        :param _id: Id of your annotation.
        :param _type: Type of analysis in your annotation
        :param image_url: URI of API image
        :param x: coordinate x
        :param y: coordinate y
        :param w: coordinate w (width)
        :param h: coordinate w (height)
        :param kwargs: verbose (boolean, default is false)
        """
        super().__init__(_id=_id, image_url=image_url, **kwargs)
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def fit(self):
        """
        To fit with API image service dimension
        """
        assert isinstance(self.ratio, tuple), "Ratio attribute is None. You need to get a tuple (width, height)"
        self.x *= self.ratio[0]
        self.w *= self.ratio[0]
        self.y *= self.ratio[1]
        self.h *= self.ratio[1]
    def get_svg(self):
        """
        to build svg object in html with the data of your annotation.
        :return: str, html <rect>
        """
        #return f"""<rect id="{str(self.id)}" x="{str(self.x)}" y="{str(self.y)}" width="{str(self.w)}" height="{str(self.h)}" stroke="{str("color")}" rx="20" ry="20" fill-opacity=0 stroke-width="2px"/>"""
        return f"""<path d="M{self.x},{self.y} L{self.x + self.w},{self.y} L{self.x + self.w},{self.y + self.h} L{self.x},{self.y + self.h} Z" fill-opacity="0" fill="#00f000" stroke="{str("color")}" stroke-width="2" stroke-linecap="butt" stroke-linejoin="miter" stroke-miterlimit="10"/>"""


class Marker(FormSVG):
    def __init__(self, _id, image_url, x, y, **kwargs):
        """
        class for marker form.
        :param _id: Id of your annotation.
        :param _type: Type of analysis in your annotation
        :param image_url: URI of API image
        :param x: coordinate x
        :param y: coordinate y
        :param kwargs: verbose (boolean, default is false)
        """
        super().__init__(_id=_id, image_url=image_url, **kwargs)
        self.x = x
        self.y = y
        self.w = 10
        self.h = 10

    def fit(self):
        """
        To fit with API image service dimension
        """
        assert isinstance(self.ratio, tuple), "Ratio attribute is None. You need to get a tuple (width, height)"
        self.x *= self.ratio[0]
        self.y *= self.ratio[1]

    def get_svg(self):
        """
        to build svg object in html with the data of your annotation.
        :return: str, html <path>
        """
        # !!!!!!!! : passer  à l'échelle, utiliser la fonction scale !!!!!!!!!
        # https://yqnn.github.io/svg-path-editor/
        # base 1:1 "M{str(self.x)},{str(self.y)}c0,-3.0303 1.51515,-6.06061 4.54545,-9.09091c0,-2.51039 -2.03507,-4.54545 -4.54545,-4.54545c-2.51039,0 -4.54545,2.03507 -4.54545,4.54545c3.0303,3.0303 4.54545,6.06061 4.54545,9.09091z" id="{self.id}" fill-opacity="0" fill="#00f000" stroke="{str("color")}" stroke-width="2" stroke-linecap="butt" stroke-linejoin="miter" stroke-miterlimit="10"/>"""
        # ICI base 20:20
        return f"""<path d="M{str(self.x)},{str(self.y)} c 0 -60.606 30.303 -121.2122 90.909 -181.8182 c 0 -50.2078 -40.7014 -90.909 -90.909 -90.909 c -50.2078 0 -90.909 40.7014 -90.909 90.909 c 60.606 60.606 90.909 121.2122 90.909 181.8182 z" fill-opacity="0" fill="#00f000" stroke="{str("color")}" stroke-width="2" stroke-linecap="butt" stroke-linejoin="miter" stroke-miterlimit="10"/>"""
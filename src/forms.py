import requests
from collections import namedtuple
from PIL import Image
from io import BytesIO


class FormSVG(object):
    # Ratio is None or tuple (width, height)
    ratio = None
    dim_img_origin = None

    def __init__(self, _id: str, _type: str, image_url: str, **kwargs):
        """
        General initalisation of form class to svg.
        :param _id: Id of your annotation.
        :param type: Type of analysis in your annotation
        :param image_url: URI of API image
        :param kwargs: verbose
        """
        self.redimension = False
        if image_url.startswith('https://') or image_url.startswith('http://'):
            # col 'Name' in csv
            self.id = _id
            # col Type
            self.type = _type
            # col References -> API image
            self.image_url = image_url
            # tuple (width, height)
            self.image_size = self._get_dim_img()

            # Other
            self.verbose = kwargs.get('verbose', False)
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
            if self.dim_img_origin is None:
                raise ValueError("Attribute class 'dim_img_origin' don't be none value ")
            else:
                if self.verbose:
                    print(f'Redimension of image {str(self.id)}')
                self.ratio = self._get_ratio(self.dim_img_origin[0], self.dim_img_origin[1])
                self.fit()

    def _get_dim_img(self) -> namedtuple:
        """
        To get image API dimension
        :param url: str, url image
        :return: tuple with width, height
        """
        response = requests.get(self.image_url)
        img = Image.open(BytesIO(response.content))
        return img.size[0], img.size[1]

    def _get_ratio(self, width: float or int, height: float or int) -> float or int:
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

    def check_dim_manifest(self, canvas):
        """
        To get dimension of original image.
        :param canvas: canvas json part in manifest
        :return: None
        """

        Size = namedtuple('Size', ['w', 'h'])
        img_manifest = Size(h=canvas['images'][0]['resource']['height'], w=canvas['images'][0]['resource']['width'])

        assert isinstance(img_manifest,
                          Size), "We can't get the dimension of the canvas of original image in the manifest."

        if self.image_size[0] != img_manifest.w or self.image_size[1] != img_manifest.h:
            # get tuple with original dimension
            self.dim_img_origin = (img_manifest.w, img_manifest.h)
            # Indication of change status -> run property function
            self.redimension = True

    def fit(self):
        pass


class Rectangle(FormSVG):
    def __init__(self, _id, image_url, _type, x, y, w, h, **kwargs):
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
        super().__init__(_id=_id, image_url=image_url, _type=_type, **kwargs)
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
        return f"""<rect id="{str(self.id)}" x="{str(self.x)}" y="{str(self.y)}" width="{str(self.w)}" height="{str(self.h)}" stroke="{str("color")}" rx="20" ry="20" fill-opacity=0 stroke-width="2px"/>"""


class Marker(FormSVG):
    def __init__(self, _id, image_url, _type, x, y, **kwargs):
        """
        class for marker form.
        :param _id: Id of your annotation.
        :param _type: Type of analysis in your annotation
        :param image_url: URI of API image
        :param x: coordinate x
        :param y: coordinate y
        :param kwargs: verbose (boolean, default is false)
        """
        super().__init__(_id=_id, image_url=image_url, _type=_type, **kwargs)
        self.x = x
        self.y = y
        self.w = 5
        self.h = 5

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
        return f"""<path d="M{str(self.x)},{str(self.y)}c0,-3.0303 1.51515,-6.06061 4.54545,-9.09091c0,-2.51039 -2.03507,-4.54545 -4.54545,-4.54545c-2.51039,0 -4.54545,2.03507 -4.54545,4.54545c3.0303,3.0303 4.54545,6.06061 4.54545,9.09091z" id="{self.id}" fill-opacity="0" fill="#00f000" stroke="{str("color")}" stroke-width="2" stroke-linecap="butt" stroke-linejoin="miter" stroke-miterlimit="10"/>"""
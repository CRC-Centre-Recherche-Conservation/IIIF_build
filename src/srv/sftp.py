#### CREDITS ####
#### Crazy Ant Labs ####
#### https://github.com/crazyantlabs/sftptogo-examples/blob/main/snippets/python/py-sftp/sftp.py.mustache ####

import os
import re
import platform
import paramiko
from PIL import Image
from io import BytesIO
from collections import defaultdict, namedtuple
from urllib.parse import urlparse

# Configure path
current_path = os.path.dirname(os.path.abspath(__file__))


class Sftp:
    def __init__(self, hostname, username, password, port=22, client=None, verbose=False):
        """Constructor Method"""
        # Set connection object to None (initial value)
        if client is None:
            self.client = paramiko.client.SSHClient()
        else:
            self.client = client
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.verbose = verbose

    def connect(self):
        """Connects to the sftp server and returns the sftp connection object"""

        try:
            # Get the sftp connection object
            self.client.connect(
                hostname=self.hostname,
                username=self.username,
                password=self.password,
                port=self.port,
            )
            self.sftp = self.client.open_sftp()
        except Exception as err:
            raise Exception(err)
        finally:
            if self.verbose:
                print(f"Connected to {self.hostname} as {self.username}.")

    def disconnect(self):
        """Closes the sftp connection"""
        self.client.close()
        if self.verbose:
            print(f"Disconnected from host {self.hostname}")

    def listdir(self, remote_path):
        """lists all the files and directories in the specified path and returns them"""
        sftp = self.client.open_sftp()
        for obj in sftp.listdir(remote_path):
            yield obj

    def upload(self, source_local_path, remote_path):
        """
        Uploads the source files from local to the sftp server.
        """
        try:
            if self.verbose:
                print(
                    f"uploading to {self.hostname} as {self.username} [(remote path: {remote_path});(source local path: {source_local_path})]")

            # Download file from SFTP
            self.sftp.put(source_local_path, remote_path)
            if self.verbose:
                print("upload completed")

        except Exception as err:
            print(err)

    def exists(self, path):
        try:
            self.sftp.stat(path)
            return True
        except IOError:
            return False

    @staticmethod
    def prepare_images() -> defaultdict:
        # recuperer l'id dans le dictionnaire
        # recuperer la liste d'images et mettre dans une liste
        # envoyer les images dans le dossier (projet/id_analysis+nom_fichier)
        # return dataframe avec id, url de la premiere image, list des images a mettre en calque

        # Variables
        data_files = os.path.join("data", "data_files")
        anl_patter = re.compile(r"((?:HS_SWIR_|HS_VNIR_|sXRF_)\d+)")
        idx_analysis = defaultdict(list)
        # Search all id analysis
        for path, subdirs, files in os.walk(data_files, topdown=True):
            for name in files:
                path_image = os.path.join(path, name)
                search_path = re.search(anl_patter, path_image)
                if search_path:
                    id_ = search_path.group(0)
                    idx_analysis[id_].append(path_image)
        return idx_analysis

    @classmethod
    def upload_images(cls, project: str, id_: str, imgs: list, path_remote='/home/rayondemiel/iiif/images/', security=False, **kwargs):

        # export IIIFSRV_URL = 'sftp://user:password@host'
        sftp_url = os.environ.get("IIIFSRV_URL")  # URI format: sftp://user:password@host

        if not sftp_url:
            raise ValueError(
                "First, please set environment variable IIIFSRV_URL and try again. URI SCHEME : sftp://user:password@host")

        # parse sftp url to get all attributes
        parsed_url = urlparse(sftp_url)

        sftp = cls(
            hostname=parsed_url.hostname,
            username=parsed_url.username,
            password=parsed_url.password,
            verbose=kwargs['verbose']
        )

        # Connect to SFTP
        sftp.connect()

        # build dir project
        path_project = os.path.join(path_remote, project)
        if sftp.exists(path_project) is True and security is True:
            print(f"The project '{project}' already exists. Existing files could be damaged.")
            input_path = input('Do you want to continue ? [y/n]').lower()
            if input_path == 'n':
                sftp.disconnect()
                exit(0)
        elif sftp.exists(path_project) is False and security is False:
            sftp.sftp.mkdir(path_project)

        print('test')

        for img in imgs:
            if platform.system() == 'Windows':
                name_file = img.split('\\')[-1]
            else:
                name_file = img.split('/')[-1]
            sftp.upload(img, path_project + '/' + id_ + '&' + name_file)

        print(f'Successful uploads for all images of {id_}')
        # Disconnect from SFTP
        sftp.disconnect()

    @classmethod
    def get_list_dir(cls, project: str, path_remote='/home/rayondemiel/iiif/images/'):

        # export IIIFSRV_URL = 'sftp://user:password@host'
        sftp_url = os.environ.get("IIIFSRV_URL")  # URI format: sftp://user:password@host

        if not sftp_url:
            raise ValueError(
                "First, please set environment variable IIIFSRV_URL and try again. URI SCHEME : sftp://user:password@host")

        # parse sftp url to get all attributes
        parsed_url = urlparse(sftp_url)

        sftp = cls(
            hostname=parsed_url.hostname,
            username=parsed_url.username,
            password=parsed_url.password
        )

        sftp.connect()
        path_remote = path_remote + project
        file_list = list(sftp.listdir(path_remote))

        def get_size(path_img: str):
            "To get size of images"
            Size = namedtuple('Size', ['weight', 'height'])
            with sftp.sftp.open(path_img) as f:

                #print('hello')
                print(f)
                #img = Image.open(BytesIO(f.content))
            #return Size(weight=img.size[0], height=img.size[1])

        # build dict with size for any images
        dict_files = {}
        for img in file_list:
            size = get_size(path_remote + img)
            dict_files[img] = size

        del file_list
        sftp.disconnect()
        return dict_files



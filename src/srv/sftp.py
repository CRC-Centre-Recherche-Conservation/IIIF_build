#### CREDITS ####
#### Crazy Ant Labs ####
#### https://github.com/crazyantlabs/sftptogo-examples/blob/main/snippets/python/py-sftp/sftp.py.mustache ####

import os
import re
import platform
import pysftp
from collections import defaultdict
from urllib.parse import urlparse

# Configure path
current_path = os.path.dirname(os.path.abspath(__file__))


class Sftp:
    def __init__(self, hostname, username, password, port=22, **kwargs):
        """Constructor Method"""
        # Set connection object to None (initial value)
        self.connection = None
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.verbose = kwargs['verbose']

    def connect(self):
        """Connects to the sftp server and returns the sftp connection object"""

        try:
            # Get the sftp connection object
            self.connection = pysftp.Connection(
                host=self.hostname,
                username=self.username,
                password=self.password,
                port=self.port,
            )
        except Exception as err:
            raise Exception(err)
        finally:
            print(f"Connected to {self.hostname} as {self.username}.")

    def disconnect(self):
        """Closes the sftp connection"""
        self.connection.close()
        print(f"Disconnected from host {self.hostname}")

    def listdir(self, remote_path):
        """lists all the files and directories in the specified path and returns them"""
        for obj in self.connection.listdir(remote_path):
            yield obj

    def listdir_attr(self, remote_path):
        """lists all the files and directories (with their attributes) in the specified path and returns them"""
        for attr in self.connection.listdir_attr(remote_path):
            yield attr

    def upload(self, source_local_path, remote_path):
        """
        Uploads the source files from local to the sftp server.
        """

        try:
            if self.verbose:
                print(
                    f"uploading to {self.hostname} as {self.username} [(remote path: {remote_path});(source local path: {source_local_path})]")

            # Download file from SFTP
            self.connection.put(source_local_path, remote_path)
            print("upload completed")

        except Exception as err:
            raise Exception(err)

    def download(self, remote_path, target_local_path):
        """
        Downloads the file from remote sftp server to local.
        Also, by default extracts the file to the specified target_local_path
        """

        try:
            if self.verbose:
                print(
                    f"downloading from {self.hostname} as {self.username} [(remote path : {remote_path});(local path: {target_local_path})]")

            # Create the target directory if it does not exist
            path, _ = os.path.split(target_local_path)
            if not os.path.isdir(path):
                try:
                    os.makedirs(path)
                except Exception as err:
                    raise Exception(err)

            # Download from remote sftp server to local
            self.connection.get(remote_path, target_local_path)
            print("download completed")

        except Exception as err:
            raise Exception(err)

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

    @staticmethod
    def upload_images(project: str, id_: str, imgs: list, path_remote='/home/rayondemiel/iiif/images/', security=True):

        # export IIIFSRV_URL = 'sftp://user:password@host'
        sftp_url = os.environ.get("IIIFSRV_URL")  # URI format: sftp://user:password@host

        if not sftp_url:
            raise ValueError(
                "First, please set environment variable IIIFSRV_URL and try again. URI SCHEME : sftp://user:password@host")

        # parse sftp url to get all attributes
        parsed_url = urlparse(sftp_url)

        sftp = Sftp(
            hostname=parsed_url.hostname,
            username=parsed_url.username,
            password=parsed_url.password,
        )

        # Connect to SFTP
        sftp.connect()

        # build dir project
        path_project = os.path.join(path_remote, project.lower())
        if sftp.connection.exists is True and security is True:
            print(f"The project '{project}' already exists. Existing files could be damaged.")
            input_path = input('Do you want to continue ? [y/n]').lower()
            if input_path == 'n':
                sftp.disconnect()
                exit(0)
        else:
            sftp.connection.makedirs(path_project)

        for id_img in imgs:
            if platform.system() == 'Windows':
                name_file = id_img.split('\\')[-1]
            else:
                name_file = id_img.split('/')[-1]
            print(path_project + '/' + id_img + '&' + name_file)
            sftp.upload(id_img, path_project + '/' + id_img + '&' + name_file)
        # Disconnect from SFTP
        sftp.disconnect()

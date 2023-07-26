#### CREDITS ####
#### Crazy Ant Labs ####
#### https://github.com/crazyantlabs/sftptogo-examples/blob/main/snippets/python/py-sftp/sftp.py.mustache ####

import pysftp
from urllib.parse import urlparse
import os

# Configure path
current_path = os.path.dirname(os.path.abspath(__file__))


class Sftp:
    def __init__(self, hostname, username, password, port=22):
        """Constructor Method"""
        # Set connection object to None (initial value)
        self.connection = None
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port

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
            print(
                f"uploading to {self.hostname} as {self.username} [(remote path: {remote_path});(source local path: {source_local_path})]"
            )

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
            print(
                f"downloading from {self.hostname} as {self.username} [(remote path : {remote_path});(local path: {target_local_path})]"
            )

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
    def upload_images(project: str, analysis: str, path_remote='/home/rayondemiel/iiif/images/'):

        # hps = hyperspectral
        # sxrf = scans XRF
        # faire un script pour lire à partir du YAML les images devant être publiées sur serveur IIIF
        if analysis.lower() not in ['hps', 'sxrf']:
            raise ValueError('Need to corresponding to hyperspectral (HPS) or XRF scans (sXRF)')

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
        path_project = os.path.join(path_remote, project.lower(), analysis.lower())
        if sftp.connection.exists:
            print('The project exists.')
            input_path = input('Do you want to continue ? [y/n]').lower()
            if input_path == 'n':
                exit(0)
        else:
            sftp.connection.makedirs(path_project)

        path_dir_data = 'xrf' if analysis.lower() == 'sxrf' else 'hps'

        for file in os.listdir('data'):
            if os.path.isfile(os.path.join("data", path_dir_data, project.lower(), file)) and file.endswith('.tif'):
                print(file)

        # Disconnect from SFTP
        sftp.disconnect()


if __name__ == "__main__":
    Sftp.upload_images(project='ms_blabla', analysis='sXRF')
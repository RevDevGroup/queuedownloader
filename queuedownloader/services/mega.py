from ._base import DownloaderService, execute_behaviour
from os import path
from mega import Mega

class MegaService(DownloaderService):
    name = "MegaService"

    def __init__(self, *args, **kwargs):
        super(MegaService, self).__init__(*args, **kwargs)

        self.accounts = kwargs.get("accounts", [])
        self.output = path.join(self.directory, path.basename(self.url))

    @execute_behaviour
    def execute(self):
        api = Mega()

        if self.authuser and self.authpasswd:
            api.login(self.authuser, self.authpasswd)
        else:
            api.login_anonymous()

        api.download_url(self.url, dest_filename=self.output)

    @staticmethod
    def filesize(url, authuser=None, authpasswd=None):
        api = Mega()
        info = api.get_public_url_info(url)
        
        return info["size"]

    @staticmethod
    def supported(url):
        if isinstance(url, str):
            if url.startswith("https://mega.nz") or url.startswith("https://mega.co.nz"):
                return True
        else:
            raise TypeError("url should be a str")

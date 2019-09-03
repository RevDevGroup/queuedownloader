from .._base import DownloaderService, execute_behaviour
from os import path, getcwd, remove
from json import loads, dumps
from uuid import uuid4
from re import fullmatch

class PlayStoreService(DownloaderService):   
    name = "PlayStoreService"

    def __init__(self, *args, **kwargs):
        super(PlayStoreService, self).__init__(*args, **kwargs)        
        
        self.output = path.join(self.directory, path.basename(self.url) + ".apk")
        self.download_obb = kwargs.get("download_obb", True)
        
        with open(path.abspath(path.join(getcwd(), "config/credentials.json")), "r") as file:
            credentials = loads(file.read())[0]           
           
        config = {}
        config["USERNAME"] = kwargs.get("authuser", credentials["USERNAME"])
        config["PASSWORD"] = kwargs.get("authpasswd", credentials["PASSWORD"])
        config["ANDROID_ID"] = kwargs.get("android_id", credentials["ANDROID_ID"])
        config["LANG_CODE"] = kwargs.get("langcode", credentials["LANG_CODE"])
        config["LANG"] = kwargs.get("lang", credentials["LANG"])
        config["SDK_VERSION"] = kwargs.get("sdk_version", credentials["SDK_VERSION"])

        self.temp_file = path.abspath(path.join(getcwd(), "assets/%s.json" % str(uuid4())))

        with open(self.temp_file, "w") as file:
            file.write(dumps([config]))

    @execute_behaviour
    def execute(self):       
        try:
            # import play store module
            from .playstore import Playstore            
            api = Playstore(self.temp_file.strip(' \'"'))

            try:
                app = api.app_details(self.url).docV2
            except AttributeError:
                raise Exception("Error when downloading %s: unable to get app's details" % 
                    (self.url.strip(' \'"')))
                        
            details = {
                'package_name': app.docid,
                'title': app.title,
                'creator': app.creator
            }
            
            return api.download(details['package_name'], self.output, 
                                        download_obb=self.download_obb)
        finally:
            # remove temp file
            try:
                remove(temp_file)
            except:
                pass

    @staticmethod
    def supported(url):
        if isinstance(url, str):
            if url.startswith("https://play.google.com") or fullmatch(r"^[A-Za-z0-9]+\.[A-Za-z0-9]+\.[A-Za-z0-9]+$", url):
                return True
        else:
            raise TypeError("url should be a str")
        
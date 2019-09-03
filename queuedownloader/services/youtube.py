from ._base import DownloaderService
from youtube_dl import YoutubeDL

class YouTubeService(DownloaderService):   
    name = "YouTubeService"

    def __init__(self, *args, **kwargs):
        super(YouTubeService, self).__init__(*args, **kwargs)
        
        self.subtitles = kwargs.get("subtitles", True)
        self.subtitles_lang = kwargs.get("subtitles_lang", "spanish")

    
    @staticmethod
    def supported(url):
        if isinstance(url, str):
            if url.startswith("https://youtube.com/") or url.startswith("https://youtu.be/"):
                return True
        else:
            raise TypeError("url should be a str")
        
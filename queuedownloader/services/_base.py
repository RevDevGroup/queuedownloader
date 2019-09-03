from functools import wraps

def execute_behaviour(func):
    @wraps(func)
    def wrapper(self):
        self.running = True

        try:
            return func(self)
        except Exception as e:
            raise e
        finally:
            self.running = False
    
    #copy documentation data
    wrapper.__doc__ = func.__doc__
    wrapper.__name__ = func.__name__
    wrapper.__annotations__ = func.__annotations__
    return wrapper

class DownloaderService(object):
    # Name of service
    name = "DownloadService"

    def __init__(self, *args, **kwargs):
        self.running = False

        if len(args) < 2:
            raise Exception("the service need url and directory to save for correct download")

        self.url, self.directory = args
        
        self.authuser = kwargs.get("authuser", None)
        self.authpasswd = kwargs.get("authpasswd", None)

    @execute_behaviour
    def execute(self):
        """
        Execute service rutine. Block execution
        """
        raise NotImplementedError("implement download service")

    def cancel(self):
        """
        Cancel current download.
        """
        pass

    def wait(self):
        while self.running:
            pass

    @property
    def progress(self):
        raise NotImplementedError("implement download service")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.wait()
        return False

    @staticmethod
    def supported(url):
        return False

    @staticmethod
    def filesize(url, authuser=None, authpasswd=None):
        """
        Get the file size of file
        """
        return None
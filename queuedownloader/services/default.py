from ._base import DownloaderService, execute_behaviour
from subprocess import Popen, PIPE
from os import path, name as osname
import re

class DefaultService(DownloaderService):
    name = "DefaultService"    

    def __init__(self, *args, **kwargs):
        # setting default values
        super(DefaultService, self).__init__(*args, **kwargs)

        output = path.join(self.directory, path.basename(self.url))

        # if windows os invoke wget instance in windows subsystem linux
        # only for debug
        # use the unix path system
        if osname == "nt":
            output = output.replace("\\", "/")
            output = re.sub(r"(?P<Letter>[A-Z]):/", r"/mnt/\1/", output).lower()

        self.wget_args = ["wget", "--quiet", "--continue",
                "--output-document=%s" % output]

        # if windows os invoke wget instance in windows subsystem linux
        # only for debug
        if osname == "nt":
            self.wget_args = ["wsl", "-e"] + self.wget_args

        if self.authuser and self.authpasswd:
            self.wget_args.append("--user=" + str(self.authuser))
            self.wget_args.append("--password=" + str(self.authpasswd))

        self.wget_args.append(self.url)        

    @execute_behaviour
    def execute(self):
        self.cancelled = False
        
        self._wget = Popen(self.wget_args)
        self._wget.wait()

        # if process was cancelled
        if self.cancelled:
            return False

        elif self._wget.returncode == 1:
            raise Exception("Generic error code.")
        elif self._wget.returncode == 2:
            raise Exception("Parse error.")
        elif self._wget.returncode == 3:
            raise Exception("File I/O error.")
        elif self._wget.returncode == 4:
            raise Exception("Network failure.")
        elif self._wget.returncode == 5:
            raise Exception("SSL verification failure.")
        elif self._wget.returncode == 6:
            raise Exception("Username/password authentication failure.")
        elif self._wget.returncode == 7:
            raise Exception("Protocol errors.")
        elif self._wget.returncode == 8:
            raise Exception("Server issued an error response.")

        # return true if wget instance return 0
        return self._wget.returncode == 0

    def cancel(self):
        if self.running:            
            self._wget.kill()
            
            self.cancelled = True
            self.running = False

    @staticmethod
    def filesize(url, authuser=None, authpasswd=None):
        try:
            from requests import head

            auth = None
            if authuser and authpasswd:
                auth = (authuser, authpasswd)

            r = head(url, auth=auth, timeout=5) # max wait 5 seconds

            if "content-length" in r.headers:
                return r.headers['content-length']
            else:
                return None
        except Exception:
            try:
                # dont have requests module using curl
                args = ["curl", "--head", url]

                if authuser and authpasswd:
                    args.extend(["--user", "%s:%s" % (authuser, authpasswd)])

                with Popen(args, stdout=PIPE, stderr=PIPE) as curl:
                    out, err = curl.communicate(
                        timeout=5)  # max wait 5 seconds
                    for line in out.splitlines():
                        if b"Content-Length" in line:
                            length = line.split(b' ')[1]
                            if length.isdigit():
                                return int(length)

                    return None
            except Exception:
                return None

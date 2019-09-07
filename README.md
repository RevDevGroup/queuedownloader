# queuedownload
A download queue that use multithreading for download resources from internet

* Support add services of download, by default contains Mega, Play Store, Youtube, and others services
* Easy to use
* Small

## Installation
For install the most updated version:
```
$ git clone https://github.com/jorgeajimenezl/queuedownloader.git
$ cd queuedownloader
$ git submodule update --init --recursive
$ pip install -e .
```

We periodically publish source code and wheels [on PyPI](https://pypi.python.org/pypi/queuedownloader).
```
$ pip install queuedownloader
```

## Usage
By defult when you add task to queue the service is detected and use anonymous 
login if necessary

```python
with DownloadQueueManager() as m:
    m.addtask("user1", "https://subdomain.domain.com/folder/resource.extension")
    m.addtask("user2", "https://mega.nz/someurl")
    m.addtask("user3", "https://youtu.be/someurl")

    with m.snapshot():
        for info in m.queueinfo():
            print (info)
```

but each service have its parameters

```python
with DownloadQueueManager() as m:
    m.addtask("user1", "com.music.spotify", service=PlayStoreService, authuser="someuser@gmail.com", authpasswd="somerarepassword", sdk_version=24)
    m.addtask("user2", "https://youtu.be/someurl", service=YoutubeService, subtitles=True, quality="720p@60")
```

and every service have common parameters some as authuser, authpasswd, and others

```python
with DownloadQueueManager() as m:
    m.addtask("user1", "https://subdomain.domain.com/somebigfile", sha1="9ccbdefd64d10dc92629e0c3a3dc224285fed9ba")
    m.addtask("user2", "https://mega.nz/someurl", retrycount=10)
    m.addtask("user3", "https://youtu.be/someurl", authuser="someuser@gmail.com", authpasswd="somemostrarepassword")
```

## Authors: 
> Jorge Alejandro Jimenez Luna jorgeajimenezl@nauta.cu  
> Jimmy Angel Pérez Díaz jimscope@protonmail.com

## Support Us:
[![ko-fi](https://www.ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/V7V512ZVF)

from concurrent.futures.thread import ThreadPoolExecutor
from uuid import uuid1, UUID
from threading import Lock, RLock
from os import stat, path, getcwd, makedirs
from json import dumps, loads
import contextlib
from datetime import datetime
from collections import namedtuple

import sys
import logging

from .services import (DownloaderService, DefaultService, 
                        MegaService, PlayStoreService)
from .utils import memoize_when_activated

DEFAULT_SERVICES = [MegaService, PlayStoreService]

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("queuedownloader")
logger.setLevel(logging.DEBUG)

class DownloadQueueManager(object):
    def __init__(self, max_threads=4, oncts=None):
        self._queue = []  # list
        self._executor = ThreadPoolExecutor(max_workers=max_threads)
        self._tasks_info = {}
        self._tasks = {}
        self._services = {}
        self._directorySaveBase = path.join(getcwd(), "downloaded")
        # use for retries downloads and cannot cancelled because the task always are beging
        # use set for best perfomace (hash)
        self._cancelled_task = set()
        self._oncts = oncts
        self._lock = RLock()

    def getservice(self, url):
        for service in DEFAULT_SERVICES:
            if service.supported(url):
                return service

        #raise Exception("dont are service available to download this resource")
        return DefaultService

    def _worker(self, key):
        t = self._tasks_info[key]
        user_directory = path.join(self._directorySaveBase, t["username"])

        if issubclass(t["service"], DownloaderService):
            if not path.exists(user_directory):
                makedirs(user_directory)

            with t["service"](t["url"], user_directory, **t) as s:
                self._services[key] = s
                return s.execute()
        else:
            raise TypeError(
                "'service' param should be a DownloaderService subclass")

    def _addservicetask(self, **kwargs):
        #setting default values
        kwargs["service"] = kwargs.get("service", self.getservice(kwargs["url"]))
        kwargs["retrycount"] = kwargs.get("retrycount", 4)
        kwargs["filesize"] = kwargs.get("filesize", kwargs["service"].filesize(kwargs["url"]))
        
        key = uuid1()

        self._queue.append(key)
        self._tasks_info[key] = kwargs

        w = self._executor.submit(self._worker, key)
        w.add_done_callback(lambda x: self._completework(x, key))

        # if task is running, set a task value
        if not w.done():
            self._tasks[key] = w

        return key

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
        return False

    @memoize_when_activated
    def queueinfo(self):
        ret = []

        for key in self._queue:
            t = self._tasks_info[key]
            # dict in following order:
            # uuid, username, url, progress, file size, running
            # dont use yield because don't know if generator is cachable
            run = False

            if key in self._tasks:
                run = self._tasks[key].running()

            ret.append(dict(
                id=key,
                username=t["username"],
                url=t["url"],
                progress=None,  # implement this
                filesize=t["filesize"],
                running=run
            ))

        return ret

    @contextlib.contextmanager
    def snapshot(self):
        """
        Capture all information
        >>> with q.snapshot():
        ...     for info in q.queueinfo():
        ...         print (info)
        """
        with self._lock:
            if hasattr(self, "_cache"):
                yield
            else:
                try:
                    # add all memorizable calls
                    self.queueinfo.cache_activate(self)
                    yield
                finally:
                    self.queueinfo.cache_deactivate(self)

    """ def _sha1check(self, path, hash):
        if isinstance(hash, str) and isinstance(path, str):        
            with open(path, 'rb', buffering=0) as f:
                return hashlib.sha1(f.readall()).hexdigest() == hash.lower()
        else:
            raise TypeError("'hash' and 'path' params should be a str")   """

    def _completework(self, x, key):
        if x.cancelled() or key in self._cancelled_task:
            self._cancelled_task.remove(key)
            logger.info("task %s cancelled", key)
        else:
            t = self._tasks_info[key]
            complete = None

            try:
                complete = x.result()

                # sha1 comprobation
                """ if complete and t.sha1:
                    #files very long are very slow
                    outputpath = path.join(self._directorySave % t.usernamemk, path.basename(t.url))
                    if stat(output).st_size <= 500000000: #50MB
                        complete = self._sha1check(outputpath, t.sha1) """

                if complete:
                    logger.info("task %s completed", key)

                    if callable(self._oncts):  # called if complete task
                        self._oncts('complete', (t["username"], t["url"]))
            except Exception:
                pass

            if not complete:
                e = x.exception()

                if t["retrycount"] > 1 and self.restarttask(key):
                    logger.info("task %s fail attempt %d with exception: %s", key, 
                            t["retrycount"] + 1, e)

                    if callable(self._oncts):  # called if task was restarted
                        self._oncts('retry', (t["username"], t["url"]))

                    return  # if restart is successful, skip next lines
                else:
                    logger.info("task %s is not complete after raise exception: %s", key, e)

                    if callable(self._oncts):  # called if full fail task
                        self._oncts('fail', (t["username"], t["url"]))

        try:
            # remove all if task is complete or cannot retry
            self._queue.remove(key)  # remove from queue of tasks
            self._tasks_info.pop(key)  # remove from information list
            self._tasks.pop(key)  # remove task from currents tasks
            self._services.pop(key)  # remove from services running list
        except Exception:
            pass

    def canceltask(self, key):
        """
        Cancel the task

        :param key: uuid of task
        """

        #for safe calls
        if not isinstance(key, UUID):
            key = UUID(key)

        try:
            # not always the download service are started
            if key in self._services:
                # remove from services running list and cancel
                self._services.pop(key).cancel()

            self._cancelled_task.add(key)

            # remove from tasks list and return if is cancellable
            if self._tasks.pop(key).cancel():
                self._queue.remove(key)  # remove from queue of tasks
                self._tasks_info.pop(key)  # remove from information list
                return True
            else:
                return False
        except:
            return False

    def restarttask(self, key):
        """
        Restart the task. Return is True if operation is complete otherwise return False
        False return rasons: id don't exists; starting task; ending task; is completed

        :param key: uuid of task
        """

        #for safe calls
        if not isinstance(key, UUID):
            key = UUID(key)

        # if task don't contained in queue cannot restarted
        if not key in self._queue:
            return False

        # if task are cancelled
        if key in self._cancelled_task:
            self._cancelled_task.remove(key)
            return False

        try:
            # if task is running stop
            if key in self._tasks:
                # if task cancelled cannot restart taks
                if self._tasks[key].cancelled():
                    return False

                # if task is begin execution (is not completed and can be canceled)
                if not self._tasks[key].done() and not self._tasks[key].cancel():
                    return False

                # wait end task
                while not self._tasks[key].done():
                    pass

            self._queue.remove(key)  # delete from left side
            self._queue.append(key)  # insert at right

            self._tasks_info[key]["retrycount"] -= 1

            w = self._executor.submit(self._worker, key)
            w.add_done_callback(lambda x: self._completework(x, key))

            # if task is running, set a task value
            if not w.done():
                self._tasks[key] = w

            return True
        except Exception:
            return False

    def waitall(self):
        while len(self._tasks) > 0:
            pass

    def shutdown(self, wait=True):
        """
        Shutdown the queue. After call this method 
        you cannot add task to queue

        :param wait: wait while all tasks are completed
        """
        if wait:
            self.waitall()
        else:
            # cancell all tasks
            for key in self._queue:
                self.canceltask(key)

        # turn off worker
        self._executor.shutdown(wait)

    def savequeue(self, path):
        """
        Save queue to json file

        :param path: path of the json to save queue info
        """
        data = []

        for key in self._queue:
            t = self._tasks_info[key].copy()
            t["service"] = t["service"].name
            data.append(t)

        with open(path, "w") as f:
            f.write(dumps(data))

    def loadqueue(self, path):
        """
        Load queue save from json file and add to current queue

        :param path: path of the json to load queue info
        """
        data = []
        with open(path, "r") as file:
            data = loads(file.read())

        for info in data:          
            for service in DEFAULT_SERVICES:
                if service.name == info["service"]:
                    self._addservicetask(**info)
                    break

    def addtask(self, username, url, **kwargs):
        """
        Add download task to queue.
        Warning: This call can block by 5 seconds for get size of file if this is don't specific.

        :param username: used for identificate.
        :param url: uri of resource to download.
        :param service: download service to use (class)
        :param sha1: sha1 for check if download is successful [Algorithm SHA1].
        :param authuser: [opcional] used for resources protected with authentication service.
        :param username: [opcional] used for resources protected with authentication service.
        :param retrycount: - Used for restart download if fail.
        """
        for i in [username, url, kwargs.get("sha1"), kwargs.get("authuser"), kwargs.get("authpasswd")]:
            if i and not isinstance(i, str):
                raise TypeError(
                    "username, url, sha1, authuser, authpasswd params should be a str")

        if not isinstance(kwargs.get("retrycount", 0), int):
            raise TypeError("'retrycount' param should be a int")

        if "service" in kwargs and\
            issubclass(kwargs["service"], DownloaderService) and\
            not kwargs["service"].supported(url):
                raise Exception("this service cannot support for this url")            

        return self._addservicetask(
                username=username,
                url=url,                
                **kwargs
            )    
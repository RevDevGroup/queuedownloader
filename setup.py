import re
from setuptools import setup, find_packages

version = ''
with open('queuedownloader/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

INSTALL_REQUIRES = (
    ["requests", "mega.py", "youtube_dl", "protobuf", "pycryptodome"]
)

with open('README.md') as readme:
    setup(
        name='queuedownloader',
        version=version,
        description="A download queue that use multithreading for download resources from internet",
        long_description=readme.read(),
        license="MIT License",
        author="Jorge Alejandro Jimenez Luna, Jimmy Angel Perez Diazu",
        author_email="jorgeajimenezl@nauta.cu",
        url="https://github.com/jorgeajimenezl/queuedownloader",
        classifiers=[
            "Intended Audience :: Developers",
            "License :: MIT License",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3.7",
            "Topic :: Internet :: Downloader",
        ],
        keywords="internet, download, queue, queuedownloader",
        install_requires=INSTALL_REQUIRES,
        test_suite="test.app",
        packages=[
            "queuedownloader", 
            "queuedownloader.services"
        ],
        package_dir={'queuedownloader': 'queuedownloader'},
        zip_safe=False,
    )
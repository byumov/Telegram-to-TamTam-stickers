import codecs
import os.path
from setuptools import setup, find_packages

PKG_NAME = 'tg_to_tt_stickers'

def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()

# https://packaging.python.org/guides/single-sourcing-package-version/
def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")

setup(
    name=PKG_NAME,
    packages=find_packages(where="src"),
    install_requires=[
        "webp==0.1.3",
        "pillow==9.3.0",
        "requests==2.25.1",
        "aiohttp==3.8.1",
    ],
    package_dir={"": "src"},
    author='Ivan Buymov',
    author_email='ivan@buymov.ru',
    version=get_version(f"src/{PKG_NAME}/__init__.py"),
    entry_points = {
        'console_scripts': ['tg-to-tt-bot=tg_to_tt_stickers.run:run'],
    },
    description="TamTam bot which can convert Telegram stickers" \
                "to TamTam format and helps to upload to TamTam",
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
    url='https://github.com/byumov/Telegram-to-TamTam-stickers'
)

from setuptools import setup, find_packages
PKG_NAME = 'tg_to_tt_stickers'


setup(
    name=PKG_NAME,
    packages=find_packages(where="src"),
    install_requires=[
        "webp==0.1.3",
        "pillow==8.4.0",
        "requests==2.25.1",
        "aiohttp==3.7.4",
    ],
    package_dir={"": "src"},
    author='Ivan Buymov',
    author_email='ivan@buymov.ru',
    version="0.0.1",
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

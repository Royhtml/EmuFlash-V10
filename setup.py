from setuptools import setup, find_packages
import os
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md'), 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="emuflash",
    version="10.0",
    author="Dwi Bakti N Dev",
    author_email="dwibakti76@gmail.com",
    description="A lightweight retro emulator featuring over 250 fully patched games, designed for effortless play with no PC-specific configuration required.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/royhtml",
    project_urls={
        "Profile": "https://profiledwibaktindev.netlify.app/",
        "ich.io": "https://royhtml.itch.io/",
        "Facebook": "https://www.facebook.com/Royhtml",
        "Webtoons": "https://www.webtoons.com/id/canvas/mariadb-hari-senin/episode-4-coding-championship/viewer?title_no=1065164&episode_no=4",
    },
    packages=find_packages(exclude=['tests*']),
    install_requires=[
        "pillow>=8.0",
        "pyinstaller>=4.0",
        "pyqt5>=5.15",
    ],
    entry_points={
        "gui_scripts": [
            "emuflash = emuflash.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "emuflash": ["*.ico", "*.png"],
    },
    classifiers=[
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",

    "Topic :: Games/Entertainment",
    "Topic :: Games/Entertainment :: Arcade",
    "Topic :: Multimedia :: Graphics",
    "Intended Audience :: End Users/Desktop",
    ],
    python_requires=">=3.6",
)

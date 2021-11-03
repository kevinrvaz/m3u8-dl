# m3u8-dl
[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/)
[![PyPI version](https://badge.fury.io/py/m3u8dl.svg)](https://badge.fury.io/py/m3u8dl)
[![Docker](https://github.com/excalibur-kvrv/m3u8-dl/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/excalibur-kvrv/m3u8-dl/actions/workflows/docker-publish.yml)
[![CodeQL](https://github.com/excalibur-kvrv/m3u8-dl/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/excalibur-kvrv/m3u8-dl/actions/workflows/codeql-analysis.yml)
[![Upload Python Package](https://github.com/excalibur-kvrv/m3u8-dl/actions/workflows/python-publish.yml/badge.svg)](https://github.com/excalibur-kvrv/m3u8-dl/actions/workflows/python-publish.yml)
[![Downloads](https://pepy.tech/badge/m3u8dl)](https://pepy.tech/project/m3u8dl)

A CLI program to download a video played using a m3u8 playlist. Read about m3u8 here https://en.wikipedia.org/wiki/M3U#M3U8

## Dependencies
- Install python external modules using `pip install -r requirements.txt` after activating virtualenv.
- FFMPEG for video conversion, visit https://www.ffmpeg.org/download.html.
- Visit https://www.wikihow.com/Install-FFmpeg-on-Windows for FFMPEG setup on windows.
- Visit https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment for instructions on how to use virtualenv. 

## Usage

### Setup without Docker
- clone the repository using `git clone "ssh/https url"`.
- create a virtual environment using `virtualenv -p python3.6 venv` in linux terminal, see 'Dependencies' for platform specific instructions.
- activate virtual environment using `source venv/bin/activate` in linux terminal, see 'Dependencies' for platform specific instructions.
- install dependencies using `pip install -r requirements.txt`.
- insert the url request headers in headers.txt.
- start the script using `python -m m3u8dl <url of playlist>`.

### Setup with Docker
- build docker image using `docker build -t m3u8dl:0.5.0 .`
- start container `docker run -d -it --entrypoint='bash' --name m3u8dl-app m3u8dl:0.5.0` 
- go into container terminal `docker exec -it m3u8dl-app bash`

## Installing/Uninstalling
### Installation and usage using pip:-
- ensure ffmpeg is installed see dependecies section
- visit PyPI https://pypi.org/project/m3u8dl/0.5.0/ or install using below commands.
- run `pip install m3u8dl==0.5.0`
- run the program now using `python -m m3u8dl <url-of-playlist>`

### Uninstalling using pip:-
- run `pip uninstall m3u8dl`

### Installation in ubuntu using PyInstaller:-
- install pyinstaller using `pip install PyInstaller`
- activate virtualenv using `source venv/bin/activate`
- run `pyinstaller main.py --name m3u8-dl --onefile -p venv/lib/python3.6/site-packages/
` in terminal.
- run `sudo mv dist/m3u8-dl /usr/local/bin/` in terminal window.
- now that the program is installed globally you can start the program using `m3u8-dl` in the terminal

### Uninstalling in ubuntu:-
- run `sudo rm /usr/local/bin/m3u8-dl`

## CLI Options
    --help, -h:- display how to use the script
    --convert, -c:- specify this flag to convert the video to mp4 using ffmpeg`
    --name, -n:- specify the name by which to save the downloaded video, else 'video' is chosen as default name`
    --header-path, -p:- specify the path of header file`
    --retry, -r:- specify number of retries, by default 5 retries will be initiated
    --debug, -d:- print helpful messages to console to understand program flow
    --processes, -m:- specify custom number of processes, default is 4
    --threads, -t:- specify custom number of threads, default is 4 per process

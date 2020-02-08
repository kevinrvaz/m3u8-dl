# m3u8-playlist-downloader
a CLI program to download videos in a m3u8 playlist, write it to a single video file and convert it to mp4 using ffmpeg 

## Dependencies
- Requests module install using `pip install requests`<br>
- FFMPEG for video conversion visit https://www.ffmpeg.org/download.html<br>
- PyInstaller for building executable `pip install pyinstaller`<br>

## Usage without installation
- create a virtual environment using `virtualenv -p python3.6 venv` in linux<br/>
- activate virtual environment using `source venv/bin/activate` in linux<br/>
- insert the url request headers in headers.txt<br/>
- start the script using `python m3u8_playlist_downloader.py <url of playlist>`

## Installing/Uninstalling
for installation in ubuntu using PyInstaller:-
- active virtualenv using `source venv/bin/activate`
- run `pyinstaller m3u8_playlist_downloader.py --name m3u8-dl --onefile --hidden-import=requests`
- run `sudo mv dist/m3u8-dl /usr/local/bin` in terminal window

for uninstall in ubuntu:-
- run `sudo rm /usr/local/bin/m3u8-dl`

## CLI Options
- `--help, -h:- display how to use the script`<br>
- `--convert, -c:- specify this flag to convert the video to mp4 using ffmpeg`<br>
- `--name, -n:- specify the name by which to save the downloaded video, ele 'video' is chosen as default name`<br>
- `--header-path, -p:- specify the path of header file`<br>
- `--force, -f:- specify to re-download the video if it exists`<br>
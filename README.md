# m3u8-playlist-downloader
a CLI program to download videos in a m3u8 playlist, write it to a single video file and convert it to mp4 using ffmpeg 

## Dependencies
- Install python external modules using `pip install -r requirements.txt` after activating virtualenv<br>
- FFMPEG for video conversion, visit https://www.ffmpeg.org/download.html<br>

## Usage without installation
- create a virtual environment using `virtualenv -p python3.6 venv` in terminal<br/>
- activate virtual environment using `source venv/bin/activate` in terminal<br/>
- install dependencies
- insert the url request headers in headers.txt<br/>
- start the script using `python m3u8_playlist_downloader.py <url of playlist>`

## Installing/Uninstalling
for installation in ubuntu using PyInstaller:-
- activate virtualenv using `source venv/bin/activate`
- run `pyinstaller m3u8_playlist_downloader.py --name m3u8-dl --onefile --hidden-import=requests` in terminal.
- run `sudo mv dist/m3u8-dl /usr/local/bin` in terminal window.
- now that the program is installed globally you can start the program using `m3u8-dl` in the terminal

for uninstall in ubuntu:-
- run `sudo rm /usr/local/bin/m3u8-dl`

## CLI Options
    --help, -h:- display how to use the script
    --convert, -c:- specify this flag to convert the video to mp4 using ffmpeg`<br>
    --name, -n:- specify the name by which to save the downloaded video, ele 'video' is chosen as default name`<br>
    --header-path, -p:- specify the path of header file`<br>
    --force, -f:- specify to re-download the video if it exists`<br>
    --retry, -r:- specify number of retries, by default 5 retries will be initiated
import subprocess
import os


def concat_all_ts(video_file: str) -> None:
    """
    Parameters
    ----------
    video_file: str
        The file_name by which to save the concatenated .ts files
    """

    subprocess.Popen(["ffmpeg", "-f", "concat", "-safe", "0", "-i", "ts_list.txt",
                      "-c", "copy", f"{video_file}.ts"], stdout=subprocess.DEVNULL).wait()
    os.unlink("ts_list.txt")


def convert_video(video_input: str, video_output: str) -> None:
    """
    Parameters
    ----------
    video_input : str
        The input file name

    video_output : str
        The output file name
    """

    flags = ["ffmpeg", "-i", f"{video_input}.ts", "-acodec", "copy", "-vcodec", "copy", video_output]
    subprocess.Popen(flags, stdout=subprocess.DEVNULL).wait()
    os.unlink(f"{video_input}.ts")


def get_ts_start_time(file_path: str) -> float:
    """
    Parameters
    ----------
    file_path : str
        The file_path to the file to be probed

    Returns
    -------
    float
        The start time of the .ts file located at file_path
    """

    parse_png_to_mpeg2ts_stream(file_path)
    return float(os.path.split(file_path)[-1])


def parse_png_to_mpeg2ts_stream(file_path: str) -> None:
    """
    Parameters
    ----------
    file_path: str
        The file_path to be converted to mpeg2-ts, note this function assumes that the file will
        be detected as png due to starting bytes, and re parse it as mpeg2-ts
    """

    cmd = "ffmpeg -y -f mpegts -i {} -c copy {}.ts -v quiet".format(file_path, file_path)
    subprocess.Popen(cmd, shell=True).wait()
    os.unlink(file_path)
    os.rename(f"{file_path}.ts", file_path)


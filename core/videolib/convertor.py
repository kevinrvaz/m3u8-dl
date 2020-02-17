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

    cmd = "ffprobe {} -show_entries format=start_time -v quiet -of csv='p=0'" \
        .format(file_path)
    ts_time_stamp = subprocess.check_output(cmd, shell=True, close_fds=True)
    return float(ts_time_stamp)

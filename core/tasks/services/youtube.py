import os
import time
import uuid
import ffmpeg
from pytube import YouTube

from core.gui.main.components import convert_widget, console
from core.utility import files

# Cached temporary streams.
cached_temp_files = []


def get_YouTube_object(link):
    return YouTube(link)


# Called by the Convert Frame to finish a YouTube download request.
def download(youtube):
    # get the save location. May prompt the user.
    save_dir = files.get_save_location()
    if save_dir is None:
        # if failed to get a save location
        console.printError(
            '*SaveDir not specified. Either enable *Save=Auto, or select a save location when prompted.')
        return
    # Setup
    mode = convert_widget.output_mode.get()
    output_filename = files.clean_filename(convert_widget.get_output_filename(youtube.title))

    output_filepath = save_dir + "/" + output_filename
    # account for root dirs
    if save_dir[-1] == "/":
        output_filepath = save_dir + output_filename

    # download depending on output mode.
    if mode == 'Video':
        # get video and audio streams ready
        video_stream = youtube.streams.get_by_itag(convert_widget.video_stream_selector.get_selected_itag())
        audio_stream = youtube.streams.get_by_itag(convert_widget.audio_stream_selector.get_selected_itag())

        # temp download the streams
        src_vid = ffmpeg.input(temp_download_stream(save_dir, video_stream))
        src_aud = ffmpeg.input(temp_download_stream(save_dir, audio_stream))

        start_time = time.time()
        console.printInfo('Converting file and downloading as \"' + output_filename + "\".")

        # perform the concatenation
        operation = ffmpeg.concat(src_vid, src_aud, v=1, a=1)
        # get audio and video codecs
        operation = operation.output(output_filepath)
        try:
            operation.run(overwrite_output=True, quiet=True, cmd=files.resource_path("ffmpeg.exe"))
        except ffmpeg.Error as ex:
            # print error messages from FFMPEG before deleting temp files and throwing exception.
            print(ex.stdout.decode('utf8'))
            print(ex.stderr.decode('utf8'))
            cleanup_temp_files()
            raise ex

        # delete temp files leftover
        cleanup_temp_files()

        # print confirmation message
        console.printSuccess('Video file has been saved to \"' + output_filepath + "\". (" +
                             str(round(time.time() - start_time, 2)) + "s)")
        # add hyperlink to open the file
        console.addHyperlinkOpenFile('Show File in Explorer', output_filepath)

    elif mode == 'Audio':
        # download the audio stream, plug the temporary location into ffmpeg.
        audio_stream = youtube.streams.get_by_itag(convert_widget.audio_stream_selector.get_selected_itag())
        src_aud = ffmpeg.input(temp_download_stream(save_dir, audio_stream))

        start_time = time.time()
        console.printInfo('Converting file and downloading as \"' + output_filename + "\".")

        # perform the conversion and download
        operation = ffmpeg.output(src_aud, output_filepath)
        try:
            operation.run(overwrite_output=True, quiet=True, cmd=files.resource_path("ffmpeg.exe"))
        except ffmpeg.Error as ex:
            # print error messages from FFMPEG before deleting temp files and throwing exception.
            print(ex.stdout.decode('utf8'))
            print(ex.stderr.decode('utf8'))
            cleanup_temp_files()
            raise ex

        # delete temp files leftover
        cleanup_temp_files()

        # print confirmation message
        console.printSuccess('Audio file has been saved to \"' + output_filepath + "\". (" +
                             str(round(time.time() - start_time, 2)) + "s)")
        # add hyperlink to open the file
        console.addHyperlinkOpenFile('Show File in Explorer', output_filepath)

    elif mode == 'Mute Video':
        # download the video stream, plug the temporary location into ffmpeg.
        video_stream = youtube.streams.get_by_itag(convert_widget.video_stream_selector.get_selected_itag())
        src_vid = ffmpeg.input(temp_download_stream(save_dir, video_stream))

        start_time = time.time()
        console.printInfo('Converting file and downloading as \"' + output_filename + "\".")

        # perform the conversion and download
        operation = ffmpeg.output(src_vid, output_filepath)
        try:
            operation.run(overwrite_output=True, quiet=True, cmd=files.resource_path("ffmpeg.exe"))
        except ffmpeg.Error as ex:
            # print error messages from FFMPEG before deleting temp files and throwing exception.
            print(ex.stdout.decode('utf8'))
            print(ex.stderr.decode('utf8'))
            cleanup_temp_files()
            raise ex

        # delete temp files leftover
        cleanup_temp_files()

        # print confirmation message
        console.printSuccess('Mute video file has been saved to \"' + output_filepath +
                             "\". (" + str(round(time.time() - start_time, 2)) + "s)")
        # add hyperlink to open the file
        console.addHyperlinkOpenFile('Show File in Explorer', output_filepath)


# downloads a stream temporarily, returns the filepath.
# assumes save location is valid. don't forget to clean up temp files.
def temp_download_stream(loc, stream):
    # Download the file
    filepath = stream.download(output_path=loc, filename=str(uuid.uuid4()))
    # add to cache, and return
    cached_temp_files.append(filepath)
    return filepath


# removes all cached temp files from the system.
def cleanup_temp_files():
    global cached_temp_files
    for filepath in cached_temp_files:
        os.remove(filepath)
    cached_temp_files = []

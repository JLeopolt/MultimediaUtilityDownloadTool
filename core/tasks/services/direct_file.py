import os
import pathlib
import time
import urllib
import uuid
from urllib import request
import ffmpeg

from core.utility import files
from core.gui.main.components import convert_widget, console

cached_temp_files = []


# Called by the Convert Frame to finish a direct file download request.
def download(url_meta):
    # get the save location. May prompt the user.
    save_dir = files.get_save_location()
    if save_dir is None:
        # if failed to get a save location
        console.printError(
            '*SaveDir not specified. Either enable *Save=Auto, or select a save location when prompted.')
        return

    # Setup
    mode = convert_widget.output_mode.get()
    output_filename = files.clean_filename(convert_widget.get_output_filename(pathlib.Path(url_meta.filename).stem))
    output_filepath = get_filepath_from_save_dir(output_filename, save_dir)

    # Get the requested output filetype.
    output_filetype = pathlib.Path(output_filename).suffix
    input_file_type = pathlib.Path(url_meta.filename).suffix

    # If the output filetype is the same as the input filetype
    if output_filetype == input_file_type and mode == 'Video':
        # Download directly. No ffmpeg needed.
        local_fp, comp_time = download_source(url_meta, output_filepath)
        console.printSuccess('Downloaded file as \"' + local_fp + "\". (" + comp_time + "s)")
        return

    # temp download the source file
    local_path, c_time = download_source(url_meta,
                                         get_filepath_from_save_dir(str(uuid.uuid4()) + input_file_type, save_dir))
    cached_temp_files.append(local_path)
    console.printInfo('Retrieved source file. (' + c_time + "s)")

    # if conversion necessary
    # download depending on output mode.
    if mode == 'Video':
        start_time = time.time()
        console.printInfo('Converting file and downloading as \"' + output_filename + "\".")

        # perform the ffmpeg conversion and download.
        f_input = ffmpeg.input(local_path)
        operation = ffmpeg.output(f_input, output_filepath, vf="pad=ceil(iw/2)*2:ceil(ih/2)*2")
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
        start_time = time.time()
        console.printInfo('Converting file and downloading as \"' + output_filename + "\".")

        # perform the conversion and download
        f_input = ffmpeg.input(local_path)
        operation = ffmpeg.output(f_input, output_filepath, vf="pad=ceil(iw/2)*2:ceil(ih/2)*2")
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
        start_time = time.time()
        console.printInfo('Converting file and downloading as \"' + output_filename + "\".")

        # perform the conversion and download
        f_input = ffmpeg.input(local_path)
        operation = ffmpeg.output(f_input, output_filepath, vf="pad=ceil(iw/2)*2:ceil(ih/2)*2", an=None)
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


# Gets a filepath from a filename (with ext) and directory.
def get_filepath_from_save_dir(filename, save_dir):
    filepath = save_dir + "/" + filename
    # account for root dirs
    if save_dir[-1] == "/":
        filepath = save_dir + filename
    return filepath


# downloads the source file from a URL
# returns local filepath, time to complete.
def download_source(url_meta, save_location):
    start_time = time.time()
    return [urllib.request.urlretrieve(url_meta.url, save_location)[0], str(round(time.time() - start_time, 2))]


def cleanup_temp_files():
    global cached_temp_files
    for filepath in cached_temp_files:
        os.remove(filepath)
    cached_temp_files = []

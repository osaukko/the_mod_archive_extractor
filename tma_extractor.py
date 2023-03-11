import argparse
import datetime
import os
import sys
import uuid
import zipfile
from zipfile import ZipFile

dry_run = False
output_path = ''


def directory_reader(directory):
    """
    Browse through the files and folders in the directory. Zip files are passed to the zip_reader, and subfolders
    are executed recursively in the same function. Other files are ignored.

    :param directory:   Read this directory
    """
    print(f'[Reading DIR] {directory}')
    files = os.listdir(directory)
    files.sort()
    for file in files:
        absolute_file_path = os.path.join(directory, file)
        if os.path.isdir(absolute_file_path):
            directory_reader(absolute_file_path)
        elif os.path.isfile(absolute_file_path) and file.endswith('.zip'):
            zip_reader(open(absolute_file_path, 'rb'))
        else:
            print(f'[Ignoring FILE] {file}')


def zip_reader(zip_file_obj):
    """
    Reading ZIP content and sending files to file_handler.

    :param zip_file_obj:    file like object with zip content
    """
    try:
        zip_file = ZipFile(zip_file_obj)
        print(f'[Reading ZIP] {os.path.basename(zip_file.filename)}')
        for file_info in zip_file.infolist():
            print(f"[Extracting] {file_info.filename}")
            file_obj = zip_file.open(file_info)
            if file_info.filename.endswith(".zip"):
                zip_reader(file_obj)
            else:
                file_handler(file_obj.read(), file_info)
    except zipfile.BadZipfile as e:
        print(f'[ERROR] {e}')


def file_handler(content, file_info):
    """
    Using *file_info* to decide output path, then checks if the filename already exists.
    If filename already exists, then it is checked if the content is also duplicate.

    Files with unique names are written right away. File with duplicate names but different
    contents are written to subfolder with new name,

    :param content:     Uncompressed file content
    :param file_info:   ZipInfo object
    """
    # Some filenames work better if the CP437 encoding is changed to ISO-8859-1
    filename = file_info.filename.encode('cp437').decode('iso-8859-1')
    if filename != file_info.filename:
        print(f"[Encoding fix] {file_info.filename} -> {filename}")

    # Making output filename
    global output_path
    dir_a = filename[:1].upper()
    dir_b = filename[:2].upper()
    out_dir = os.path.normpath(f"{output_path}/{dir_a}/{dir_b}/")
    out_file = os.path.join(out_dir, filename)

    # Ensuring the output directory exists
    global dry_run
    if not dry_run:
        os.makedirs(out_dir, exist_ok=True)

    # 1st duplicate?
    if os.path.isfile(out_file):
        if is_same_file(content, out_file):
            print(f"[SKIPPING] Duplicate of {out_file}")
            return
        else:
            handle_first_duplicate(out_file)

    # Timestamp from the file info
    timestamp = datetime.datetime(*file_info.date_time).timestamp()

    # Use new name for duplicates and original name otherwise
    if os.path.isdir(out_file):
        is_duplicate, out_file = find_new_name(out_file, content)
        if is_duplicate is None:
            print(f"[SKIPPING] Duplicate of {out_file}")
            return

    write_file(content, out_file, timestamp)


def write_file(content, path, timestamp):
    """
    Read all bytes from the file_obj and save them to the *path* file

    :param content:     Bytes to write
    :param timestamp:   POSIX timestamp as float
    :param path:        Output to this file
    """
    global dry_run
    print(f'[Writing] {path} ({len(content)} bytes)')
    if not dry_run:
        file = open(path, 'wb')
        file.write(content)
        file.close()
        os.utime(path, (timestamp, timestamp))


def handle_first_duplicate(path):
    """
    This function renames the file in *path* to new using uuid_v4 for random name. Then directory is created using the
    *path* name. Finally, the file we renamed earlier is moved to the new path using the original name with "1-" as
    prefix.

    :param path:    Move this file to subdirectory of the same name using new name with the '1-' prefix
    """
    dirname = os.path.dirname(path)
    filename = os.path.basename(path)
    tempname = os.path.join(dirname, str(uuid.uuid4()))
    newpath = os.path.join(path, f'1-{filename}')
    print(f'[Moving] {path} -> {newpath}')
    global dry_run
    if not dry_run:
        os.rename(path, tempname)
        os.makedirs(path)
        os.rename(tempname, newpath)


def find_new_name(path, content):
    """
    Test if duplicates folder has file with the same content already.

    :param path:    Test files from this directory
    :param content: Compare against this content
    :return:        Tuple (is_duplicate, filename) where is_duplicate:
                        True => Filename for exact duplicate found
                        False => Content is unique, save using this filename

    """
    filename = os.path.basename(path)
    index = 1
    while True:
        newpath = os.path.join(path, f'{index}-{filename}')
        if not os.path.exists(newpath):
            return False, newpath
        if is_same_file(content, newpath):
            return True, newpath
        index += 1


def is_same_file(content, path):
    """
    Checking if the file length is the same, then comparing content.

    :param content: Compare against these bytes
    :param path:    Compare file from this path
    :return:        True if the file at *path* has the same *content*
    """
    if os.path.getsize(path) != len(content):
        return False

    file = open(path, "rb")
    block_size = 4096
    start_index = 0
    while start_index < len(content):
        block = file.read(block_size)
        if block != content[start_index:start_index+block_size]:
            return False
        start_index += block_size
    return True


def main():
    """
    Main function does the command line argument parsing and calls directory handler

    :return:    Exit code 0 on success, 1 on errors
    """
    global dry_run
    global output_path
    parser = argparse.ArgumentParser(
        prog='The Mod Archive Extractor',
        description='The program will extract the zip files downloaded as torrents from The Mod Archive to place them '
                    'in the appropriate subfolders. Duplicates will be placed in the folder with the original name '
                    'and renumbered there.')
    parser.add_argument('input_dir', help='Starting directory')
    parser.add_argument('output_dir', help='Where to output modules')
    parser.add_argument('-n', '--just-print', '--dry-run',
                        action='store_true', dest='dry_run',
                        help='Do everything but actual file operations. Instead, print what would happen.')
    args = parser.parse_args()
    dry_run = args.dry_run
    output_path = os.path.normpath(args.output_dir)

    directory_reader(os.path.normpath(args.input_dir))

    return 0


if __name__ == "__main__":
    sys.exit(main())

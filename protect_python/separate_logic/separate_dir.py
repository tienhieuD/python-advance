import os
import sys
import glob
import shutil
import re
from distutils.dir_util import copy_tree

sys.path.append(os.path.dirname(__file__))
import separate_file


def get_files_in_dir(path='C:/Users/hieudt/Desktop/jaddons'):
    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(path):
        for file in f:
            if file.endswith('.py'):
                files.append(os.path.join(r, file))
    return files


def separate_dir(fromDirectory, toDirectory, path_contain_regex, path_not_contain_regex):
    shutil.rmtree(toDirectory)
    copy_tree(fromDirectory, toDirectory)
    files = get_files_in_dir(toDirectory)
    for file_path in files:
        save_path = re.sub('(\w+?).py$', 'jprotect_\g<1>.py', file_path)
        main_path = file_path
        if any(re.match(pattern, file_path) for pattern in path_not_contain_regex):
            continue
        if all(re.match(pattern, file_path) for pattern in path_contain_regex):
            print(file_path)
            separate_file.separate_file(file_path, save_path, main_path)

if __name__ == '__main__':
    fromDirectory = 'C:/code/myaddon/tristar_project/073.Odoo_TriStar/trunk/3. SourceCode/addons'
    toDirectory = 'C:/Users/hieudt/Desktop/jaddons'

    separate_dir(
        fromDirectory,
        toDirectory,
        ['.+?models.+?', '.+?tristar.+?'],
        ['.+?__.py.+?'],
    )
    # shutil.rmtree(toDirectory)
    # copy_tree(fromDirectory, toDirectory)
    #
    # files = get_files_in_dir(toDirectory)
    #
    # for file_path in files:
    #     save_path = re.sub('(\w+?).py$', 'jprotect_\g<1>.py', file_path)
    #     main_path = file_path
    #     if 'models' in file_path and 'tristar' in file_path and '__.py' not in file_path:
    #         print(file_path)
    #         separate_file.separate_file(file_path, save_path, main_path)
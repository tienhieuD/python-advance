import os
import sys
import glob
import shutil

from distutils.dir_util import copy_tree
sys.path.append(os.path.dirname(__file__))

import separate_file

if __name__ == '__main__':
    fromDirectory = 'C:/code/myaddon/tristar_project/073.Odoo_TriStar/trunk/3. SourceCode/addons'
    toDirectory = 'C:/Users/hieudt/Desktop/jaddons'
    shutil.rmtree(toDirectory)
    copy_tree(fromDirectory, toDirectory)


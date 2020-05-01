#!python
#cython: language_level=3
import os
import re
import sys
from distutils.core import setup
from distutils.extension import Extension

from Cython.Distutils import build_ext

sys.path.append(os.path.dirname(__file__))
from separate_dir import separate_dir, get_files_in_dir

if __name__ == '__main__':  # RUN
    fromDirectory = 'C:/code/myaddon/tristar_project/073.Odoo_TriStar/trunk/3. SourceCode/addons'

    toDirectory = os.path.dirname(__file__) + '/dist'
    includes = ['.+?models.+?', '.+?tristar.+?']
    excludes = ['.+?__.py', '.+?tristar_payslip_sumary_canteen_foreign.py']
    separate_dir(fromDirectory, toDirectory, includes, excludes)
    files = get_files_in_dir(toDirectory)
    ext_modules = []
    to_remove_files = []
    for file_path in files:
        if 'jprotect_' in file_path:
            module_name = file_path.split(os.path.dirname(__file__))[-1].replace('\\', '.')[1:-3]
            ext_modules.append(Extension(module_name, [file_path]), )
            to_remove_files += [file_path]
    for extension in ext_modules:
        extension.cython_directives = {'language_level': "3"}
    setup(name='tristar', cmdclass={'build_ext': build_ext}, ext_modules=ext_modules)

    for remove_file_path in to_remove_files:
        if os.path.exists(remove_file_path):
            os.remove(remove_file_path)
            os.remove(remove_file_path[:-3] + '.c')

    complied_files = get_files_in_dir(toDirectory, ext=['.pyd', '.so'])
    for file_path in complied_files:
        new_name = re.sub('(.+?jprotect_\w+?)\.(.+?)\.(pyd|so)', '\g<1>.\g<3>', file_path)
        os.rename(file_path, new_name)

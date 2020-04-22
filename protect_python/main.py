# from module_cake import main      # this comes from a compiled binary
# main ()

# from ctypes import *

# import ctypes
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))
sys.path.append(os.path.dirname(__file__))
# adder = CDLL('./module_cake.cp37-win32.pyd')
# adder = ctypes.CDLL('./module_cake1.pyd')
# adder2 = ctypes.PyDLL('./module_cake1.pyd')

if __name__ == "__main__":
    import module_cake
    cake = module_cake.xxx(1,2)
    print(cake)

import py_compile
print(py_compile.compile('./hashxx.py', 'hashxxc.pyc'))
import subprocess

if __name__ == "__main__":
    rc, gopath = subprocess.getstatusoutput('python ./hashxxc.pyc 1000')
    print(rc)
    print(gopath)
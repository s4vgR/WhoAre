
# C:\python27\python setup.py bdist_msi

from cx_Freeze import setup, Executable
setup(
name = "AutoIs",
version = "1.0.0",
options = {"build_exe": {
'packages': ["cymru", "wx"],
'include_files': ['media/'],
'include_msvcr': True,
}},
executables = [Executable("gui.py", base="Win32GUI")]
)
import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
# Add any additional packages or modules that your project specifically needs
build_exe_options = {
    "packages": [
        "os", "sys", "threading", "zipfile", "json", "random", "tkinter", "requests", "tkinterdnd2", 
        "customtkinter", "time", "tkfilebrowser", "queue"
    ],
    "excludes": [],  # Exclude any packages not needed. You might need to adjust this.
    "include_files": []  # Include any non-Python files you use in your application
}

# GUI applications require a different base on Windows (the default is for a console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="Sketchfab Model Uploader",
    version="0.1",
    description="A utility to upload models to Sketchfab.",
    options={"build_exe": build_exe_options},
    executables=[Executable("sketchfab.py", base=base)]
)

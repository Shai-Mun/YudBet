import subprocess

# subprocess.run(args="cmd /c dir c:\windows")

# subprocess.run(args=["cmd /c dir c:\Program Files"], shell=True)

subprocess.run(args=["cmd /c", "dir", "c:\Program Files"], shell=True)
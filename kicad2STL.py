import os
import sys
import subprocess
import json

with open("preferences.json") as f:
    # self.prefs = json.load(f)
    fcadCmdPath = json.load(f)["freecadPath"]

# fcadCmdPath = r"C:\\Program Files\\FreeCAD 0.20\\bin\\FreeCADCmd.exe"
fcadExpScr = "fcad_pcb_export.FCMacro"
arg = sys.argv[1]
shell = [fcadCmdPath, fcadExpScr, arg]
print("Executing: ", " ".join(shell))
subprocess.call(shell)
# os.system('\"\" \"\"')
# os.system("dir")

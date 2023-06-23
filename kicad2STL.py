import os, sys, subprocess
fcadCmdPath = r"C:\\Program Files\\FreeCAD 0.20\\bin\\FreeCADCmd.exe"
fcadExpScr = "fcad_pcb_export.FCMacro"
arg = sys.argv[1] #"Testarg"
subprocess.call([fcadCmdPath, fcadExpScr, arg])
#os.system('\"\" \"\"')
#os.system("dir")
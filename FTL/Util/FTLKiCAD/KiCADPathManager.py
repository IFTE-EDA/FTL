import json
import os
from pathlib import Path
from string import Template


class KiCADPathManager:
    def __init__(self, kcuPath: str):
        if os.path.isfile(kcuPath):
            # a config file was specified
            self.confFile = kcuPath
        else:
            # preferred way - a kicad user dir was specified
            self.confFile = os.path.join(kcuPath, "kicad_common.json")
        with open(self.confFile) as file:
            self.json = json.load(file)
        self.paths = self.json["environment"]["vars"]

    @classmethod
    def searchForKiCADInstallation(cls):
        raise NotImplementedError("Not implemented yet. Sorry!")

    def getWorkingDir(self):
        return self.json["system"]["working_dir"]

    def getPath(self, pathName: str):
        if pathName in self.paths:
            return self.paths[pathName]
        else:
            raise IndexError(
                "Path not found in configuration file '{}': {}".format(
                    self.confFile, pathName
                )
            )

    def resolvePath(self, path: str):
        if path.startswith("$"):
            # return os.path(path[1:].format(**self.paths))
            return str(Path(path[1:].format(**self.paths)))
        else:
            return path

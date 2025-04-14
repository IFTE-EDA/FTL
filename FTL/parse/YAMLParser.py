import os
from pathlib import Path

import sys

sys.path.append(r"../..")
from FTL.parse.DXFParser import DXFParser
from FTL.core.GMSHGeometry import GMSHPhysicalGroup, GMSHGeom3D, GMSHGeom2D
import gmsh


class YAMLParser:
    """
    A class to parse_yaml YAML files for creating gometries from DXF files.
    """

    def __init__(self, file_path):
        """
        Initializes the YAMLParser with the path to the YAML file.

        :param file_path: Path to the YAML file.
        """
        self.file_path = file_path
        self.parse_yaml()

    def parse_yaml(self):
        """
        Parses the YAML file and returns its content as a dictionary.

        :return: Dictionary representation of the YAML file.
        """
        import yaml

        with open(self.file_path, "r") as file:
            data = yaml.safe_load(file)

        self.yaml_data = data
        if self.yaml_data["File"] is not None:
            self.dxf_file = data["File"]
            self.dxfparser = DXFParser(self.dxf_file)

        self.vars = {}
        self.vars["LAYER"] = {}
        for item in data["Layers"]:
            self.vars["LAYER"][item["Name"]] = {}

    def make_geometry(self, data=None):
        """
        Creates geometry objects based on the parsed YAML data.

        :param data: Dictionary representation of the YAML file.
        :return: List of geometry objects created from the YAML data.
        """
        self.zpos = (
            0
            if "Z" not in self.yaml_data["Settings"]
            else self.yaml_data["Settings"]["Z"]
        )
        if data is None:
            data = self.yaml_data
        for item in data["Layers"]:
            self.make_layer(item)
        GMSHPhysicalGroup.commit_all()

    def _get_var(self, var: str):
        """
        Solves the variables in the YAML file.

        :param var: Variable to be solved.
        :return: Value of the solved variable.
        """
        if not var.startswith("$"):
            return var
        if var.startswith("$LAYER"):
            var_exploded = var.split("/")
            layer_name = var_exploded[1]
            var_name = var_exploded[2]
            return self.vars["LAYER"][layer_name][var_name]

    def _set_var(self, var: str, value):
        """
        Sets the value of a variable in the YAML file.

        :param var: Variable to be set.
        :param value: Value to be assigned to the variable.
        """
        if var.startswith("$LAYER"):
            var_exploded = var.split("/")
            layer_name = var_exploded[1]
            var_name = var_exploded[2]
            self.vars["LAYER"][layer_name][var_name] = value

    def make_layer(self, layer):
        """
        Creates a layer object based on the parsed YAML data.

        :param layer: Dictionary representation of the layer in the YAML file.
        :return: Layer object created from the YAML data.
        """
        # TODO: Check for layer existence?
        dxf_layer = self.dxfparser.get_layer(layer["Layer"])
        geom = dxf_layer.render()
        layer_vars = self.vars["LAYER"][layer["Name"]]
        if "Extrude" in layer:
            print(self.vars)
            layer_vars = {
                "BOT": self._get_var(layer["Extrude"][0]),
                "TOP": self._get_var(layer["Extrude"][1]),
                "THICKNESS": float(self._get_var(layer["Extrude"][1]))
                - float(self._get_var(layer["Extrude"][0])),
            }
            pass
        elif "Thickness" in layer:
            layer_vars = {
                "BOT": self.zpos,
                "TOP": self.zpos + layer["Thickness"],
                "THICKNESS": layer["Thickness"],
            }
        else:
            raise ValueError(
                "Layer {} must have either Extrude or Thickness defined.".format(
                    layer["Name"]
                )
            )
        geom_3d = geom.extrude(
            float(layer_vars["THICKNESS"]),
            zpos=float(layer_vars["BOT"]),
        )
        if "Subtract" in layer:
            if not isinstance(layer["Subtract"], list):
                print(
                    "Subtracting layer {} from layer {}".format(
                        layer["Subtract"], layer["Name"]
                    )
                )
                geom.cutout(
                    self.dxfparser.get_layer(layer["Subtract"]).render()
                )
            else:
                print(
                    "Subtracting layers {} from layer {}".format(
                        layer["Subtract"], layer["Name"]
                    )
                )
                for sub in layer["Subtract"]:
                    geom.cutout(
                        self.dxfparser.get_layer(layer["Subtract"]).render()
                    )
        if "Add" in layer:
            if not isinstance(layer["Add"], list):
                print(
                    "Adding layer {} to layer {}".format(
                        layer["Add"], layer["Name"]
                    )
                )
                geom.add(self.dxfparser.get_layer(layer["Add"]).render())
            else:
                print(
                    "Adding layers {} to layer {}".format(
                        layer["Add"], layer["Name"]
                    )
                )
                for sub in layer["Add"]:
                    geom.add(self.dxfparser.get_layer(layer["Add"]).render())

        self.vars["LAYER"][layer["Name"]] = layer_vars
        # gmsh.model.occ.synchronize()
        # gmsh.fltk.run()
        # geom_3d = geom.extrude(layer["Thickness"], zpos=self.zpos)
        # TODO: Check if this is okay
        self.zpos += layer_vars["THICKNESS"]
        geom_3d.create_group_solid(layer["Name"])

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

    def make_layer(self, layer):
        """
        Creates a layer object based on the parsed YAML data.

        :param layer: Dictionary representation of the layer in the YAML file.
        :return: Layer object created from the YAML data.
        """
        # TODO: Check for layer existence?
        dxf_layer = self.dxfparser.get_layer(layer["Layer"])
        geom = dxf_layer.render()
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
        # gmsh.model.occ.synchronize()
        # gmsh.fltk.run()
        geom_3d = geom.extrude(layer["Thickness"], zpos=self.zpos)
        self.zpos += layer["Thickness"]
        geom_3d.create_group_solid(layer["Name"])

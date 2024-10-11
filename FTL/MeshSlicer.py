from __future__ import annotations
import logging
from typing import List
import vedo as v

from .Transformations import Transformation
from .MeshLayer import MeshLayer


class MeshSlicer:
    def __init__(
        self, layers: List[MeshLayer], transformations: List[MeshLayer]
    ):
        self.layers = layers
        self.transformations = transformations

    def get_subdivided_mesh(self, mel_solid, mel_trans, mel_residual):
        meshes = []
        for layer in self.layers:
            mesh = layer.mesh
            meshes.append(mesh)
        return v.merge(meshes)

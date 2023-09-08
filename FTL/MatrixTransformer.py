import vedo as v
import vtk
import numpy as np
from PyQt6 import QtCore
from PyQt6.QtCore import QObject, QThread, pyqtSignal

import FTL

MODE_GUI = False


def debug(str):
    if MODE_GUI:
        # main.console(str)
        print(str)
    else:
        print(str)


class MatrixTransformer(QtCore.QObject):
    def __init__(self, rcFP=None, rcRender=None):
        super().__init__()
        if rcFP is None:
            rcFP = FTL.RenderContainer()
        elif type(rcFP) is v.Plotter:
            rcFP = FTL.RenderContainer(rcFP)
        if rcRender is None:
            rcRender = FTL.RenderContainer()
        elif type(rcFP) is v.Plotter:
            rcRender = FTL.RenderContainer(rcRender)
        self.rcFP = rcFP
        self.rcRender = rcRender

        self.points = []
        self.layers = []
        self.nlayers = 0
        self.transformations = []
        self.mel = None
        self.debugOutput = []
        self.fixed_scope = None
        self.fixed_mesh = []

        self.fixedPts = []
        self.transformedPts = []

        self.xmin, self.xmax = (0, 0)
        self.ymin, self.ymax = (0, 0)
        self.zmin, self.zmax = (0, 0)

    progress = QtCore.pyqtSignal(int)
    status = QtCore.pyqtSignal(str)

    def update_progress(self, cur, max):
        self.progress.emit(int(cur / max * 100))

    def add_transformation(self, tr):
        # trId = len(self.transformations)
        self.transformations.append(tr)
        tr.parent = self
        if tr.addResidual:
            res = tr.getResidualTransformation()
            debug("    - adding Residual {}".format(res))
            self.add_transformation(res)

    def add_layer(self, layer):
        self.layers.append(layer)
        xmin, xmax = layer.mesh.xbounds()
        ymin, ymax = layer.mesh.ybounds()
        zmin, zmax = layer.mesh.zbounds()

        self.xmin = min(self.xmin, xmin)
        self.xmax = max(self.xmax, xmax)
        self.ymin = min(self.ymin, ymin)
        self.ymax = max(self.ymax, ymax)
        self.zmin = min(self.zmin, zmin)
        self.zmax = max(self.zmax, zmax)

        self.nlayers += 1

    def visualize(self):
        debug(
            "\n-------------------------\n-----  VISUALIZING  -----\n-------------------------"
        )
        self.status.emit("Visualizing...")
        self.progress.emit(0)
        # meshes = [layer.mesh for layer in self.layers]
        for layer in self.layers:
            self.rcFP.add_layer(layer.name, layer.mesh.clone().c("grey"))
        trId = 0
        if len(self.transformations) > 0:
            while trId < len(self.transformations):
                tr = self.transformations[trId]
                debug(tr)
                self.status.emit(
                    "Visualizing Transformation {}/{}".format(
                        trId, len(self.transformations)
                    )
                )
                self.update_progress(trId + 1, len(self.transformations))
                debug("{} meshes found".format(len(tr.meshes)))
                area = tr.getArea().extrude(3).z(-1.5).c("green").alpha(0.2)
                self.rcFP.add_transformation(
                    tr.name + "_outline", tr.getOutline().c("yellow7")
                )
                self.rcFP.add_transformation(
                    tr.name + "_area", area.clone(), False
                )
                self.rcRender.add_transformation(
                    tr.name + "_area", area.clone(), True
                )
                if len(tr.meshes) > 0:
                    self.rcRender.add_layer(
                        tr.name + "_slice",
                        v.merge(tr.meshes).alpha(1).c("blue"),
                        False,
                    )
                if tr.addResidual:
                    if len(self.transformations[trId + 1].meshes) > 0:
                        self.rcRender.add_layer(
                            tr.name + "-Res_slice",
                            v.merge(self.transformations[trId + 1].meshes)
                            .alpha(1)
                            .c("green"),
                            False,
                        )
                    trId += 2  # skip next transformation as we did it as a residual here
                else:
                    trId += 1  # next transformation
        else:
            print("No Transformations found to visualize.")
        if len(self.fixed_mesh) > 0:
            self.rcRender.add_layer(
                "Mesh_Fixed", v.merge(self.fixed_mesh).alpha(1).c("red"), True
            )

    def calculate_assignments(self, onlybaselayer=False):
        scope_residual = None
        for layerId, layer in enumerate(self.layers):
            if layerId == 0:
                debug(
                    "\nCalculating assignments. Layer #0 seen as substrate to generate transformation scopes..."
                )
                part = layer.mesh.clone()
                trId = 0
                while trId < len(self.transformations):
                    tr = self.transformations[trId]
                    debug("-> Transformation #{}: {}".format(trId, tr))
                    self.status.emit(
                        "Calculating Assignments... Layer {}/{}, Transformation {}/{}".format(
                            layerId + 1,
                            len(self.layers),
                            trId + 1,
                            len(self.transformations),
                        )
                    )
                    self.update_progress(
                        layerId * len(self.layers) + trId,
                        len(self.transformations),
                    )

                    outline = tr.getOutline()
                    mesh_transformed, part = cut_with_line(
                        part, outline, closed=True
                    )

                    v.write(mesh_transformed, "_mesh_transformed.stl")
                    v.write(part, "_part.stl")

                    # ol_gop = tr.getOutlinePts()
                    scope_transformed = get_contour_scope(mesh_transformed)
                    tr.scope = scope_transformed
                    tr.meshes.append(mesh_transformed.clone())
                    tr.mel.append(layer.mel_trans)
                    self.rcFP.add_transformation(
                        tr.name + "_mesh",
                        scope_transformed.clone().c("blue").alpha(0.2),
                        False,
                    )

                    fixedMeshes = []
                    residualMeshes = []
                    split = part.split()
                    p0, p1 = tr.getBorderlinePts()
                    self.rcFP.add_debug(
                        tr.name + "_borderline",
                        v.Line(tr.getBorderlinePts()).lw(2).c("red"),
                        False,
                    )
                    for prt in split:
                        if prt.intersect_with_line(p0, p1).any():
                            fixedMeshes.append(prt)
                        else:
                            residualMeshes.append(prt)
                    part = v.merge(fixedMeshes)

                    # TODO: if fixedmesh is Null, there might be a problem with geometries

                    if tr.addResidual and len(residualMeshes) > 0:
                        residual = v.merge(residualMeshes)
                        scope_residual = get_contour_scope(residual)
                        self.transformations[trId + 1].scope = scope_residual
                        self.transformations[trId + 1].meshes.append(residual)
                        self.transformations[trId + 1].mel.append(
                            layer.mel_residual
                        )

                    if tr.addResidual:
                        debug(
                            "    Skipping residual Transformation #{}: {}\n".format(
                                trId + 1, self.transformations[trId + 1]
                            )
                        )
                        trId += 2  # skip next transformation as we did it as a residual here
                    else:
                        trId += 1  # next transformation

                self.fixed_mesh.append(part)
                self.fixed_scope = get_contour_scope(part)

                # TODO accessing fixed_scope causes error
                debug("Base layer done.\n")
                continue
            if onlybaselayer:
                break
            debug(
                "Calculating {} assignments for layer #{}".format(
                    len(self.transformations), layerId
                )
            )

            mesh_fixed = layer.mesh.clone()
            trId = 0
            while trId < len(self.transformations):
                tr = self.transformations[trId]
                debug("-> Transformation #{}: {}".format(trId, tr))

                (
                    mesh_transformed,
                    mesh_fixed,
                    mesh_residual,
                ) = split_with_transformation(self, mesh_fixed, tr)

                self.debugOutput.append(
                    mesh_transformed.clone().z(20).c("blue")
                )

                debug("  -> Slice successful.")
                tr.meshes.append(mesh_transformed.clone())
                tr.mel.append(layer.mel_trans)
                self.debugOutput.append(
                    v.Line(tr.getBorderlinePts()).lw(2).c("red")
                )

                if (
                    tr.addResidual
                    and mesh_residual is not None
                    and mesh_residual.npoints > 0
                ):
                    debug("  -> Adding residual....")
                    self.transformations[trId + 1].meshes.append(mesh_residual)
                    self.transformations[trId + 1].mel.append(
                        layer.mel_residual
                    )
                    self.debugOutput.append(
                        scope_residual.clone().c("green").alpha(0.2)
                    )

                if tr.addResidual:
                    debug(
                        "    Skipping residual Transformation #{}: {}\n".format(
                            trId + 1, self.transformations[trId + 1]
                        )
                    )
                    trId += 2  # skip next transformation as we did it as a residual here
                else:
                    trId += 1  # next transformation

                self.debugOutput.append(mesh_transformed.clone().c("blue"))

                debug("    Transformation done.\n")
            if mesh_fixed is not None:
                self.fixed_mesh.append(mesh_fixed)
            else:
                self.fixed_mesh.append(None)

    def getPointId(self, pt, meshNum):
        # return self.mesh[meshNum].closest_point(pt, 1, return_point_id=True)
        return self.layers[meshNum].mesh.closest_point(
            pt, 1, return_point_id=True
        )

    def start_transformation(self):
        for tr in self.transformations:
            for meshNum in range(len(tr.meshes)):
                mesh = tr.get_preprocessed_mesh(meshNum).clean()
                # mats = []
                if (
                    tr.transformWholeMesh
                ):  # Transformation implemented a method to  the whole transformation on its own
                    mesh = tr.transformMesh(mesh)
                else:
                    points = mesh.points()
                    for pid, pt in enumerate(points):
                        self.update_progress(pid, len(points))
                        vec = np.array([pt[0], pt[1], pt[2], 1])
                        vec = np.dot(tr.getMatrixAt(pt), vec)
                        points[pid][0] = vec[0]
                        points[pid][1] = vec[1]
                        points[pid][2] = vec[2]
                    mesh.points(points)
                tr.meshes[meshNum] = mesh
                self.debugOutput.append(mesh)

    def get_result_mesh(self):
        for trId, tr in enumerate(self.transformations):
            for meshNum, mesh in enumerate(tr.meshes):
                print(
                    "--------> Got {}_{}-tr'ed".format(
                        self.layers[meshNum].name, tr.name
                    )
                )
                self.rcRender.add_layer(
                    "{}_{}-tr'ed".format(self.layers[meshNum].name, tr.name),
                    mesh.alpha(1).c(self.layers[meshNum].color),
                    True,
                )

        meshes = [v.merge(tr.meshes) for tr in self.transformations]
        meshes = [e for e in meshes if e is not None]
        meshes.append(v.merge(self.fixed_mesh))
        ret = v.merge(meshes)
        return ret

    def getTransformedMeshList(self):
        meshes = {e.name: None for e in self.layers}
        print(meshes)
        for meshNum in range(self.nlayers):
            layer = [tr.meshes[meshNum] for tr in self.transformations]
            layer.append(self.fixed_mesh[meshNum])
            print(
                "{} meshes in '{}'".format(
                    len(layer), self.layers[meshNum].name
                )
            )
            meshes[self.layers[meshNum].name] = v.merge(layer)
        print(meshes)
        return meshes


def cut_with_line(mesh, points, invert=False, closed=True, residual=True):
    mesh = mesh.clone()
    pplane = vtk.vtkPolyPlane()
    if isinstance(points, v.Points):
        points = points.points().tolist()

    if closed:
        if isinstance(points, np.ndarray):
            points = points.tolist()
        points.append(points[0])

    vpoints = vtk.vtkPoints()
    for p in points:
        if len(p) == 2:
            p = [p[0], p[1], 0.0]
        vpoints.InsertNextPoint(p)

    n = len(points)
    polyline = vtk.vtkPolyLine()
    polyline.Initialize(n, vpoints)
    polyline.GetPointIds().SetNumberOfIds(n)
    for i in range(n):
        polyline.GetPointIds().SetId(i, i)
    pplane.SetPolyLine(polyline)

    currentscals = mesh.polydata().GetPointData().GetScalars()
    if currentscals:
        currentscals = currentscals.GetName()

    clipper = vtk.vtkClipPolyData()
    clipper.SetInputData(mesh.polydata(True))  # must be True
    clipper.SetClipFunction(pplane)
    clipper.SetInsideOut(invert)
    clipper.GenerateClippedOutputOn()
    clipper.GenerateClipScalarsOff()
    clipper.SetValue(0)
    clipper.Update()
    cpoly = clipper.GetOutput(0)
    kpoly = clipper.GetOutput(1)

    vis = False
    if currentscals:
        cpoly.GetPointData().SetActiveScalars(currentscals)
        vis = mesh.mapper().GetScalarVisibility()

    if mesh.GetIsIdentity() or cpoly.GetNumberOfPoints() == 0:
        mesh._update(cpoly)
    else:
        # bring the underlying polydata to where _data is
        M = vtk.vtkMatrix4x4()
        M.DeepCopy(mesh.GetMatrix())
        M.Invert()
        tr = vtk.vtkTransform()
        tr.SetMatrix(M)
        tf = vtk.vtkTransformPolyDataFilter()
        tf.SetTransform(tr)
        tf.SetInputData(cpoly)
        tf.Update()
        mesh._update(tf.GetOutput())

    mesh.pointdata.remove("SignedDistances")
    mesh.mapper().SetScalarVisibility(vis)
    cutoff = v.Mesh(kpoly)
    cutoff.property = vtk.vtkProperty()
    cutoff.property.DeepCopy(mesh.property)
    cutoff.property.DeepCopy(mesh.property)
    cutoff.SetProperty(cutoff.property)

    return mesh, cutoff


def split_with_transformation(self, mesh, tr):
    mesh_transformed, part = cut_with_line(mesh.clone(), tr.getOutline())
    # mesh_transformed = mesh_transformed.clean()
    fixedMeshes = []
    residualMeshes = []
    split = part.split()
    debug("  -> Splitting {} parts...".format(len(split)))
    for prt in split:
        inter = len(self.fixed_scope.inside_points(prt.points()).points())
        # debug("    Intersecting points: {}".format(inter))                  # TODO: Check for bounding box intersections
        if inter:
            fixedMeshes.append(prt)
        else:
            residualMeshes.append(prt)
    mesh_fixed = v.merge(fixedMeshes)
    mesh_residual = v.merge(residualMeshes)

    return mesh_transformed, mesh_fixed, mesh_residual


def get_contour_scope(mesh):
    newMesh = mesh.clone()
    newMesh.clean()
    contour = newMesh.project_on_plane("z")
    extrude = contour.clean().extrude(4, cap=True).z(-2)
    return extrude

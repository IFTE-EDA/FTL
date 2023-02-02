import vedo as v
from Transformation import *
import vtk

class MatrixTransformer:
    def __init__(self, plt=None):
        self.plotter = plt
        self.points = []
        #self.mesh = []
        self.layers = []
        #for i, mesh in enumerate(meshes):
        #    self.mesh.append(mesh)
        #    self.points.append(mesh.points())
        self.nlayers = 0
        self.transformations = []
        self.mel = None
        self.debugOutput = []
        self.fixed_scope = None
        self.fixed_mesh = []

        #self.bounds = mesh.bounds()

        self.fixedPts = []
        self.transformedPts = []

        self.xmin, self.xmax = (0, 0)
        self.ymin, self.ymax = (0, 0)
        self.zmin, self.zmax = (0, 0)

    def add_transformation(self, tr):
        trId = len(self.transformations)
        self.transformations.append(tr)
        #self.transformedPts.append([])
        tr.parent = self
        if (tr.addResidual):
            res = tr.getResidualTransformation()
            print ("    - adding Residual {}".format(res))
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

    def visualize(self, plt):
        print("\n-------------------------\n-----  VISUALIZING  -----\n-------------------------")
        meshes = [l.mesh for l in self.layers]
        #meshes = []
        #for layer in self.layers:
        #    meshes.append(layer.mesh)
        #plt.show(merge(self.layers[:].mesh).alpha(1).c("grey").z(-20))
        plt.show(merge(meshes).alpha(1).c("grey").z(-20))
        trId = 0
        while trId < len(self.transformations):
            tr = self.transformations[trId]
            print(tr)
            print("{} meshes found".format(len(tr.meshes)))
            area = v.Rectangle((tr.xmin, tr.ymin), (tr.xmax, tr.ymax)).extrude(3).z(-1.5).c("green").alpha(0.2)
            self.debugOutput.extend([area, tr.getOutline().c("yellow7")])
            #borderScope = tr.getBorderScope(4)
            plt.show(area, tr.getOutline().c("yellow7"))
            if len(tr.meshes) > 0:
                plt.show(v.merge(tr.meshes).alpha(1).c("blue"))
            if tr.addResidual:
                if len(self.transformations[trId+1].meshes) > 0:
                    plt.show(v.merge(self.transformations[trId+1].meshes).alpha(1).c("green"))
                #print("    Skipping residual Transformation #{}: {}\n    -> added {} residual points.".format(trId+1, self.transformations[trId + 1], len(self.transformations[trId + 1].points)))
                trId += 2       #skip next transformation as we did it as a residual here
            else:
                trId += 1       #next transformation
        if len(self.fixed_mesh) > 0:
            plt.show(v.merge(self.fixed_mesh).alpha(1).c("red"))

    def calculate_assignments(self, onlybaselayer=False):
        for layerId, layer in enumerate(self.layers):

            if layerId == 0:
                print ("\nCalculating assignments. Layer #0 seen as substrate to generate transformation scopes...")
                part = layer.mesh.clone()
                trId = 0
                while trId < len(self.transformations):
                    tr = self.transformations[trId]
                    print("-> Transformation #{}: {}".format(trId, tr))

                    outline = tr.getOutline()
                    mesh_transformed, part = cut_with_line(part, outline, closed=True)
                    #print(outline)
                    #self.plotter.show(outline.c("red").lw(4), mesh_transformed.clone().c("blue").z(layerId*100+trId*20), part.clone().c("orange").z(layerId*100+trId*20))
                    self.plotter.render()
                    write(mesh_transformed, "_mesh_transformed.stl")
                    write(part, "_part.stl")
                    olpts = outline.points()
                    oleds = outline.edges()
                    olpts = list(olpts)
                    #olpts.append(olpts[0])
                    #outline.points(olpts)
                    #outline.edges(oleds)
                    ol_gop = tr.getOutlinePts()
                    scope_transformed = get_contour_scope(mesh_transformed)
                    tr.scope = scope_transformed
                    tr.meshes.append(mesh_transformed.clone())
                    tr.mel.append(layer.mel_trans)
                    self.debugOutput.append(scope_transformed.clone().c("blue").alpha(0.2))

                    fixedMeshes = []
                    residualMeshes = []
                    split = part.split()
                    p0, p1 = tr.getBorderlinePts()
                    self.debugOutput.append(Line(tr.getBorderlinePts()).lw(2).c("red"))
                    for prt in split:
                        #border = tr.getBorderlinePts()
                        if prt.intersect_with_line(p0, p1).any():
                            fixedMeshes.append(prt)
                        else:
                            residualMeshes.append(prt)
                    part = v.merge(fixedMeshes)

                    if tr.addResidual and len(residualMeshes) > 0:
                        residual = v.merge(residualMeshes)
                        scope_residual = get_contour_scope(residual)
                        self.transformations[trId + 1].scope = scope_residual
                        self.transformations[trId + 1].meshes.append(residual)
                        self.transformations[trId + 1].mel.append(layer.mel_residual)

                    # print("    Transformation done. Points fixed: {}; discovered: {}; transformed: {}; residual: {}".format(len(fixedPts), len(discoveredPoints), len(transformedPts), len(residualPts)))

                    if tr.addResidual:
                        # print("    Skipping residual Transformation #{}: {}\n    -> added {} residual points.".format(trId+1, self.transformations[trId + 1], len(self.transformations[trId + 1].points)))
                        print("    Skipping residual Transformation #{}: {}\n".format(trId + 1,
                                                                                      self.transformations[trId + 1]))
                        trId += 2  # skip next transformation as we did it as a residual here
                    else:
                        trId += 1  # next transformation

                self.fixed_mesh.append(part)
                #self.mel.append(layer.mel)
                self.fixed_scope = get_contour_scope(part)
                self.debugOutput.append(self.fixed_scope.clone().c("red").alpha(0.2))
                print ("Base layer done.\n")
                continue
            if onlybaselayer:
                break
            print("Calculating {} assignments for layer #{}".format(len(self.transformations), layerId))

            mesh_fixed = layer.mesh.clone()
            trId = 0
            while trId < len(self.transformations):
                tr = self.transformations[trId]
                print("-> Transformation #{}: {}".format(trId, tr))


                #mesh_fixed, mesh_transformed, mesh_residual = cut_with_line(mesh_fixed, tr.getOutlinePts(), closed=True)
                mesh_transformed, mesh_fixed, mesh_residual = split_with_transformation(self, mesh_fixed, tr)

                self.debugOutput.append(mesh_transformed.clone().z(20).c("blue"))
                #if mesh_residual is not None:
                    #self.debugOutput.append(mesh_residual.clone().z(20).c("green"))
                #self.debugOutput.extend([mesh_transformed.z(20).c("blue"), mesh_fixed.z(20).c("red"), mesh_residual.z(20).c("green")])


                #mesh_transformed, mesh_fixed, mesh_residual = split_with_transformation(self, mesh_fixed, tr)
                print("  -> Slice successful.")
                tr.meshes.append(mesh_transformed.clone())
                tr.mel.append(layer.mel_trans)
                p0, p1 = tr.getBorderlinePts()
                self.debugOutput.append(Line(tr.getBorderlinePts()).lw(2).c("red"))

                if tr.addResidual and mesh_residual is not None and mesh_residual.npoints > 0:
                    print("  -> Adding residual....")
                    self.transformations[trId + 1].meshes.append(mesh_residual)
                    self.transformations[trId + 1].mel.append(layer.mel_residual)
                    #self.debugOutput.append(scope_residual.clone().c("green").alpha(0.2))

                if tr.addResidual:
                    # print("    Skipping residual Transformation #{}: {}\n    -> added {} residual points.".format(trId+1, self.transformations[trId + 1], len(self.transformations[trId + 1].points)))
                    print("    Skipping residual Transformation #{}: {}\n".format(trId + 1,
                                                                                  self.transformations[trId + 1]))
                    trId += 2  # skip next transformation as we did it as a residual here
                else:
                    trId += 1  # next transformation

                self.debugOutput.append(mesh_transformed.clone().c("blue"))

                print("    Transformation done.\n")
            if mesh_fixed is not None:
                # self.debugOutput.append(mesh_fixed.clone().z(20).c("red"))
                self.fixed_mesh.append(mesh_fixed)
            else:
                self.fixed_mesh.append(None)
            #if mesh_fixed is not None:
            #    self.debugOutput.append(mesh_fixed.clone())

            #print("---------------------------------------------\n Points fixed: {}; transformed: {}; residual: {}".format(fixedPtCloud.npoints, transformedPtCloud.npoints, residualPtCloud.npoints))
            #print("Total Points: {}\n\n".format(fixedPtCloud.npoints + transformedPtCloud.npoints + residualPtCloud.npoints))



    def getPointId(self, pt, meshNum):
        #return self.mesh[meshNum].closest_point(pt, 1, return_point_id=True)
        return self.layers[meshNum].mesh.closest_point(pt, 1, return_point_id=True)

    def start_transformation(self):
        for tr in self.transformations:
            for meshNum in range(len(tr.meshes)):
                mesh = tr.get_preprocessed_mesh(meshNum)
                layer = self.layers[meshNum]
                points = mesh.points()
                for pid, pt in enumerate(points):
                    vec = np.array([pt[0], pt[1], pt[2], 1])
                    vec = np.dot(tr.getMatrixAt(pt), vec)
                    #pt[0] = vec[0]
                    #pt[1] = vec[1]
                    #pt[2] = vec[2]
                    points[pid][0] = vec[0]
                    points[pid][1] = vec[1]
                    points[pid][2] = vec[2]
                mesh.points(points)
                tr.meshes[meshNum] = mesh
                self.debugOutput.append(mesh)
        #return self.points

    def get_result_mesh(self):
        meshes = [v.merge(tr.meshes) for tr in self.transformations]
        meshes = [e for e in meshes if e is not None]
        meshes.append(v.merge(self.fixed_mesh))
        ret = v.merge(meshes)
        return ret

def cut_with_line(mesh, points, invert=False, closed=True, residual=True):
    mesh = mesh.clone()
    pplane = vtk.vtkPolyPlane()
    if isinstance(points, Points):
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
    cutoff = Mesh(kpoly)
    cutoff.property = vtk.vtkProperty()
    cutoff.property.DeepCopy(mesh.property)
    cutoff.property.DeepCopy(mesh.property)
    cutoff.SetProperty(cutoff.property)

    #ret = [mesh]
    #ret.append(split[0])#extend(cutoff.split())
    #ret.append(split[1])
    return mesh, cutoff



def split_with_transformation(self, mesh, tr):
    mesh_transformed, part = cut_with_line(mesh.clone(), tr.getOutline())
    fixedMeshes = []
    residualMeshes = []
    split = part.split()
    print("  -> Splitting {} parts...".format(len(split)))
    for prt in split:
        # border = tr.getBorderlinePts()
        inter = len(self.fixed_scope.inside_points(prt.points()).points())
        #print("    Intersecting points: {}".format(inter))                  # TODO: Check for bounding box intersections
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
    contour = newMesh.project_on_plane('z')
    extrude = contour.clean().extrude(4, cap=True).z(-2)
    return extrude

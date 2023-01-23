from typing import Union
import shapely
import shapely.geometry
#from shapely import box
import vtk
from numpy import ndarray
from vedo import *
"""
#sys.setrecursionlimit(2000)

"""
plt = Plotter(interactive=False, axes=7)

def getPointId(pt, m):
    #return pcb.closest_point(pt, 1, tol=0.001, return_point_id=True)
    return m.closest_point(pt, 1, return_point_id=True)



def split_with_line(mesh, points, invert=False, closed=True):
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
    cpoly = clipper.GetOutput()
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
    cutoff.SetProperty(cutoff.property)
    cutoff.c("k5").alpha(0.2)

    #ret = [mesh]
    split = cutoff.split()
    #ret.append(split[0])#extend(cutoff.split())
    #ret.append(split[1])
    return split[0], mesh, split[1]
    #return Assembly([mesh, cutoff])



delta = 4
pts = [ (25, -150),
        (95, -150),
        (95, -120),
        (25, -120)]
line = Line(pts, closed=True).c("red")

#pcb = load("LTest_hook.stl").subdivide(0, 2, mel=2).clean().alpha(0.5).color("grey")
meshes = []
meshes.append(load("LTest_hook_board.stl").subdivide(0, 2, mel=2).clean())
meshes.append(load("LTest_hook_trace.stl").subdivide(0, 2, mel=2).clean())
print("Subdivided.")

#pcb = merge(load("LTest_hook.stl").clean().alpha(0.5).color("grey"))
meshPoints = [mesh.points() for mesh in meshes]


(mFixed, mTrans, mRes) = tuple(split_with_line(meshes[0], pts, closed=True))
area = Cube(side=1).scale([70,30,10]).z(-2).x(60).y(-140+5).alpha(0.1).lw(0.1)

plt.show(mFixed.c("red"), mTrans.c("green"), mRes.c("blue"), meshes[1], area, line)
plt.render()
plt.interactive().close()
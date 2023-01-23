from vedo import *
from Transformation import *

class MatrixTransformer:
    def __init__(self, meshes, mel):
        self.points = []
        self.mesh = []
        #self.points[0] = []
        #self.points[1] = []
        for i, mesh in enumerate(meshes):
            self.mesh.append(mesh)
            self.points.append(mesh.points())
            #self.points[i] = mesh.points()
            #self.mesh[i] = mesh
        self.numMeshes = len(meshes)
        self.transformations = []
        self.mel = mel
        self.debugOutput = []

        #self.bounds = mesh.bounds()
        self.xmin, self.xmax = mesh.xbounds()
        self.ymin, self.ymax = mesh.ybounds()
        self.zmin, self.zmax = mesh.zbounds()

        self.fixedPts = []
        self.transformedPts = []

        meshNumStr = "/".join([str(mesh.npoints) for mesh in self.mesh])

        print("Transformer created. Imported {} meshes with {} points.".format(self.numMeshes, meshNumStr))

    def add_transformation(self, tr):
        trId = len(self.transformations)
        self.transformations.append(tr)
        #self.transformedPts.append([])
        tr.parent = self
        if (tr.addResidual):
            res = tr.getResidualTransformation()
            print ("    - ading Residual {}".format(res))
            self.add_transformation(res)

    def visualize(self, plt):
        trId = 0
        while trId < len(self.transformations):
            tr = self.transformations[trId]
            borderScope = tr.getBorderScope(4)
            area = Rectangle((tr.xmin, tr.ymin), (tr.xmax, tr.ymax)).extrude(4).z(-2).c("green").alpha(0.2)
            # area = Rectangle((tr.xmin, tr.ymin), (tr.xmax, tr.ymax)).extrude(4).z(-2).c("red").alpha(0.2)
            box = Rectangle((borderScope[0], borderScope[1]), (borderScope[2], borderScope[3])).extrude(4).z(-2).alpha(0.2).lw(0.1).c("red")
            plt.show(area, box, self.mesh)
            if tr.addResidual:
                #print("    Skipping residual Transformation #{}: {}\n    -> added {} residual points.".format(trId+1, self.transformations[trId + 1], len(self.transformations[trId + 1].points)))
                trId += 2       #skip next transformation as we did it as a residual here
            else:
                trId += 1       #next transformation

    def calculate_assignments(self):
        for meshNum, mesh in enumerate(self.mesh):
            print("Calculating {} assignments for mesh #{}".format(len(self.transformations), meshNum))
            visitedPts = [False] * mesh.npoints #len(self.points[meshNum])
            fixedPts = []

            rect = []
            #for trId, tr in enumerate(self.transformations):
            trId = 0
            while trId < len(self.transformations):
                tr = self.transformations[trId]
                print("-> Transformation #{}: {}".format(trId, tr))
                transformedPts = []
                residualPts = []
                borderEdges = []
                points_in_border = []
                lines = []

                #rect = Rectangle(tr.xmin, tr.ymin, tr.xmax, tr.ymax)
                borderScope = tr.getBorderScope(4)
                #area = tr.getOutline().extrude(4).z(-2).c("green").alpha(0.2)
                area = Rectangle((tr.xmin, tr.ymin), (tr.xmax, tr.ymax)).extrude(4).z(-2).c("green").alpha(0.2)
                #area = Rectangle((tr.xmin, tr.ymin), (tr.xmax, tr.ymax)).extrude(4).z(-2).c("red").alpha(0.2)
                box = Rectangle((borderScope[0], borderScope[1]), (borderScope[2], borderScope[3])).extrude(4).z(-2).alpha(0.2).lw(0.1).c("red")
                scope = mesh.clone().cut_with_mesh(box).c("red")
                scopeEdges = scope.edges()
                scopePoints = scope.points()
                print("    Found {} points and {} edges in scope".format(len(scopePoints), len(scopeEdges)))

                for e, edge in enumerate(scopeEdges):
                    # pid1, pid2 = edge
                    pid1 = self.getPointId(scopePoints[edge[0]], meshNum)
                    pid2 = self.getPointId(scopePoints[edge[1]], meshNum)
                    p1 = self.points[meshNum][pid1]
                    p2 = self.points[meshNum][pid2]
                    #borderEdges.append(Line(p1, p2).lw(3).c("red").alpha(0.2))
                    if area.is_inside(p1) and not area.is_inside(p2):
                        borderEdges.append(Line(p1, p2).lw(2).c("green"))
                        points_in_border.append(p1)
                        fixedPts.append(pid2)
                        visitedPts[pid2] = True
                    elif area.is_inside(p2) and not area.is_inside(p1):
                        borderEdges.append(Line(p1, p2).lw(2).c("red"))
                        points_in_border.append(p2)
                        # borderIDs.append(pid2)
                        # borderVerts.append(p2)
                        fixedPts.append(pid1)
                        visitedPts[pid1] = True

                print("    Found {} points and {} edges on border.\n    Starting presort...".format(len(points_in_border), len(borderEdges)))
                self.debugOutput.append(borderEdges)
                self.borderEdges = borderEdges
                self.debugOutput.append(Points(points_in_border, r=3).c("black"))
                discoveredPoints = []
                borderIDs = []

                for pt in points_in_border:
                    pid = self.getPointId(pt, meshNum)
                    if visitedPts[pid]:
                        continue
                    borderIDs.append(pid)
                    visitedPts[pid] = True
                    if area.is_inside(pt):
                        transformedPts.append(pid)
                        # visitedPts[pid] = True
                        for cv in mesh.connected_vertices(pid):
                            if not visitedPts[cv]:
                                borderIDs.append(cv)
                                # visitedPts[cv] = True
                                if not area.is_inside(self.points[meshNum][cv]):  # outside area -> fixed point at border
                                    visitedPts[cv] = True
                                    fixedPts.append(cv)
                                else:  # inside point
                                    discoveredPoints.append(cv)
                                    # transformedPts.append(cv)
                    else:
                        visitedPts[pid] = True
                        # discoveredPoints.append(pid)

                print("    Border-presort done. Points fixed: {}; discovered: {}".format(len(fixedPts), len(discoveredPoints)))

                i = 0
                while i < len(discoveredPoints):
                    curId = discoveredPoints[i]
                    if visitedPts[curId]:
                        i += 1
                        continue
                    visitedPts[curId] = True
                    curPt = self.points[meshNum][curId]

                    if not area.is_inside(curPt):
                        residualPts.append(curId)
                    else:
                        transformedPts.append(curId)
                    for cv in mesh.connected_vertices(curId):
                        if not visitedPts[cv]:
                            discoveredPoints.append(cv)
                    i += 1

                #tr.points[meshNum] = transformedPts
                tr.points.append(transformedPts)

                if tr.addResidual:
                    self.transformations[trId+1].points.append(residualPts)
                    # self.mesh.delete_cells_by_point_index(residualPts)

                print("    Transformation done. Points fixed: {}; discovered: {}; transformed: {}; residual: {}".format(len(fixedPts), len(discoveredPoints), len(transformedPts), len(residualPts)))

                #VISUALIZE
                transformedVerts = []
                residualVerts = []

                for pid in transformedPts:
                    transformedVerts.append(self.points[meshNum][pid])
                for pid in residualPts:
                    residualVerts.append(self.points[meshNum][pid])
                transformedPtCloud = Points(transformedVerts, r=5).c("yellow7")
                residualPtCloud = Points(residualVerts, r=5).c("green").alpha(0.02)

                self.debugOutput.extend([transformedPtCloud, residualPtCloud, box, area, tr.getOutline().c("yellow7")])
                #trId += (2 if tr.addResidual else 1)
                if tr.addResidual:
                    print("    Skipping residual Transformation #{}: {}\n    -> added {} residual points.".format(trId+1, self.transformations[trId + 1], len(self.transformations[trId + 1].points)))
                    trId += 2       #skip next transformation as we did it as a residual here
                else:
                    trId += 1       #next transformation
                print("    Transformation done.\n")

            fixedVerts = []
            for pid in fixedPts:
                fixedVerts.append(self.points[meshNum][pid])
            fixedPtCloud = Points(fixedVerts, r=5).c("red")
            self.debugOutput.append(fixedPtCloud)
            print("---------------------------------------------\n Points fixed: {}; transformed: {}; residual: {}".format(fixedPtCloud.npoints, transformedPtCloud.npoints, residualPtCloud.npoints))
            print("Total Points: {}\n\n".format(fixedPtCloud.npoints + transformedPtCloud.npoints + residualPtCloud.npoints))



    def getPointId(self, pt, meshNum):
        # return pcb.closest_point(pt, 1, tol=0.001, return_point_id=True)
        return self.mesh[meshNum].closest_point(pt, 1, return_point_id=True)

    def start_transformation(self):
        """self.colors = [[0, 0, 255, 100]] * len(self.points)
        for i, pt in enumerate(self.points):
            #self.points.point_colors[pt] = [255, 0, 0, 200]  # RGBA
            for tr in self.transformations:
                if (tr.isInScope(pt)):
                    if (tr.color is not None):
                        self.colors[i] = tr.color
                    vec = np.array([pt[0], pt[1], pt[2], 1])
                    #mat = tr.getMatrixAt(pt)
                    #pt = tr.getMatrixAt(pt) * pt
                    vec = np.dot(tr.getMatrixAt(pt), vec)
                    #vec[0] = mat[0][0] * pt[0] + mat[0][1] * pt[1] + mat[0][2] * pt[2] + mat[0][3]
                    #vec[1] = mat[1][0] * pt[0] + mat[1][1] * pt[1] + mat[1][2] * pt[2] + mat[1][3]
                    #vec[2] = mat[2][0] * pt[0] + mat[2][1] * pt[1] + mat[2][2] * pt[2] + mat[2][3]
                    pt[0] = vec[0]
                    pt[1] = vec[1]
                    pt[2] = vec[2]
        return self.points
        """
        for meshNum, mesh in enumerate(self.mesh):
            for tr in self.transformations:
                for pid in tr.points[meshNum]:
                    pt = self.points[meshNum][pid]
                    vec = np.array([pt[0], pt[1], pt[2], 1])
                    vec = np.dot(tr.getMatrixAt(pt), vec)
                    #pt[0] = vec[0]
                    #pt[1] = vec[1]
                    #pt[2] = vec[2]
                    self.points[meshNum][pid][0] = vec[0]
                    self.points[meshNum][pid][1] = vec[1]
                    self.points[meshNum][pid][2] = vec[2]
        return self.points
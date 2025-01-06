import numpy as np


class PolygonNester:
    def __init__(self, polygons=None):
        self.polygons = (
            polygons if polygons is not None else []
        )  # np.empty(0, dtype=Polygon)

    def add_polygon(self, polygon):
        exit_loop = False
        for poly in self.polygons:
            print(f"Checking {polygon}")
            if not poly.overlaps(polygon):
                print(f"\tPolygon {polygon} does not overlap {poly}")
                continue
            if poly.contains(polygon):
                print(
                    f"\tPolygon {polygon} is contained in {poly} - checking children..."
                )
                for child in poly.children:
                    if child.contains(polygon):
                        print(
                            f"\t\tPolygon {polygon} is contained in child {child} - creating new polygon"
                        )
                        exit_loop = True
                        break  # self.polygons = np.append(self.polygons, polygon)
                        return
                if exit_loop:
                    exit_loop = False
                    continue
                print(
                    f"\tPolygon {polygon} is not contained in a child element - adding as new child"
                )
                poly.children = np.append(poly.children, polygon)
                polygon.parent = poly
                return
                """if polygon.contains(poly):
                print(f"\tPolygon {poly} is contained in {polygon} - checking children...")
                """
                """for child in polygon.children:
                    if child.contains(poly):
                        print(f"\t\tPolygon {poly} is contained in child {child} - creating new polygon")
                        self.polygons.append(poly)
                        return
                print(f"\tPolygon {poly} is not contained in a child element - adding as new child")
                """
                """
                polygon.children = [poly]#np.append(polygon.children, poly)
                poly.parent = polygon
                return
                """
        self.polygons.append(polygon)

    """def nest(self):
        for poly in self.polygons:
            for other in self.polygons:
                if other == poly:
                    continue
                if poly.contains(other) and other not in poly.children:
                    poly.children = np.append(poly.children, other)
                    other.parent = poly
    """


class Polygon:
    num_polys: int = 0

    @staticmethod
    def reset():
        Polygon.num_polys = 0

    def __init__(self, points=None):
        self.points = (
            points if points is not None else np.empty(0, dtype=np.float64)
        )
        self.parent = None
        self.children = np.empty(0, dtype=Polygon)
        self.number = Polygon.num_polys
        Polygon.num_polys += 1

    def __repr__(self):
        return f"Polygon {self.number}"

    @property
    def bounding_box(self):
        if len(self.points) == 0:
            return None
        return (np.min(self.points, axis=0), np.max(self.points, axis=0))

    def contains(self, item):
        bb2 = self.bounding_box
        bb1 = item.bounding_box

        if (bb1[0] >= bb2[0]).all() and (bb1[1] <= bb2[1]).all():
            return True
        else:
            return False

    def overlaps(self, item):
        bb2 = self.bounding_box
        bb1 = item.bounding_box

        if (bb1[0][0] < bb2[1][0]) == (bb1[1][0] > bb2[0][0]) and (
            bb1[0][1] < bb2[1][1]
        ) == (bb1[1][1] > bb2[0][1]):
            return True
        else:
            return False

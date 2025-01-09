import numpy as np


class PolygonNester:
    def __init__(self, polygons=None):
        self.polygons = (
            polygons if polygons is not None else []
        )  # np.empty(0, dtype=Polygon)

    def dump(self):
        for poly in self.polygons:
            print(f"| {poly}")
            for child in poly.children:
                print(f"|\t {child}")

    def add_polygon(self, polygon, bulge=None):
        def recalc():
            for poly_recalc in poly_recalcs:
                self.add_polygon(poly_recalc)

        if bulge is not None:
            polygon.bulge = bulge
        exit_loop = False
        poly_recalcs = np.array([], dtype=Polygon)
        self.dump()
        print(f">>>Sorting {polygon}<<<")
        for poly in self.polygons:
            print(f"Checking {poly}")
            if not poly.overlaps(polygon):
                print(f"\t{polygon} does not overlap {poly}")
                continue
            if polygon.contains(poly):
                print(
                    f"\t{poly} is contained in {polygon} - removing to reorder..."
                )
                # print(np.where(self.polygons == poly))
                self.polygons = np.delete(
                    self.polygons, np.isin(self.polygons, [poly])
                )
                poly_recalcs = np.append(poly_recalcs, poly)
                poly_recalcs = np.append(poly_recalcs, poly.children)
                poly.children = np.array([], dtype=Polygon)
            if poly.contains(polygon):
                print(
                    f"\t{polygon} is contained in {poly} - checking children..."
                )
                if len(poly.children) > 0 and poly.children_contained_in(
                    polygon
                ):
                    print(
                        f"\t\tAll children of {poly} are contained in {polygon} - removing to reorder..."
                    )
                    polygon.parent = poly
                    poly_recalcs = np.append(poly_recalcs, poly.children)
                    poly.children = np.array([polygon], dtype=Polygon)
                    recalc()
                    return
                for child in poly.children:
                    if child.contains(polygon):
                        print(
                            f"\t\t{polygon} is contained in child {child} - creating new polygon"
                        )
                        exit_loop = True
                        break  # self.polygons = np.append(self.polygons, polygon)
                        return
                if exit_loop:
                    exit_loop = False
                    continue
                print(
                    f"\t{polygon} is not contained in a child element - adding as new child"
                )
                poly.children = np.append(poly.children, polygon)
                polygon.parent = poly
                recalc()
                return
        self.polygons = np.append(self.polygons, polygon)
        recalc()

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
        self.bulge = False
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

    @property
    def children_bounding_box(self):
        if len(self.children) == 0:
            return None
        return (
            np.min([ch.bounding_box[0] for ch in self.children], axis=0),
            np.max([ch.bounding_box[1] for ch in self.children], axis=0),
        )

    def contains(self, item):
        if item is None:
            return False
        bb2 = self.bounding_box
        bb1 = item.bounding_box

        if (bb1[0] >= bb2[0]).all() and (bb1[1] <= bb2[1]).all():
            return True
        else:
            return False

    def children_contained_in(self, item):
        if item is None or len(item.points) == 0:
            return False
        bb1 = self.children_bounding_box
        bb2 = item.bounding_box

        if (bb1[0] >= bb2[0]).all() and (bb1[1] <= bb2[1]).all():
            return True
        else:
            return False

    def overlaps(self, item):
        if item is None:
            return False
        bb2 = self.bounding_box
        bb1 = item.bounding_box

        if (bb1[0][0] < bb2[1][0]) == (bb1[1][0] > bb2[0][0]) and (
            bb1[0][1] < bb2[1][1]
        ) == (bb1[1][1] > bb2[0][1]):
            return True
        else:
            return False

    def children_overlap(self, item):
        if item is None or len(item.points) == 0:
            return False
        bb2 = self.children_bounding_box
        bb1 = item.bounding_box

        if (bb1[0][0] < bb2[1][0]) == (bb1[1][0] > bb2[0][0]) and (
            bb1[0][1] < bb2[1][1]
        ) == (bb1[1][1] > bb2[0][1]):
            return True
        else:
            return False

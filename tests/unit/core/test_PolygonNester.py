import numpy as np
import pytest
from FTL.core.PolygonNester import PolygonNester, Polygon


class Test_PolygonNester:
    def setup_class(self):
        pass

    def test_polygon_create_empty(self):
        Polygon.reset()
        p = Polygon()
        assert len(p.points) == 0
        assert p.points.shape == (0,)
        assert p.bounding_box is None
        assert p.number == 0
        assert p.__repr__() == "Polygon 0"

    def test_polygon_create(self):
        Polygon.reset()
        p = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        assert p.points == [(0, 0), (1, 0), (1, 1), (0, 1)]
        assert p.number == 0
        assert p.__repr__() == "Polygon 0"

    def test_polygon_create_enumerate(self):
        Polygon.reset()
        p1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        p2 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        assert p1.number == 0
        assert p2.number == 1

    def test_polygon_bounding_box_empty(self):
        p = Polygon()
        assert p.bounding_box is None

    def test_polygon_bounding_box_square(self):
        p = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        assert np.array_equal(p.bounding_box, [(0, 0), (1, 1)])

    def test_polygon_bounding_box_irr(self):
        p = Polygon([(0, 0), (1, 0), (1, 2), (0, 1)])
        assert np.array_equal(p.bounding_box, [(0, 0), (1, 2)])

    def test_polygon_bounding_box_line(self):
        p = Polygon([(0, 0), (1, 0), (1, 0), (0, 0)])
        assert np.array_equal(p.bounding_box, [(0, 0), (1, 0)])

    def test_polygon_children_bounding_box_1_rect(self):
        p = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])
        p.children = np.array([Polygon([(1, 1), (2, 1), (2, 2), (1, 2)])])
        print(p.children_bounding_box)
        assert np.array_equal(p.children_bounding_box, [(1, 1), (2, 2)])

    def test_polygon_children_bounding_box_2_rects(self):
        p = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])
        p.children = np.array(
            [
                Polygon([(1, 1), (2, 1), (2, 2), (1, 2)]),
                Polygon([(3, 3), (4, 3), (4, 4), (3, 4)]),
            ]
        )
        print(p.children_bounding_box)
        assert np.array_equal(p.children_bounding_box, [(1, 1), (4, 4)])

    """---------- BBOX COLLISION TEST ----------"""

    @pytest.mark.xfail
    def test_polygon_contains_empty(self):
        p1 = Polygon()
        p2 = Polygon()
        assert not p1.contains(p2)
        assert not p2.contains(p1)

    def test_polygon_contains_concentric_squares(self):
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(1, 1), (2, 1), (2, 2), (1, 2)])
        assert p1.contains(p2)
        assert not p2.contains(p1)

    def test_polygon_contains_disjunct_squares(self):
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(4, 4), (5, 4), (5, 5), (4, 5)])
        assert not p1.contains(p2)
        assert not p2.contains(p1)

    def test_polygon_contains_squares_kissing_corners_outside(self):
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(3, 3), (4, 3), (4, 4), (3, 4)])
        assert not p1.contains(p2)
        assert not p2.contains(p1)

    def test_polygon_contains_squares_kissing_edges_outside(self):
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(3, 1), (4, 1), (4, 2), (3, 2)])
        assert not p1.contains(p2)
        assert not p2.contains(p1)

    def test_polygon_contains_squares_kissing_corners_inside(self):
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        assert p1.contains(p2)
        assert not p2.contains(p1)

    def test_polygon_contains_squares_kissing_edges_inside(self):
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(0, 1), (1, 1), (1, 2), (0, 2)])
        assert p1.contains(p2)
        assert not p2.contains(p1)

    def test_polygon_contains_squares_overlapping(self):
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(1, 1), (4, 1), (4, 4), (1, 4)])
        assert not p1.contains(p2)
        assert not p2.contains(p1)

    def test_polygon_overlaps_concentric_squares(self):
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(1, 1), (2, 1), (2, 2), (1, 2)])
        assert p1.overlaps(p2)
        assert p2.overlaps(p1)

    def test_polygon_overlaps_disjunct_squares(self):
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(4, 4), (5, 4), (5, 5), (4, 5)])
        assert not p1.overlaps(p2)
        assert not p2.overlaps(p1)

    def test_polygon_overlaps_squares_kissing_corners_outside(self):
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(3, 3), (4, 3), (4, 4), (3, 4)])
        assert not p1.overlaps(p2)
        assert not p2.overlaps(p1)

    def test_polygon_overlaps_squares_kissing_edges_outside(self):
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(3, 1), (4, 1), (4, 2), (3, 2)])
        assert not p1.overlaps(p2)
        assert not p2.overlaps(p1)

    def test_polygon_overlaps_squares_kissing_corners_inside(self):
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        assert p1.overlaps(p2)
        assert p2.overlaps(p1)

    def test_polygon_overlaps_squares_kissing_edges_inside(self):
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(0, 1), (1, 1), (1, 2), (0, 2)])
        assert p1.overlaps(p2)
        assert p2.overlaps(p1)

    def test_polygon_overlaps_squares_overlapping(self):
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(1, 1), (4, 1), (4, 4), (1, 4)])
        assert p1.overlaps(p2)
        assert p2.overlaps(p1)

    def test_polygon_overlaps_overlapping_stripe(self):
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(-1, 1), (4, 1), (4, 2), (-1, 2)])
        assert p1.overlaps(p2)
        assert p2.overlaps(p1)

    """---------- BBOX COLLISION TEST ----------"""

    def test_polygon_children_overlap_empty(self):
        p = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])
        p.children = np.array(
            [
                Polygon([(1, 1), (2, 1), (2, 2), (1, 2)]),
                Polygon([(3, 3), (4, 3), (4, 4), (3, 4)]),
            ]
        )
        p_test = Polygon()
        assert not p.children_overlap(p_test)

    def test_polygon_children_overlap_1_rect(self):
        p = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])
        p.children = np.array(
            [
                Polygon([(1, 1), (2, 1), (2, 2), (1, 2)]),
                Polygon([(3, 3), (4, 3), (4, 4), (3, 4)]),
            ]
        )
        p_test = Polygon([(0.5, 0.5), (4.5, 0.5), (4.5, 4.5), (0.5, 4.5)])
        assert p.children_overlap(p_test)

    def test_polygon_children_dont_overlap_1_rect(self):
        p = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])
        p.children = np.array(
            [
                Polygon([(1, 1), (2, 1), (2, 2), (1, 2)]),
                Polygon([(3, 3), (4, 3), (4, 4), (3, 4)]),
            ]
        )
        p_test = Polygon([(0.5, 0.5), (0.8, 0.5), (0.8, 0.8), (0.5, 0.8)])
        print(p.children_bounding_box)
        print(p_test.bounding_box)
        assert not p.children_overlap(p_test)

    def test_polygon_children_contained_in_empty(self):
        p = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])
        p.children = np.array(
            [
                Polygon([(1, 1), (2, 1), (2, 2), (1, 2)]),
                Polygon([(3, 3), (4, 3), (4, 4), (3, 4)]),
            ]
        )
        p_test = Polygon()
        assert not p.children_contained_in(p_test)

    def test_polygon_children_contained_in_1_rect(self):
        p = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])
        p.children = np.array(
            [
                Polygon([(1, 1), (2, 1), (2, 2), (1, 2)]),
                Polygon([(3, 3), (4, 3), (4, 4), (3, 4)]),
            ]
        )
        p_test = Polygon([(0.5, 0.5), (4.5, 0.5), (4.5, 4.5), (0.5, 4.5)])
        print(p.children_bounding_box)
        print(p_test.bounding_box)
        assert p.children_contained_in(p_test)

    def test_polygon_children_not_contained_in_1_rect(self):
        p = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])
        p.children = np.array(
            [
                Polygon([(1, 1), (2, 1), (2, 2), (1, 2)]),
                Polygon([(3, 3), (4, 3), (4, 4), (3, 4)]),
            ]
        )
        p_test = Polygon([(0.5, 0.5), (0.8, 0.5), (0.8, 0.8), (0.5, 0.8)])
        print(p.children_bounding_box)
        print(p_test.bounding_box)
        assert not p.children_contained_in(p_test)

    """---------- NESTER TEST ----------"""

    def test_polygon_nester_create_empty(self):
        pn = PolygonNester()
        assert len(pn.polygons) == 0
        # assert pn.polygons.shape == (0,)

    def test_polygon_nester_create_from_polygon(self):
        p = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        pn = PolygonNester([p])
        assert len(pn.polygons) == 1
        assert pn.polygons[0] == p

    def test_polygon_nester_nest_square_containing_1_square(self):
        Polygon.reset()
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(1, 1), (2, 1), (2, 2), (1, 2)])
        pn = PolygonNester()
        print("P1: ", p1)
        print("P2: ", p2)
        pn.add_polygon(p1)
        assert pn.polygons == [p1]
        pn.add_polygon(p2)
        assert pn.polygons == [p1]
        assert p1.children == [p2]
        assert p2.parent == p1

    def test_polygon_nester_nest_square_containing_2_squares(self):
        Polygon.reset()
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(1, 1), (1.5, 1), (1.5, 1.5), (1, 1.5)])
        p3 = Polygon([(2, 2), (2.5, 2), (2.5, 2.5), (2, 2.5)])
        pn = PolygonNester()
        print("P1: ", p1)
        print("P2: ", p2)
        print("P3: ", p3)
        pn.add_polygon(p1)
        assert pn.polygons == [p1]
        pn.add_polygon(p2)
        assert pn.polygons == [p1]
        assert p1.children == [p2]
        assert p2.parent == p1
        pn.add_polygon(p3)
        assert pn.polygons == [p1]
        assert list(p1.children) == [p2, p3]
        assert p2.parent == p1
        assert p3.parent == p1

    def test_polygon_nester_nest_square_containing_2_concentric_squares(self):
        Polygon.reset()
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(1, 1), (2, 1), (2, 2), (1, 2)])
        p3 = Polygon([(1.25, 1.25), (1.75, 1.25), (1.75, 1.75), (1.25, 1.75)])
        pn = PolygonNester()
        print("P1: ", p1)
        print("P2: ", p2)
        pn.add_polygon(p1)
        assert pn.polygons == [p1]
        pn.add_polygon(p2)
        assert pn.polygons == [p1]
        assert p1.children == [p2]
        assert p2.parent == p1
        pn.add_polygon(p3)
        assert list(pn.polygons) == [p1, p3]
        assert list(p1.children) == [p2]
        assert p2.parent == p1
        assert p3.parent is None

    def test_polygon_nester_nest_square_containing_3_concentric_squares(self):
        Polygon.reset()
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(1, 1), (2, 1), (2, 2), (1, 2)])
        p3 = Polygon([(1.25, 1.25), (1.75, 1.25), (1.75, 1.75), (1.25, 1.75)])
        p4 = Polygon([(1.3, 1.3), (1.7, 1.3), (1.7, 1.7), (1.3, 1.7)])
        pn = PolygonNester()
        print("P1: ", p1)
        print("P2: ", p2)
        pn.add_polygon(p1)
        assert pn.polygons == [p1]
        print("-------------------")

        pn.add_polygon(p2)
        assert pn.polygons == [p1]
        assert p1.children == [p2]
        assert p2.parent == p1
        print("-------------------")

        pn.add_polygon(p3)
        assert list(pn.polygons) == [p1, p3]
        assert list(p1.children) == [p2]
        assert p2.parent == p1
        assert p3.parent is None
        print("-------------------")

        pn.add_polygon(p4)
        assert list(pn.polygons) == [p1, p3]
        assert list(p1.children) == [p2]
        assert p2.parent == p1
        assert list(p3.children) == [p4]
        assert p3.parent is None
        assert p4.parent == p3

    def test_polygon_nester_nest_square_containing_2_squares_kissing_corners(
        self,
    ):
        Polygon.reset()
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(1, 1), (2, 1), (2, 2), (1, 2)])
        p3 = Polygon([(2, 2), (2.5, 2), (2.5, 2.5), (2, 2.5)])
        pn = PolygonNester()
        print("P1: ", p1)
        print("P2: ", p2)
        pn.add_polygon(p1)
        assert pn.polygons == [p1]
        pn.add_polygon(p2)
        assert pn.polygons == [p1]
        assert p1.children == [p2]
        assert p2.parent == p1
        pn.add_polygon(p3)
        assert list(pn.polygons) == [p1]
        assert list(p1.children) == [p2, p3]
        assert p2.parent == p1
        assert p3.parent == p1

    def test_polygon_nester_nest_square_containing_2_squares_kissing_edges(
        self,
    ):
        Polygon.reset()
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(1, 1), (2, 1), (2, 2), (1, 2)])
        p3 = Polygon([(2, 1), (2.5, 1), (2.5, 2), (2, 2)])
        pn = PolygonNester()
        print("P1: ", p1)
        print("P2: ", p2)
        pn.add_polygon(p1)
        assert pn.polygons == [p1]
        pn.add_polygon(p2)
        assert pn.polygons == [p1]
        assert p1.children == [p2]
        assert p2.parent == p1
        pn.add_polygon(p3)
        assert list(pn.polygons) == [p1]
        assert list(p1.children) == [p2, p3]
        assert p2.parent == p1
        assert p3.parent == p1

    def test_polygon_nester_nest_square_containing_2_overlapping_squares(self):
        Polygon.reset()
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(1, 1), (2, 1), (2, 2), (1, 2)])
        p3 = Polygon([(1.5, 1.5), (2.5, 1.5), (2.5, 2.5), (1.5, 2.5)])
        pn = PolygonNester()
        print("P1: ", p1)
        print("P2: ", p2)
        pn.add_polygon(p1)
        assert pn.polygons == [p1]
        pn.add_polygon(p2)
        assert pn.polygons == [p1]
        assert p1.children == [p2]
        assert p2.parent == p1
        pn.add_polygon(p3)
        assert list(pn.polygons) == [p1]
        assert list(p1.children) == [p2, p3]
        assert p2.parent == p1
        assert p3.parent == p1

    def test_polygon_nester_nest_4_overlapping_squares(self):
        Polygon.reset()
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(1, 1), (4, 1), (4, 4), (1, 4)])
        p3 = Polygon([(2, 2), (5, 2), (5, 5), (2, 5)])
        p4 = Polygon([(3, 3), (6, 3), (6, 6), (3, 6)])
        pn = PolygonNester()
        print("P1: ", p1)
        print("P2: ", p2)
        print("P3: ", p3)
        print("P4: ", p4)
        pn.add_polygon(p1)
        pn.add_polygon(p2)
        pn.add_polygon(p3)
        pn.add_polygon(p4)
        assert list(pn.polygons) == [p1, p2, p3, p4]
        assert list(p1.children) == []
        assert list(p2.children) == []
        assert list(p3.children) == []
        assert list(p4.children) == []

    def test_polygon_nester_nest_3_overlapping_squares_enclosed_in_new_square(
        self,
    ):
        Polygon.reset()
        p1 = Polygon([(1, 1), (2, 1), (2, 2), (1, 2)])
        p2 = Polygon([(1.25, 1.25), (1.75, 1.25), (1.75, 1.75), (1.25, 1.75)])
        p3 = Polygon([(1.3, 1.3), (1.7, 1.3), (1.7, 1.7), (1.3, 1.7)])
        p4 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        pn = PolygonNester()
        print("P1: ", p1)
        print("P2: ", p2)
        print("P3: ", p3)
        print("P4: ", p4)
        pn.add_polygon(p1)
        assert pn.polygons == [p1]
        print("-------------------")

        pn.add_polygon(p2)
        assert pn.polygons == [p1]
        assert p1.children == [p2]
        assert p2.parent == p1
        print("-------------------")

        pn.add_polygon(p3)
        assert list(pn.polygons) == [p1, p3]
        assert list(p1.children) == [p2]
        assert p2.parent == p1
        assert p3.parent is None
        print("-------------------")

        pn.add_polygon(p4)
        assert list(pn.polygons) == [p4, p2]
        assert list(p4.children) == [p1]
        assert p1.parent == p4
        assert list(p2.children) == [p3]
        assert p3.parent == p2
        assert list(p3.children) == []
        assert p4.parent is None

    def test_polygon_nester_nest_3_overlapping_squares_enclosed_in_2_new_squares(
        self,
    ):
        Polygon.reset()
        p1 = Polygon([(1, 1), (2, 1), (2, 2), (1, 2)])
        p2 = Polygon([(1.25, 1.25), (1.75, 1.25), (1.75, 1.75), (1.25, 1.75)])
        p3 = Polygon([(1.3, 1.3), (1.7, 1.3), (1.7, 1.7), (1.3, 1.7)])
        p4 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p5 = Polygon([(-1, -1), (4, -1), (4, 4), (-1, 4)])
        pn = PolygonNester()
        print("P1: ", p1)
        print("P2: ", p2)
        print("P3: ", p3)
        print("P4: ", p4)
        pn.add_polygon(p1)
        assert pn.polygons == [p1]
        print("-------------------")

        pn.add_polygon(p2)
        assert pn.polygons == [p1]
        assert p1.children == [p2]
        assert p2.parent == p1
        print("-------------------")

        pn.add_polygon(p3)
        assert list(pn.polygons) == [p1, p3]
        assert list(p1.children) == [p2]
        assert p2.parent == p1
        assert p3.parent is None
        print("-------------------")

        pn.add_polygon(p4)
        assert list(pn.polygons) == [p4, p2]
        assert list(p4.children) == [p1]
        assert p1.parent == p4
        assert list(p2.children) == [p3]
        assert p3.parent == p2
        assert list(p3.children) == []
        assert p4.parent is None
        print("-------------------")

        pn.add_polygon(p5)
        pn.dump()
        assert list(pn.polygons) == [p5, p1, p3]

    def test_polygon_nester_add_rect_between_rect_and_children(self):
        Polygon.reset()
        p1 = Polygon([(0, 0), (3, 0), (3, 3), (0, 3)])
        p2 = Polygon([(1, 1), (2, 1), (2, 2), (1, 2)])
        p3 = Polygon([(1.25, 1.25), (1.75, 1.25), (1.75, 1.75), (1.25, 1.75)])
        p4 = Polygon([(0.5, 0.5), (2.5, 0.5), (2.5, 2.5), (0.5, 2.5)])
        pn = PolygonNester()
        print("P1: ", p1)
        print("P2: ", p2)
        print("P3: ", p3)
        print("P4: ", p4)
        pn.add_polygon(p1)
        assert pn.polygons == [p1]
        print("-------------------")

        pn.add_polygon(p2)
        assert pn.polygons == [p1]
        assert p1.children == [p2]
        assert p2.parent == p1
        print("-------------------")

        pn.add_polygon(p3)
        assert list(pn.polygons) == [p1, p3]
        assert list(p1.children) == [p2]
        assert p2.parent == p1
        assert p3.parent is None
        print("-------------------")

        pn.add_polygon(p4)
        pn.dump()
        assert list(pn.polygons) == [p1, p2]
        assert list(p1.children) == [p4]
        assert p4.parent == p1
        assert list(p2.children) == [p3]
        assert p3.parent == p2

    """
    def test_polygon_nester_nest_square_containing_2_squares(self):
        p1 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        p2 = Polygon([(1, 1), (2, 1), (2, 2), (1, 2)])
        p3 = Polygon([(3, 1), (4, 1), (4, 2), (3, 2)])
        pn = PolygonNester([p1, p2])
        print("P1: ", p1)
        print("P2: ", p2)
        print("P3: ", p3)
        pn.nest()
        print(p1.children)
        assert np.array_equal(p1.children, [p2, p3])
    """

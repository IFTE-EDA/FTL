from FTL.core.Geometry import AbstractGeom2D


class Geom2D_GMSH(AbstractGeom2D):
    def __init__(self, logger, name):
        super().__init__(logger, name)

    def add_line(self, p1, p2):
        pass

    def add_circle(self, center, radius, n_points):
        pass

    def add_arc(self, center, radius, start_angle, end_angle, n_points):
        pass

    def add_ellipse(self, center, major_axis, minor_axis, n_points):
        pass

    def add_polygon(self, points):
        pass

    def add_rectangle(self, corner1, corner2):
        pass

    def add_text(self, text, position, size):
        pass

    def add_image(self, filename, position, size):
        pass

    def add_spline(self, points, n_points):
        pass

    def add_bezier(self, points, n_points):
        pass

    def add_bspline(self, points, n_points):
        pass

    def add_bezier_surface(self, points, n_points):
        pass

    def add_bspline_surface(self, points, n_points):
        pass

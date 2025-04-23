import yaml
import gmsh
from YAMLParser import YAMLParser

# with open("stackup_test.yaml", "r") as f:
#    data = yaml.safe_load(f)
# print(data)

parser = YAMLParser("stackup_test.yaml")
parser.make_geometry()

gmsh.model.occ.synchronize()
gmsh.fltk.run()
# run meshing
# gmsh.model.mesh.generate(3)
# gmsh.fltk.run()

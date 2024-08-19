from KiCADParser import KiCADParser
import os

filename_easy = "test.kicad_pcb"
filename_meander = "MeanderTest.kicad_pcb"
filename_meander_hatch = "MeanderTest_hatch.kicad_pcb"
filename_sp2 = "SP2.kicad_pcb"

# parser = KiCADParser(filename_easy)
# parser = KiCADParser(filename_meander_hatch)
parser = KiCADParser(filename_sp2)
parser.render()
# layers = parser.render_layers()
# layers["F.Cu"].plot()

from KiCADParser import KiCADParser

filename_easy = "test.kicad_pcb"
filename_meander = "MeanderTest.kicad_pcb"

# parser = KiCADParser(filename_easy)
parser = KiCADParser(filename_meander)
parser.render()
# layers = parser.render_layers()
# layers["F.Cu"].plot()

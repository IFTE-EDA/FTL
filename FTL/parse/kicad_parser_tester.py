from KiCADParser import KiCADParser

filename_easy = "test.kicad_pcb"

parser = KiCADParser(filename_easy)
parser.render().plot()

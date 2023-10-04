import os
from .FileParser import *
from .MatrixTransformer import *
from .MeshLayer import *
from .RenderContainer import *

# from FTL.Transformations import *
from .Transformations import *
from .MainWindow import *

data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
uic_path = os.path.join(os.path.dirname(__file__), "UI")


def get_data(file: str) -> str:
    return os.path.join(data_path, file)


def get_uic(file: str) -> str:
    return os.path.join(uic_path, file + ".ui")


# from FTL.MatrixTransformer import MatrixTransformer
# from FTL.MeshLayer import MeshLayer
# from FTL.RenderContainer import RenderContainer
# from FTL.Transformations import *
# from FTL.MainWindow import MainWindow


# import FTL.MatrixTransformer
# import FTL.MeshLayer
# import FTL.RenderContainer
# from FTL.Transformations import *
# import FTL.MainWindow
# if __name__ == "__main__":
#    print("FTL module called! Yay!")

from pathlib import Path
import sys
import os
import vedo as v

sys.path.append("../FTL")
# sys.path.append(os.path.abspath(os.getcwd()))
import FTL
import pytest
import logging


class Test_MeshSlicer:
    def setup_class(self):
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        self.filename = (
            Path(__file__).parent / "data" / "Teststrip_DirBend.json"
        )
        self.parser = FTL.FileParser(self.filename)
        self.parser.parse()
        print(self.parser.transformations)
        print(self.parser.layers)

    @pytest.mark.order(0)
    def test_attrs(self):
        pass


if __name__ == "__main__":
    tester = Test_MeshSlicer()
    tester.setup_class()
    tester.test_attrs()

from enum import Enum
import vedo as v

ItemType = Enum("ItemType", "Layer Transformation Debug")


class RenderContainer:
    def __init__(self, plt=None):
        if plt is None:
            plt = v.Plotter(axes=1, interactive=True)
        self.plotter = plt
        self.layers = {}
        self.layers_visible = True
        self.transformations = {}
        self.transformations_visible = True
        self.debug = {}
        self.debug_visible = True

    def add_layer(self, label, item, vis=True):
        self.layers[label] = [item, vis]
        # debug("Adding to layers: {}={} ({})".format(label, item, vis))

    def add_transformation(self, label, item, vis=True):
        self.transformations[label] = [item, vis]
        # debug("Adding to transformations: {}={} ({})".format(label, item, vis))

    def add_debug(self, label, item, vis=True):
        self.debug[label] = [item, vis]
        # debug("Adding to debug: {}={} ({})".format(label, item, vis))

    def add_item(self, item_type, label, item, vis=True):
        container = self.get_container(item_type)
        container[label] = [item, vis]
        # debug ("Adding to {}: {}={}".format(container))

    def set_container_visibility(self, item_type, vis):
        if item_type == ItemType.Layer:
            self.layers_visible = vis
        elif item_type == ItemType.Transformation:
            self.transformations_visible = vis
        elif item_type == ItemType.Debug:
            self.debug_visible = vis
        else:
            raise TypeError("Unknown Container Item type")

    def set_item_visibility(self, item_type, label, vis):
        container = self.get_container(item_type)
        container[label][1] = vis

    def get_container(self, item_type):
        if item_type == ItemType.Layer:
            return self.layers
        elif item_type == ItemType.Transformation:
            return self.transformations
        elif item_type == ItemType.Debug:
            return self.debug
        else:
            raise TypeError("Unknown Container Item type")

    def get_struct(self):
        struct = {}
        labels = {
            "layers": "Layers",
            "transformations": "Transformations",
            "debug": "Debug",
        }
        for name in labels:
            label = labels[name]
            container = getattr(self, name)
            container_visible = getattr(self, name + "_visible")
            items = [
                [itemLabel, container[itemLabel][1]] for itemLabel in container
            ]
            struct[label] = [items, container_visible]
        return struct

    def render(self):
        renderList = []
        self.plotter.clear()
        for name in ["layers", "transformations", "debug"]:
            container = getattr(self, name)
            container_visible = getattr(self, name + "_visible")
            if not container_visible:
                continue

            for label in container:
                item, visible = container[label]

                if visible:
                    renderList.append(item)
        self.plotter.show(renderList, resetcam=False)
        print("+++ Rendering RC +++")
        self.plotter.render()

    def clear(self):
        self.layers.clear()
        self.layers_visible = True
        self.transformations.clear()
        self.transformations_visible = True
        self.debug.clear()
        self.debug_visible = True

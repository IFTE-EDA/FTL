class Item:
    def __init__(self, num: int = 0):
        print("Item created:", num)
        self.num = num

    def hello(self, name=None):
        if name:
            print("Hello, %s!" % name)
        else:
            print("Hello world!", self.num)


class Container(object):
    def __init__(self):
        print("Construct")
        self.item1 = Item(1)
        self.item2 = Item(3)
        self.item3 = Item(5)
        self.myitems = [self.item1, self.item2, self.item3]

    def test(self):
        print("Test")

    def __getattr__(self, attr):
        def ret(*args):
            for item in self.myitems:
                getattr(item, attr)(args)

        return ret


tester = Container()
tester.test()
tester.hello()
tester.hello("Mark")

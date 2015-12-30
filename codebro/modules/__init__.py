class Module:

    def __init__(self, parser, name):
        self.parser = parser
        self.name = name
        required_functions = ('__init__', 'run', )

        # check for required functions in modules
        for func in required_functions:
            try:
                getattr(self, func)

            except AttributeError:
                print(
                    "[-] Module %s : Missing function %s" %
                    (self.name, func))

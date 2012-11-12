class Module:

    def __init__(self, parser, name):
        self.parser = parser
        self.name = name
        
        # check for required functions in modules
        for required_functions in ('__init__', 'run', ):
            try :
                getattr(self, required_functions)
                
            except AttributeError:
                print ("[-] Module %s : Missing required function %s" % (self.name,
                                                                         required_functions))
        



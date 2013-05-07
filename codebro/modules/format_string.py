import re
import clang.cindex 

from modules import Module
from analyzer.models import ModuleDiagnostic
from analyzer.models import Module as ModuleDB


class FormatStringModule(Module):

    name = "Format String"

    
    def __init__(self, parser):
        Module.__init__(self, parser, self.name)
        self.hook_on = clang.cindex.CursorKind.CALL_EXPR
        
        
    def register(self):
        if self.hook_on not in self.parser.modules.keys():
            self.parser.modules[self.hook_on] = []
        
        self.parser.modules[self.hook_on].append(self)

        self.module = ModuleDB()
        self.module.name = self.name
        self.module.project = self.parser.project
        self.module.save()

        
    def run(self, node):
        if node.kind != self.hook_on:
            return
        
        caller_name = node.displayname
        
        # fmt str method 1 : lookup for known functions (printf, fprintf, sprintf, etc.)
        # obsolete : handled by -Wformat-security
        
        # fmt str method 2 : compare args in static strings at function call
        number_of_args = -1
        line = ""

        unexposed_refs = list(node.get_children())
        # unexposed_refs[0] is a ref to node, args start at offset 1

        for i in range(1, len(unexposed_refs)):
            found = False
            arg_ref_node = unexposed_refs[i]

            for subref in arg_ref_node.get_children() :

                if subref.kind == clang.cindex.CursorKind.STRING_LITERAL:
                    line = self.solve_string(subref)
                    if "%" in line :
                        number_of_args = len(unexposed_refs) - i - 1
                        found = True
                        break

            if found :
                break
            
        if len(line) == 0  : return            # no static string literal found
        if "%" not in line : return            # no format symbol found
        if line.count("%%") == 2*line.count("%")  : return            # no static string literal found

        num_singles = line.count("%") - 2*line.count("%%")

        if number_of_args < num_singles:
            msg = "%s : args number mismatch (%d declared in string, %d found in function)"
            msg%= (caller_name, num_singles, number_of_args)
            print '++++', msg
            
            m = ModuleDiagnostic()
            m.name = self.name
            m.project = self.parser.project
            m.module = self.module
            m.filepath = node.location.file.name
            m.line = node.location.line
            m.message = msg
            m.save()
            
                
    def solve_string(self, node):
        start = node.extent.start.offset
        end = node.extent.end.offset

        with open(node.location.file.name, 'r') as f:
            data = f.read()
            res = data[start:end].strip()

        print len(res), ":", res
        return res


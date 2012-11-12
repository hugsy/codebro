from clang.cindex import CursorKind
from codebro.modules import Module
from browser.models import ModuleDiagnostic
from browser.models import Module as ModuleDB
import re


class FormatStringModule(Module):

    name = "Format String"

    
    def __init__(self, parser):
        Module.__init__(self, parser, self.name)
        self.hook_on = CursorKind.CALL_EXPR
        
        
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
        # todo

        # fmt str method 2 : compare args in static strings at function call
        number_of_args = -1
        line = ""

        unexposed_refs = list(node.get_children())
        # unexposed_refs[0] is a ref to node, args start at offset 1

        for i in range(len(unexposed_refs[1:])):
            arg_ref_node = unexposed_refs[i]
            
            if arg_ref_node.kind == CursorKind.UNEXPOSED_EXPR :
                childs = list(arg_ref_node.get_children())
                if len(childs) == 0:
                    continue
                arg_node = childs[0]

            if arg_node.kind == CursorKind.UNEXPOSED_EXPR:
                arg_node = list(arg_node.get_children())[0]
            
            if arg_node.kind == CursorKind.STRING_LITERAL:
                line = self.solve_string(arg_node)
                if "%" in line :
                    number_of_args = len(unexposed_refs) - i - 1
                    break
                
        if len(line) == 0  : return            # no static string literal found
        if "%" not in line : return            # no format symbol found
        if line.count("%%") == 2*line.count("%")  : return            # no static string literal found

        num_singles = line.count("%") - line.count("%%")

        if number_of_args < num_singles:
            msg = "In %s Number of arguments do not match (%d declared in string, %d found in function)"
            msg%= (caller_name, num_singles, number_of_args)
            
            m = ModuleDiagnostic()
            # m.uid = self.uid
            m.name = self.name
            m.project = self.parser.project
            m.module = self.module
            m.filepath = node.location.file.name
            m.line = node.location.line
            m.message = msg
            m.save()
            
                
    def solve_string(self, node):
        pattern = re.compile(r'[^"]*"(.*)"[^"]*')
        res = ""
        
        with open(node.location.file.name, 'r') as f:
            data = [x[:-1] for x in f.readlines()]
       
        # line && col start at 1 + remove dbl quote
        for line in data[node.extent.start.line-1:node.extent.end.line]:
            res+= re.sub(pattern, r'\1', line)
        
        return res


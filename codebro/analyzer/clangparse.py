from os import access, R_OK, walk, path, listdir

from clang.cindex import CursorKind
from clang.cindex import Index
from clang.cindex import TypeKind

from codebro import settings
from modules.format_string import FormatStringModule
from .models import Debug


class ClangParser:
    """
    
    """
    
    def __init__(self, project, clang_args=[]):
        """
        
        """
        self.project = project
        self.root_dir = self.project.code_path
        self.index = Index.create()
        self.parser = None
        
        self.clang_args = settings.CLANG_PARSE_OPTIONS
        self.clang_args+= self.include_sub_dirs()
        self.clang_args+= clang_args
        
        self.diags = []
        self.modules = {}
        self.register_modules( [FormatStringModule,] )
        

    def register_modules(self, modules):
        """
        
        """
        for module in modules :
            m = module(self)

            # check for existing module id
            already_exists = False
            for mod in self.modules.values() :
                if m.uid == mod.uid :
                    print("Module Id %d already declared for module '%s', cannot add" % (mod.uid, mod.name))
                    already_exists = True
                    break

            if not already_exists:
                m.register()
                
                if settings.DEBUG :
                    print("Using module '%s' on project '%s'" % (m.name, m.module.project.name))

            
    def include_sub_dirs(self):
        """
        
        """
        subdirs = []
        for root, dirs, files in walk(self.root_dir, topdown=True, followlinks=False):
            for d in dirs :
                fullpath = fpath = path.join(root, d)
                if path.isdir(fullpath):
                    subdirs.append("-I" + fullpath)           
        return subdirs

    
    @staticmethod
    def enumerate_files(root_dir, extensions):
        """
        
        """
        for root, dirs, files in walk(root_dir, topdown=True, followlinks=False):
            for f in files :
                fpath = path.join(root, f)
                if not access(fpath, R_OK):
                    continue
                
                for ext in extensions :
                    if fpath.endswith(ext):
                        yield(fpath)


    def inspect(self, node, caller):
        """
        
        """

        if node.kind == CursorKind.FUNCTION_DECL :
            caller = node.spelling
            
            if node.location.file and not node.location.file.name.endswith(".h") :
                return_type = node.type.get_result()
                args = []
            
                for c in node.get_children():
                    if c.kind == CursorKind.PARM_DECL:
                        args.append( (c.type.kind.spelling, c.displayname) )
                    
                func = [node.spelling,
                        node.location.file.name,
                        node.location.line,
                        return_type.kind.spelling,
                        args ]
            
                yield(func)

                
        elif node.kind == CursorKind.CALL_EXPR:
            infos = {}
            infos['name'] = node.displayname
            infos['line'] = node.location.line

            for module in self.modules[CursorKind.CALL_EXPR] :
                module.run(node)
                
            yield( (caller, infos) )

            
        for n in node.get_children():
            for i in self.inspect(n, caller) :
                yield i

                
    def get_xref_calls(self, filename):
        """
        
        """
        print ("Parsing '%s' with args : %s" % (filename, self.clang_args))
        self.parser = self.index.parse(filename, args=self.clang_args)

        if self.parser:
            if len(self.parser.diagnostics) :
                for d in self.parser.diagnostics:
                    cat, loc, msg = d.category_number, d.location, d.spelling
                    if loc is None  :
                        fil, lin = "Unknown", 0
                    elif loc.file is None :
                        fil, lin = "Unknown", loc.line
                    else :
                        fil, lin = loc.file.name, loc.line
                        
                    self.diags.append((cat, fil, lin, msg))
            
            for node in self.inspect(self.parser.cursor, "<OutOfScope>"):
                yield node


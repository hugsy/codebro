from clang.cindex import CursorKind
from clang.cindex import Index
from clang.cindex import TypeKind

from os import access, R_OK, walk, path

        
class ClangParser:
    """
    
    """
    
    def __init__(self, root_dir=[], clang_args=[]):
        """
        
        """        
        self.root_dir = root_dir
        self.index = Index.create()
        self.parser = None
        self.clang_args = clang_args

        
    def enumerate_files(self, extension):
        """
        
        """
        for root, dirs, files in walk(self.root_dir, topdown=True, followlinks=False):
            for f in files :
                fpath = path.join(root, f)
                if not access(fpath, R_OK):        continue
                if not fpath.endswith(extension):  continue
                yield(fpath)

                
    def get_declared_functions_in_file(self, filename, ignore_include_headers=True):
        """
        
        """
        self.parser = self.index.parse(filename, args=self.clang_args)
        
        for cursor in self.parser.cursor.get_children():
            
            if not cursor.location.file:
                continue

            if ignore_include_headers and cursor.location.file.name.endswith(".h"):
                continue


            if cursor.kind == CursorKind.FUNCTION_DECL:
                return_type = cursor.type.get_result()
                args = []
            
                for c in cursor.get_children():
                    if c.kind == CursorKind.PARM_DECL:
                        args.append( (c.type.kind.spelling, c.displayname) )
                    
                func = [cursor.spelling,
                        cursor.location.file.name,
                        cursor.location.line,
                        return_type.kind.spelling,
                        args ]
            
                yield(func)


    def inspect(self, cursor, caller):
        """
        
        """
        for cur in cursor.get_children():
           
            # get into if/switch/etc. statements
            if cur.kind == CursorKind.IF_STMT:
                self.inspect(cur, caller)
            elif cur.kind == CursorKind.SWITCH_STMT :
                self.inspect(cur, caller)
            elif cur.kind == CursorKind.COMPOUND_STMT :
                self.inspect(cur, caller)
            
            elif cur.kind == CursorKind.CALL_EXPR:
                infos = {
                    'name' : cur.displayname,
                    'line' : cur.location.line
                    }
                
                yield( (caller, infos) )

                
    def get_xref_calls(self, filename):
        """
        
        """
        self.parser = self.index.parse(filename, args=self.clang_args)
        
        for cursor in self.parser.cursor.get_children():
            
            # only interested in function declaration
            if cursor.kind != CursorKind.FUNCTION_DECL:
                continue

            current_function_name = cursor.spelling
            
            # browse function (look for '{')
            for c in cursor.get_children():
                if c.kind == CursorKind.PARM_DECL:
                    if c.kind != CursorKind.COMPOUND_STMT:
                        continue
                    
                for res in self.inspect(c, current_function_name):
                    yield res

            # and goto next function


    def debug(self):
        """
        
        """       
        if self.parser is None :
            return "Parser not initialized"
        
        if len(self.parser.diagnostics) :
            msg = []
            for d in self.parser.diagnostics:
                msg.append("%s(%d) in %s: %s" % (d.category_name,
                                                 d.category_number,
                                                 d.location,
                                                 d.spelling))

            return msg

        return "No parsing errors raised"
                          

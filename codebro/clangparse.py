from clang.cindex import CursorKind
from clang.cindex import Index
from clang.cindex import TypeKind

from os import access, R_OK, walk, path, listdir


class ClangParser:
    """
    
    """
    
    def __init__(self, root_dir=".", clang_args=[]):
        """
        
        """        
        self.root_dir = root_dir
        self.index = Index.create()
        self.parser = None
        self.clang_args = self.include_sub_dirs()

        
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


    def inspect(self, node, caller):
        """
        
        """

        if node.kind == CursorKind.CALL_EXPR:
            infos = {
                'name' : node.displayname,
                'line' : node.location.line
                }
            yield( (caller, infos) )
            
        else :     
            if node.kind == CursorKind.FUNCTION_DECL:
                caller = node.spelling

            for n in node.get_children():
                for i in self.inspect(n, caller) :
                    yield i
                
        
    def get_xref_calls(self, filename):
        """
        
        """
        self.parser = self.index.parse(filename, args=self.clang_args)
        if self.parser:
              for node in self.inspect(self.parser.cursor, "root"):
                yield node


    def get_diagnostics(self):
        """
        
        """       
        if self.parser is None :
            return []
        
        if len(self.parser.diagnostics) :
            msg = []
            for d in self.parser.diagnostics:
                msg.append((d.category_number,
                            d.location,
                            d.spelling))

            return msg

        return []
                          

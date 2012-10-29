from django.http import Http404
from django.contrib import messages
from django.db import IntegrityError

from codebro import settings
from codebro.clangparse import ClangParser

from browser.models import File, Function, Argument, Xref

from tempfile import mkstemp
from time import time
from zipfile import ZipFile, is_zipfile
from tarfile import TarFile, is_tarfile


from os import fdopen, mkdir, unlink



class Archive:
    ZIP_FILE = 1
    TGZ_FILE = 2
    TBZ_FILE = 3
    
    handlers = {
        ZIP_FILE : [ZipFile, ZipFile.close, ZipFile.extractall, 'r', is_zipfile],
        TGZ_FILE : [TarFile.open, TarFile.close, TarFile.extractall, 'r:gz', is_tarfile],
        TBZ_FILE : [TarFile.open, TarFile.close, TarFile.extractall, 'r:bz2', is_tarfile],
        }

    extensions = {
        ZIP_FILE : [".zip",],
        TGZ_FILE : [".tar.gz", ".tgz"], 
        TBZ_FILE : [".tar.bz2", ".tbz2"],
        }
    
    
    def __init__(self, fname, t):
        self.name = fname
        self.type = t
        self.handler = Archive.handlers[self.type]
 
    def extract(self, path):
        handle_open, handle_close, handle_extract, handle_mode, handle_check = self.handler
        if not handle_check(self.name):
            raise Exception("Invalid file type (%#x) '%s'" % (self.type, self.name))
        
        p = handle_open(self.name, handle_mode)
        handle_extract(p, path)
        handle_close(p)
        return True

    
def is_valid_file(f):
    if f.size >= settings.MAX_UPLOAD_SIZE :
        return False

    ext = None
    for i in Archive.extensions :
        for extension in Archive.extensions[i]:
            if f.name.endswith(extension) :
                ext = i
                break

    if ext is None :
        return False

    return ext


def extract_archive(archive_name, project_name, extension):
    path = "%s/%s" % (settings.SRC_PATH, project_name)
    try:
        mkdir(path, 0755)
    except OSError:
        unlink(archive_name)
        return None
    
    archive = Archive(archive_name, extension)
    archive.extract(path)

    unlink(archive_name)
    return path


def handle_uploaded_file(file_o, project_name, extension):
    fd, fname = mkstemp(prefix="codebro_tmp")

    with fdopen(fd, 'w') as f:
        for chunk in file_o.chunks():
            f.write(chunk)

    return extract_archive(fname, project_name, extension)


def valid_method_or_404(request, methods):
    if not request.method in methods:
        raise Http404


def is_project_parsed(project):
    return project.function_definition_number != 0 \
        and project.file_number != 0

def is_project_xrefed(project):
    return is_project_parsed(project) \
        and project.xref_number != 0


def clang_parse_project(r, p):
    """
    
    """
    cparser = ClangParser(p.get_code_path())
    
    for cur_file in cparser.enumerate_files(p.language.extension) :
        f = File()
        f.name = cur_file
        f.project = p
        f.save()

        p.file_number += 1
        
        for cur_func in cparser.get_declared_functions_in_file(cur_file):
           
            func, created = Function.objects.get_or_create(name = cur_func[0],
                                                           file = f,
                                                           project = p)
            
            
            # update issue 
            if not created:
                if cur_func[3] != func.line :
                    messages.warning(r,
                                     "Function '%s' in '%s' is declared twice (l.%d, and l.%d)" %
                                     (func.name, func.file.name, func.line, cur_func[2]) )


            func.line  = cur_func[2]                    
            func.rtype = cur_func[3]

            
            func.save()

            args = cur_func[4]
            
            if created:
                p.function_definition_number += 1
            
                for cur_arg_name, cur_arg_type in args:
                    arg = Argument()
                    arg.name, arg.type = (cur_arg_name, cur_arg_type)
                    arg.function = func
                    arg.save()

    p.is_parsed = True                

    p.save()
    messages.info(r, "Successfully parsed")  
    return True


def clang_xref_project(r, p):
    """
    
    """
    cparser = ClangParser(p.get_code_path())
    xref_num = 0
    
    for f in p.file_set.all():
        for (caller, infos) in cparser.get_xref_calls(f.name):
            caller, created = Function.objects.get_or_create(name=caller, file=f, project=p)
            callee, created = Function.objects.get_or_create(name=infos['name'], file=f, project=p)

            xref = Xref()
            xref.project = p
            xref.calling_function = caller
            xref.called_function = callee
            xref.called_function_line = infos['line']

            xref.save()
            xref_num+=1

    if xref_num :
        p.xref_number = xref_num
        p.save()
        messages.success(r, "Successfully xref-ed")
        return True
    
    else :
        messages.error(r, "No xref have been established")
        return False
    

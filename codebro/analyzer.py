from codebro.clangparse import ClangParser
from django.contrib import messages

from browser.models import File
from browser.models import Function
from browser.models import Argument
from browser.models import Xref

from threading import Thread

from codebro import settings


def insert_functions_from_file(p, fname, cparser):
    """
    
    """
    f = File()
    f.name = fname
    f.project = p
    f.save()
    
    for funcname, filename, line, rtype, args in cparser.get_declared_functions_in_file(f.name):
        
        func, created = Function.objects.get_or_create(name = funcname,
                                                       file = f,
                                                       project = p)
            
        
        # update issue 
        # if not created:
            # if line != func.line :
                # messages.warning(r,
                                 # "Function '%s' in '%s' is declared twice (l.%d, and l.%d)" %
                                 # (func.name, func.file.name, func.line, cur_func[2]) )


        func.line  = line
        func.rtype = rtype

        func.save()
        
        if settings.DEBUG :
            print func.file.name, func.name, func.line

        if created:
            args_o = []
            for cur_arg_name, cur_arg_type in args:
                arg = Argument()
                arg.name, arg.type = (cur_arg_name, cur_arg_type)
                arg.function = func

            for arg_o in args_o: arg_o.save()
                
    
def clang_parse_project(r, p):
    """
    
    """
    cparser = ClangParser(p.get_code_path())

    for cur_file in cparser.enumerate_files(p.language.extension) :
        insert_functions_from_file(p, cur_file, cparser)

    p.is_parsed = True                

    p.save()
    messages.info(r, "Successfully parsed")  
    return True


def clang_xref_project(r, p):
    """
    
    """
    cparser = ClangParser(p.get_code_path())
    
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

            if settings.DEBUG :
                print xref.calling_function.name, 'calls', xref.called_function.name, 'line', xref.called_function_line

    if p.xref_set.count() :
        messages.success(r, "Successfully xref-ed")
        return True
    
    else :
        messages.error(r, "No xref have been established")
        return False

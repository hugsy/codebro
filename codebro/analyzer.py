from codebro.clangparse import ClangParser
from django.contrib import messages

from browser.models import File
from browser.models import Function
from browser.models import Argument
from browser.models import Xref
from browser.models import Debug

from threading import Thread

from codebro import settings

    
def clang_parse_project(r, p):
    """
    
    """

    clang_xref_project(r, p)
    p.is_parsed = True                

    p.save()
    messages.info(r, "Successfully parsed")  
    return True


def clang_xref_project(r, p):
    """
    
    """
    cparser = ClangParser(p)
    
    for cur_file in ClangParser.enumerate_files(cparser.root_dir, [p.language.extension,]) :

        f, c = File.objects.get_or_create(name = cur_file, project = p)
        if c :
            f.save()
            
        for out in cparser.get_xref_calls(f.name):
            if len(out) == 5:
                # FUNC_DECL
                funcname, filename, line, rtype, args = out
                func, created = Function.objects.get_or_create(name = funcname,
                                                               file = f,
                                                               project = p)

                func.line  = line
                func.rtype = rtype
                func.save()
        
                if created:
                    args_o = []
                    for cur_arg_name, cur_arg_type in args:
                        arg = Argument()
                        arg.name, arg.type = (cur_arg_name, cur_arg_type)
                        arg.function = func

                    for arg_o in args_o: arg_o.save()

                if settings.DEBUG :
                    print func.file.name, func.name, func.line, args
                    
            
            if len(out) == 2:
                # CALL_EXPR
                (caller, infos) = out
                caller, created = Function.objects.get_or_create(name=caller, file=f, project=p)
                callee, created = Function.objects.get_or_create(name=infos['name'], file=f, project=p)

                xref = Xref()
                xref.project = p
                xref.calling_function = caller
                xref.called_function = callee
                xref.called_function_line = infos['line']

                xref.save()

                if settings.DEBUG :
                    print xref.calling_function.name, 'calls', xref.called_function.name, 'line', xref.called_function_line, 'in', f.name


    
    for cat, fil, lin, error_msg in cparser.diags:
        dbg = Debug()
        dbg.category = cat
        dbg.filepath = fil
        dbg.line = lin
        dbg.message = error_msg
        dbg.project = p
        dbg.save()
        
    
    if p.xref_set.count() :
        messages.success(r, "Successfully xref-ed")
        return True
    
    else :
        messages.error(r, "No xref have been established")
        return False

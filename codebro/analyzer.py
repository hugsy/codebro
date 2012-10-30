from codebro.clangparse import ClangParser
from django.contrib import messages

from browser.models import File
from browser.models import Function
from browser.models import Argument
from browser.models import Xref


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

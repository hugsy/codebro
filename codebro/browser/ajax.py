import json
import hashlib
import xml.sax
import os

from django.core import serializers
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.html import escape
from dajax.core import Dajax
from dajaxice.decorators import dajaxice_register

from codebro import settings
from analyzer.analysis import clang_parse_project, clang_parse_file
from analyzer.models import Project, Function, ModuleDiagnostic
from browser.helpers import valid_method_or_404
from browser.helpers import generate_graph



@dajaxice_register
def update_files(request, value, project_id):
    """
    
    """
    dajax = Dajax()
    
    try :
        p = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return dajax.json()
    
    out = []
    
    for f in Function.objects.filter(name__contains=value, project=p):
        fmt_str = "<option value='{0}'>{1} in {2}:{3}</option>"
        line = f.line if f.line is not None else 0
        filename = f.file.name if f.file is not None else "Unknown"
        funcname = f.name

        args = [serializers.serialize("xml", [f,]), ]
        args+= [ escape(x) for x in [funcname, filename, line] ]
        line = fmt_str.format( *args )
        out.append(line)

    dajax.assign('#function_files', 'innerHTML', '\n'.join(out))
    return dajax.json()


@dajaxice_register
def ajax_project_parse(request, project_id):
    """
    
    """
    project = get_object_or_404(Project, pk=project_id)
    ctx = {"status" : -1, "message": ""}

    if project.is_parsed:
        ctx["status"] = 1
        ctx["message"] = "Already parsed"
        return json.dumps(ctx)

    if clang_parse_project(request, project):
        ctx["status"]  = 0
        ctx["message"] = "Successfully parsed ... Reloading page"
    else :
        ctx["status"]  = 1
        ctx["message"] = "Failed to parse..."
        
    return json.dumps(ctx)


@dajaxice_register
def ajax_file_parse(request, project_id, filename):
    """
    
    """
    project = get_object_or_404(Project, pk=project_id)
    ctx = {"status" : -1, "message": ""}

    filerefs = project.file_set.filter( name=filename )
    if len(filerefs) == 0:
        ctx["status"] = 1
        ctx["message"] = "Invalid filename %s" % filename
        return json.dumps(ctx)

    fileref = filerefs[0]
    
    if project.is_parsed or fileref.is_parsed:
        ctx["status"] = 1
        ctx["message"] = "Already parsed"
        return json.dumps(ctx)
    
    if clang_parse_file(request, project, fileref):
        ctx["status"]  = 0
        ctx["message"] = "Successfully parsed ... Reloading page"
    else :
        ctx["status"]  = 1
        ctx["message"] = "Failed to parse..."
        
    return json.dumps(ctx)


@dajaxice_register
def ajax_project_unparse(request, project_id):
    """
    
    """
    project = get_object_or_404(Project, pk=project_id)
    ctx = {"status" : -1, "message": ""}

    ModuleDiagnostic.objects.filter(module__project=project).delete()
    project.module_set.all().delete()
    project.xref_set.all().delete()
    project.debug_set.all().delete()
    project.file_set.all().update( is_parsed=False )
    
    project.is_parsed = False
    project.save()
    
    ctx["status"]  = 0
    ctx["message"] = "Successfully unparsed ... Reloading page"
    return json.dumps(ctx)


@dajaxice_register
def ajax_add_funcgraph_link(request, f, d, x):
    """
    
    """
    valid_method_or_404(request, ["POST",])
    dajax = Dajax()

    try : depth = int(d)
    except ValueError : depth = -1
    xref = x if x is not None else True
    
    try :
         for obj in serializers.deserialize("xml", f):
            data = obj
            data.save()
            break
            
         caller_f = data.object

         if not isinstance(caller_f, Function):
             return dajax.json()
        
         project = caller_f.project
         
         if not project.is_parsed:
             return dajax.json()
         
    except xml.sax.SAXParseException:
        return dajax.json()

    
    project = caller_f.project
    
    base = "p%d-f%d-fu%d" % (project.id, caller_f.id, caller_f.id)
    base+= "@%d" % depth  if depth > 0 else 0

    basename = hashlib.sha256(base).hexdigest() + ".svg"
    pic_name = settings.CACHE_PATH + "/" + basename

    if not os.access(pic_name, os.R_OK):
        ret, err = generate_graph(pic_name, project, caller_f, xref, depth)
        if ret==False :
            return dajax.json()

    fmt_str = "<tr>"
    fmt_str+= "<td width=\"40%\">{0}</td>"
    fmt_str+= "<td width=\"15%\">{1}</td>"
    fmt_str+= "<td width=\"15%\">{2}</td>"
    fmt_str+= "<td width=\"30%\"><a href=\"{3}\">{0}</a></td>"
    fmt_str+= "</tr>"

    line = fmt_str.format(caller_f.name,
                          xref,
                          depth,
                          reverse('browser.views.get_cache',args=(basename,)))
    dajax.assign('#table-graphs', 'innerHTML', line)
    return dajax.json()


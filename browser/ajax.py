from dajax.core import Dajax
from dajaxice.decorators import dajaxice_register
from dajaxice.exceptions import DajaxiceError
from django.utils import simplejson

from django.core import serializers
from browser.models import Project, Function, Xref
from django.shortcuts import get_object_or_404

from codebro import settings

from browser.helpers import clang_parse_project, clang_xref_project
from browser.helpers import is_project_parsed, is_project_xrefed


@dajaxice_register
def update_files(request, value, project_id):
    dajax = Dajax()
    
    try :
        p = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return dajax.json()
    
    out = []
    funcs = Function.objects.filter(name__contains=value, project=p)
    
    for f in funcs:
        data = serializers.serialize("xml", [f,])
        out.append("<option value='{2}'>{1} in {0}:{3}</option>".format(f.file.name, f.name, data, f.line))

    dajax.assign('#function_files', 'innerHTML', '\n'.join(out))
    return dajax.json()


@dajaxice_register
def ajax_project_parse(request, project_id):

    project = get_object_or_404(Project, pk=project_id)
    ctx = {"status" : -1,
           "message": ""}

    if is_project_parsed(project):
        ctx["status"] = 1
        ctx["message"] = "Already parsed"
        return simplejson.dumps(ctx)

    if clang_parse_project(request, project):
        ctx["status"]  = 0
        ctx["message"] = "Successfully parsed ... Reloading page"
    else :
        ctx["status"]  = 1
        ctx["message"] = "Failed to parse..."
        
    return simplejson.dumps(ctx)


@dajaxice_register
def ajax_project_xref(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    ctx = {"status" : -1,
           "message": ""}
    
    if not is_project_parsed(project):
        ctx["status"]  = 1
        ctx["message"] = "Project '%s' must be parsed first"%project.name
        return simplejson.dumps(ctx)

    if is_project_xrefed(project):
        ctx["status"]  = 1
        ctx["message"] = "Project '%s' already xref-ed"%project.name
        return simplejson.dumps(ctx)
      
    if clang_xref_project(request, project):
        ctx["status"]  =  0
        ctx["message"] = "Successfully xref-ed ... Reloading page"
    else :
        ctx["status"]  =  1
        ctx["message"] =  "Failed to xref..."
        
    return simplejson.dumps(ctx)
    

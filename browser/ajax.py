from dajax.core import Dajax
from dajaxice.decorators import dajaxice_register
from dajaxice.exceptions import DajaxiceError

from django.core import serializers
from browser.models import Project, Function

from codebro import settings

@dajaxice_register
def update_files(request, value, project_id):
    dajax = Dajax()
    
    try :
        p = Project.objects.get(pk=project_id)
        
    except Project.DoesNotExist:
        messages.error(request, "Invalid project id")
        raise Exception("Invalid project id")
        raise DajaxiceError("Invalid project id")
    
    out = []
    funcs = Function.objects.filter(name__contains=value, project=p)
    
    for f in funcs:
        data = serializers.serialize("xml", [f,])
        out.append("<option value='{2}'>{1} in {0}:{3}</option>".format(f.file.name, f.name, data, f.line))

    dajax.assign('#function_files', 'innerHTML', '\n'.join(out))
    return dajax.json()


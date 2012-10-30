from browser.models import Project 
from browser.models import Language
from browser.models import File
from browser.models import Function 
from browser.models import Argument
from browser.models import Xref

from browser.forms import ProjectForm

from browser.helpers import valid_method_or_404
from browser.helpers import handle_uploaded_file
from browser.helpers import is_valid_file, is_project_parsed, is_project_xrefed
from browser.helpers import generate_graph

from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ValidationError, MultipleObjectsReturned
from django.core import serializers

from codebro import settings
from codebro.renderer import CodeBroRenderer

from os import listdir, access, R_OK
from os.path import abspath, isdir, islink

from xml.sax import SAXParseException 

from hashlib import sha1

import re


def index(request):
    """
    index page
    """
    ctx = {'projects': Project.objects.all().order_by('-added_date')[:4]}
    return render(request, 'index.html', ctx)



def grep(pat, filename):
    """
    shitty under-optimized grep function
    """
    blocks = []
    line_num = 0
    
    with open(filename, 'r') as f :
        for line in f.xreadlines():
            match = pat.search(line)
            if match is not None:
                blocks.append([line_num, match.string])
            line_num += 1
            
    return blocks 
            

def search(request):
    """
    search engine
    """

    valid_method_or_404(request, ["POST"])
    
    if "pattern" in request.POST:
        blocks = {}
        pat = re.compile(request.POST["pattern"], re.IGNORECASE)
        
        for f in File.objects.all() :
            ret = grep(pat, f.name)
            if len(ret) > 0:
                if f.project.name not in blocks:
                    blocks[f.project] = {}
                if f.name not in blocks[f.project]:
                    blocks[f.project][f] = {}
                blocks[f.project][f].update(ret) 
            
        ctx = {'pattern': request.POST["pattern"],
               'num_matches' : len(blocks),
               'blocks': blocks}
        
    else:
        ctx = {'pattern': ""}
        
    return render(request, "search.html", ctx)


def list(request):
    """
    enumerates all projects
    """
    
    projects = Project.objects.all().order_by('-id')
    paginator = Paginator(projects, 10)

    page = request.GET.get('page')
    try:
        projects = paginator.page(page)
        
    except PageNotAnInteger:
        projects = paginator.page(1)
        
    except EmptyPage:
        projects = paginator.page(paginator.num_pages)
        
    ctx = {'projects': projects}
    return render(request, 'list.html', ctx)


def project_detail(request, project_id):
    """
    show all details for a given project
    """
    p = get_object_or_404(Project, pk=project_id)
    setattr(p, "code_path", p.get_code_path())
    
    if not "file" in request.GET :
        cur_file = p.code_path
    else:
        cur_file = abspath(request.GET["file"])
        
    data = []

    if not cur_file.startswith(p.code_path):
        messages.error(request, "Invalid path")

    elif islink(cur_file):
        messages.error(request, "Cannot browse symlink")
        
    elif isdir(cur_file):
        data = [l for l in listdir(cur_file) if not l.startswith('.')]
 
    else :
        data = CodeBroRenderer(p).render(cur_file)
        
    ctx = {'project': p,
           'path': cur_file,
           'lines': data,
           'is_dir': isdir(cur_file) 
           }
    
    return render(request, 'project/detail.html', ctx)


def project_new(request):
    """
    create a new project
    """

    valid_method_or_404(request, ['GET', 'POST'])
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        
        if form.is_valid():
            ext = is_valid_file(request.FILES['file'])
            if ext!=False:
                if handle_uploaded_file(request.FILES['file'],
                                        form.cleaned_data['name'],
                                        ext) is not None :
                    return project_add(request, form)
                else :
                    form.errors['file']= ["Error while handling uploaded file"]
            else :
                form.errors['file'] = ["File is not valid"]
            
        msg = "Invalid form: "
        msg+= ','.join(["%s: %s"%(k,v[0]) for k,v in form.errors.iteritems()])
        messages.error(request, msg)
        return render(request, 'project/new.html', {'form': form})

    else : # request.method == 'GET' 
        form = ProjectForm()
        return render(request, 'project/new.html', {'form': form})

    
def project_add(request, form):
    """
    create and commit a new project (assume all checks were done before)
    """

    p = Project()
    p.name = form.cleaned_data['name']
    p.description = form.cleaned_data['description']        
    p.language = form.cleaned_data['language']
    p.added_date = timezone.now()
    p.file_number = 0
    p.function_definition_number = 0
    p.xref_number = 0
    p.full_clean()
    p.save()
        
    messages.success(request, "Successfully added")
    return redirect(reverse('browser.views.project_detail', args=(p.id, )))
   
    
def delete_all_references_to_project(project):
    for function in project.function_set.iterator():
        function.delete()



def project_draw(request, project_id):
    """
    
    """
    valid_method_or_404(request, ["GET",])
    
    project = get_object_or_404(Project, pk=project_id)

    if not is_project_xrefed(project):
        messages.error(request, "Project must be xref-ed first")
        return redirect( reverse("browser.views.project_detail", args=(project.id,)))


    if "file" not in request.GET or "function" not in request.GET:
        messages.error(request, "Missing argument")
        return redirect( reverse("browser.views.project_detail", args=(project.id,)))
    
    callers = Function.objects.filter(project=project,
                                      name=request.GET["function"],
                                      file__name=request.GET["file"])

    if callers.count() == 0:
        messages.error(request, "No function matching criterias")
        return redirect( reverse("browser.views.project_detail", args=(project.id,)))
            
    elif callers.count() > 1:
        messages.error(request, "More than one function match criterias")
        return redirect( reverse("browser.views.project_detail", args=(project.id,)))

    caller_f = callers[0]

    try :  depth = int(request.GET.get('depth', -1))
    except ValueError:  depth = -1

    xref_from = request.GET.get("xref", True)
    xref_from = False if request.GET.get('xref')=='1' else True

    base = "p%d-f%d-fu%d" % (project.id, caller_f.id, caller_f.id)
    base+= "@%d" % depth  if depth > 0 else ""

    basename = sha1(base).hexdigest() + ".svg"
    pic_name = settings.CACHE_PATH + "/" + basename 
    
    if not access(pic_name, R_OK):
        # if no file in cache, create it
        if generate_graph(pic_name, project, caller_f, xref_from, depth)==False :
            messages.error(request, "Failed to create png graph.")
            return redirect( reverse("browser.views.project_detail", args=(project.id,)))

    return redirect(reverse("browser.views.get_cache", args=(basename,)))



def get_cache(request, filename):
    fullpath = settings.CACHE_PATH + '/' + filename
    if not access(fullpath, R_OK):
        raise Http404

    with open(fullpath, 'r') as f:
        data = f.read()

    http = HttpResponse(content_type="image/svg+xml")
    http.write(data)
        
    return http

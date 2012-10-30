from browser.models import Project 
from browser.models import Language
from browser.models import File
from browser.models import Function 
from browser.models import Argument
from browser.models import Xref

from browser.forms import ProjectForm
from browser.helpers import valid_method_or_404
from browser.helpers import handle_uploaded_file, is_valid_file
from browser.helpers import clang_parse_project, is_project_parsed, is_project_xrefed

from django.http import HttpResponse
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

from hashlib import sha1

from pydot import Dot, Node, Edge, InvocationException

from xml.sax import SAXParseException 

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

        
def project_parse(request, project_id):
    """
    
    """
    valid_method_or_404(request, ['GET',])
    
    project = get_object_or_404(Project, pk=project_id)

    if is_project_parsed(project):
        messages.error(request, "Project '%s' already parsed"%project.name)
        return redirect(reverse('browser.views.project_detail', args=(project.id, )))

    clang_parse_project(request, project)
    return redirect(reverse('browser.views.project_detail', args=(project.id, )))


def project_xref(request, project_id):
    """
    
    """
    
    project = get_object_or_404(Project, pk=project_id)

    if not is_project_parsed(project):
        messages.error(request, "Project '%s' must be parsed first"%project.name)
        return redirect(reverse('browser.views.project_detail', args=(project.id, )))

    if is_project_xrefed(project):
        messages.error(request, "Project '%s' already xref-ed"%project.name)
        return redirect(reverse('browser.views.project_detail', args=(project.id, )))
      
    clang_xref_project(request, project)
            
    return redirect(reverse('browser.views.project_detail', args=(project.id, )))


def project_draw(request, project_id):
    """
    
    """
    valid_method_or_404(request, ["GET", "POST"])
    
    project = get_object_or_404(Project, pk=project_id)

    if not is_project_xrefed(project):
        messages.error(request, "Project must be xref-ed first")
        return redirect( reverse("browser.views.project_detail", args=(project.id,)))

    if request.method == "GET":
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
        
    else : # request.method == 'POST':
        try :
            for obj in serializers.deserialize("xml", request.POST.get('file')):
                data = obj
                data.save()
                break
            
            caller_f = data.object
            depth = int(request.POST.get('depth'))
            
            xref_from = request.POST.get("xref", True)
            xref_from = False if request.POST.get('xref')=='1' else True
            
        except SAXParseException:
            messages.error(request, "Failed to get function")
            return redirect( reverse("browser.views.project_detail", args=(project.id,)))

        except ValueError :
            depth = -1

    base = "p%d-f%d-fu%d" % (project.id, caller_f.id, caller_f.id)
    base+= "@%d" % depth  if depth > 0 else ""

    pic_name = settings.CACHE_PATH + "/" + sha1(base).hexdigest() + ".svg"
    
    if not access(pic_name, R_OK):
        # if no file in cache, create it
        if generate_graph(pic_name, project, caller_f, xref_from, depth)==False :
            messages.error(request, "Failed to create png graph.")
            return redirect( reverse("browser.views.project_detail", args=(project.id,)))

    f = open(pic_name)
    response = HttpResponse(mimetype="image/svg+xml")
    response.write(f.read())
    return response


def generate_graph(outfile, project, caller, xref, depth):
    """
    
    """

    title = "Callgraph"
    title+= "From" if xref==True else "To"
    title+= ": %s:%s" % (project.name, caller.name)
    
    graph = Dot(graph_type="digraph", graph_name=title,
                suppress_disconnected=False, simplify=False,)
    
    link_node(graph, project, caller, xref, depth)
    
    try :
        graph.write_svg(outfile)
        
    except InvocationException, ie:
        return False

    return True
    
        
def link_node(graph, project, caller_f, xref_from, depth):
    """
    
    """
    if depth is not None :
        if depth == 0:
            return
        else:
            depth -= 1
        
    caller_n = Node(caller_f.name)
    graph.add_node(caller_n)

    if xref_from:
        xrefs = project.xref_set.filter(project=project, calling_function=caller_f)
    else:
        xrefs = project.xref_set.filter(project=project, called_function=caller_f)
        
    for xref in xrefs :
        if xref_from:
            called_function = xref.called_function
            callee_n = Node(called_function.name)
            sub_xrefs = project.xref_set.filter(project=project, calling_function=called_function)
        else:
            called_function = xref.calling_function
            callee_n = Node(called_function.name)
            sub_xrefs = project.xref_set.filter(project=project, called_function=called_function)

        if sub_xrefs.count():
            url_to_decl = reverse('browser.views.project_detail', args=(project.id, ))
            url_to_decl+= "?file=%s" % called_function.file.name
            url_to_decl+= "#line-%d" % called_function.line
            callee_n.set_URL(url_to_decl)

            if xref_from:
                link_node(graph, project, xref.called_function, xref_from, depth)
            else:
                link_node(graph, project, xref.calling_function, xref_from, depth)
                
        graph.add_node(callee_n)
        if xref_from :
            edge = Edge(caller_n, callee_n)
        else:
            edge = Edge(callee_n, caller_n)

        # edge label
        lbl = xref.calling_function.file.name.replace(project.get_code_path()+'/', '')
        lbl+= '+'
        lbl+= str(xref.called_function_line)
        edge.set_label(lbl)

        # edge url
        url = reverse('browser.views.project_detail', args=(project.id, ))
        url+= "?file=%s" % xref.calling_function.file.name
        url+= "#line-%d" % xref.called_function_line
        edge.set_URL(url)
        
        edge.set_fontsize(8)
        
        graph.add_edge(edge)
        

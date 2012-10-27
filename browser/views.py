from browser.models import Project 
from browser.models import Language
from browser.models import File
from browser.models import Function 
from browser.models import Argument
from browser.models import Xref

from browser.forms import ProjectForm

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
from codebro.clangparse import ClangParser

from os import listdir
from os.path import abspath, isdir, islink

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

from pydot import Dot, Node, Edge, InvocationException

def index(request):
    """
    index page
    """
    ctx = {'projects': Project.objects.all().order_by('-added_date')[:4]}
    return render(request, 'index.html', ctx)


def search(request):
    """
    search engine
    """
    if "pattern" in request.POST:
        ctx = {'pattern': request.POST["pattern"]}
    else:
        ctx = {'pattern': ""}
    return render(request, "search_results.html", ctx)


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
        fd = open(cur_file, 'r')
        lexer = get_lexer_by_name("c", stripall=True)
        formatter = HtmlFormatter(linenos=True,
                                  cssclass="codebro",
                                  anchorlinenos=True,
                                  lineanchors="line")
        data = highlight(fd.read(), lexer, formatter).split('\n')
        fd.close()
        
    ctx = {'project': p,
           'path': cur_file,
           'lines': data,
           'is_dir': isdir(cur_file)
           }
    
    return render(request, 'project/detail.html', ctx)


def project_new(request):
    """
    create a new project, todo unify add/new
    """
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        
        if form.is_valid():
            return project_add(request, form)
        
        else:
            msg = "Invalid form: "
            msg+= ','.join(["%s: %s"%(k,v[0]) for k,v in form.errors.iteritems()])
            messages.error(request, msg)
            return render(request, 'project/new.html', {'form': form})

    elif request.method == 'GET' :
        form = ProjectForm()
        return render(request, 'project/new.html', {'form': form})

    else :
        messages.warning(request, "Invalid method")
        return redirect(reverse('browser.views.index'))

    
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


def is_project_parsed(project):
    return project.function_definition_number != 0 \
        and project.file_number != 0

def is_project_xrefed(project):
    return is_project_parsed(project) \
        and project.xref_number != 0

def project_parse(request, project_id):
    """
    
    """
    p = get_object_or_404(Project, pk=project_id)

    if is_project_parsed(p):
        messages.error(request, "Project '%s' already parsed"%p.name)
        return redirect(reverse('browser.views.project_detail', args=(p.id, )))

    
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
                    messages.warning(request,
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

    if request.method == "GET":
        p.save()
        messages.info(request, "Successfully parsed")  
        return redirect(reverse('browser.views.project_detail', args=(p.id, )))
    
    elif request.method == "POST":
        p.save()
        return True
    
    else :
        return False

    
def delete_all_references_to_project(project):
    for function in project.function_set.iterator():
        function.delete()

    

def project_xref(request, project_id):
    """
    
    """
    
    p = get_object_or_404(Project, pk=project_id)

    if not is_project_parsed(p):
        messages.error(request, "Project '%s' must be parsed first"%p.name)
        return redirect(reverse('browser.views.project_detail', args=(p.id, )))

    if is_project_xrefed(p):
        messages.error(request, "Project '%s' already xref-ed"%p.name)
        return redirect(reverse('browser.views.project_detail', args=(p.id, )))
      

    cparser = ClangParser()
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
        messages.success(request, "Successfully xref-ed")
    else :
        messages.error(request, "No xref have been established")
        
    return redirect(reverse('browser.views.project_detail', args=(p.id, )))


def project_draw(request, project_id):
    """
    
    """
    project = get_object_or_404(Project, pk=project_id)

    if not is_project_xrefed(project):
        messages.error(request, "Project must be xref-ed first")
        return redirect( reverse("browser.views.project_detail", args=(project.id,)))
    
    for obj in serializers.deserialize("xml", request.POST['file']):
        data = obj
        data.save()
        break
    caller_f = data.object

    xref_from = True
    if 'xref' in request.POST and request.POST['xref'] in ('0', '1'):
        xref_from = True if request.POST['xref']=='0' else False
    
    graph = Dot(graph_type='digraph',
                graph_name='Callgraph: %s:%s' % (project.name, caller_f.name),
                suppress_disconnected=False, simplify=False,)

    link_node(graph, project, caller_f, xref_from)

    try :
        response = HttpResponse(mimetype="image/svg+xml")
        response.write(graph.create_svg())
        return response
    
    except InvocationException, ie:
        messages.error(request, "Failed to create png graph. Reason: %s" % ie)
        return HttpResponse("Falafail")

    
def link_node(graph, project, caller_f, xref_from):
    """
    
    """
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
            url_to_decl = reverse('browser.views.project_detail', args=(p.id, ))
            url_to_decl+= "?file=%s" % called_function.file.name
            url_to_decl+= "#line-%d" % called_function.line
            callee_n.set_URL(url_to_decl)
            
            link_node(graph, project, xref.called_function)
            
        graph.add_node(callee_n)
        if xref_from :
            edge = Edge(caller_n, callee_n)
        else:
            edge = Edge(callee_n, caller_n)
            
        edge.set_label("%s+%d" % (xref.calling_function.file.name.replace(project.get_code_path()+'/', ''),
                                  xref.called_function_line))
        edge.set_fontsize(8)
        
        graph.add_edge(edge)
        

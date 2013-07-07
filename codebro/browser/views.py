import unipath
import hashlib 

from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.html import escape
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from browser.models import Project
from analyzer.models import File, Function, Debug
from browser.helpers import valid_method_or_404
from browser.helpers import handle_uploaded_file
from browser.helpers import is_valid_file, is_int, get_file_extension
from browser.helpers import generate_graph
from browser.forms import NewProjectForm, ProjectForm

from codebro import settings



def index(request):
    """
    index page
    """
    ctx = {'projects': Project.objects.all().order_by('-created')[:4]}
    return render(request, 'index.html', ctx)


def project_search(request, project_id):
    """
    perform search inside a specific project
    """
    project = get_object_or_404(Project, pk=project_id)
    filelist = File.objects.filter(project=project)    
    return generic_search(request, filelist)


def generic_search(request, filelist=None):
    """
    perform a search in all files
    """
    valid_method_or_404(request, ["GET"])
    if "q" not in request.GET:
        return render(request, "search.html", {"pattern": ""})

    pattern = request.GET["q"]
    if filelist is None:
        filelist = File.objects.all()
    context = File.search(pattern, filelist)
    
    return render(request, "search.html", context)


def project_list(request):
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
    content = []
    ctx = {}
    
    project = get_object_or_404(Project, pk=project_id)
    path = unipath.Path(request.GET.get('file', project.code_path)).absolute()

    if not path.startswith(project.code_path):
        messages.error(request, "Invalid path")

    elif path.islink():
        messages.error(request, "Cannot browse symlink")
        
    elif path.isdir():
         content = project.list_directory(path)

    elif path.isfile() :
        hl = [ int(i)  for i in request.GET.get('hl', '').split(",") if is_int(i) ]
        hl.sort()
        content = project.browse_file(path, hl)
        if len(hl) > 0:
            ctx['jump_to'] 	= hl[0]

        ctx["is_parsed"] = False
        refs = project.file_set.filter( name = path )
        if len(refs) > 0:
            ref = refs[0]
            ctx["is_parsed"] = ref.is_parsed 
        
    else :
        messages.error(request, "Inexistant path")
        
    ctx['project'] 		= project
    ctx['path'] 		= path
    ctx['lines'] 		= content
    ctx['is_dir']	  	= path.isdir()
    ctx['parent_dir']		= path.parent
    
    return render(request, 'project/detail.html', ctx)


def project_new(request):
    """
    create a new project
    """

    valid_method_or_404(request, ['GET', 'POST'])
    
    if request.method == 'POST':
        form = NewProjectForm(request.POST, request.FILES)
        
        if form.is_valid():
            if 'file' in request.FILES:
                file = request.FILES['file']
                 
                if is_valid_file(file):
                    ext = get_file_extension(file.name)
                    if handle_uploaded_file(file, form.cleaned_data['name'], ext) is not None :
                        form.cleaned_data['source_path'] = form.cleaned_data['name']
                        project = Project.create(form.cleaned_data)
                        if project:
                            messages.success(request, "Successfully added")
                            return redirect(reverse('browser.views.project_detail', args=(project.id, )))
                        else:
                            form.errors['project']= ["Failed to create project"]
                else :
                    form.errors['extension']= ["File extension is invalid"]
            else :
                form.errors['file']= ["Error while handling uploaded file"]
        else :
            form.errors['file'] = ["File is not valid"]
            
        msg = "Invalid form: "
        msg+= ", ".join(["'%s': %s"%(k,v[0]) for k,v in form.errors.iteritems()])
        messages.error(request, msg)
        
        return render(request, 'project/new.html', {'form': form, 'project_id': -1})

    else : # request.method == 'GET' 
        form = NewProjectForm()
        return render(request, 'project/new.html', {'form': form, 'project_id': -1})


def project_edit(request, project_id):
    """
    edit a project
    """ 
    valid_method_or_404(request, ['GET', 'POST'])
    project = get_object_or_404(Project, pk=project_id)

    if request.method == 'POST':
        name = escape(request.POST.get('name'))
        description = escape(request.POST.get('description'))

        if not name.isalnum:
            messages.error(request, "name must be alnum")
            
        elif not description.isalnum:
            messages.error(request, "description must be alnum")
            
        else :
            project.name = escape(name)
            project.description = escape(description)
            project.save()
            
        return redirect(reverse('browser.views.project_detail', args=(project.id, )))
        
    else: # request.method == 'GET' 
        form = ProjectForm(instance=project)
        return render(request, 'project/new.html', {'form': form, 'project_id': project.id})


def project_delete(request, project_id):
    """
    delete a project
    """
    
    project = get_object_or_404(Project, pk=project_id)

    if project.xref_set.count() > 0 or project.debug_set.count() > 0:
        messages.error(request, "Project '%s' must be unparsed first" % project.name)
        return redirect( reverse("browser.views.project_detail", args=(project.id,)))

    project.remove_file_instances()
    project.remove_files()
    project.delete()
    
    messages.success(request, "Project '%s' successfully deleted" % project.name)
    return redirect(reverse("browser.views.project_list"))



def project_draw(request, project_id):
    """
    
    """
    valid_method_or_404(request, ["GET",])
    
    project = get_object_or_404(Project, pk=project_id)

    if "file" not in request.GET or "function" not in request.GET:
        messages.error(request, "Missing argument")
        return redirect( reverse("browser.views.project_detail", args=(project.id,)))

    files = project.file_set.filter( name=request.GET["file"] )
    if len(files) < 1 :
        messages.error(request, "Cannot find %s in project" % request.GET["file"])
        return redirect( reverse("browser.views.project_detail", args=(project.id,)))

    if not files[0].is_parsed and not project.is_parsed:
        messages.error(request, "Project must be xref-ed first")
        return redirect( reverse("browser.views.project_detail", args=(project.id,)))
    
    callers = Function.objects.filter(project=project,
                                      name=request.GET["function"],
                                      file=files[0])

    if callers.count() == 0:
        messages.error(request, "No function matching criterias")
        return redirect( reverse("browser.views.project_detail", args=(project.id,)))
            
    elif callers.count() > 1:
        messages.error(request, "More than one function match criterias")
        return redirect( reverse("browser.views.project_detail", args=(project.id,)))

    caller_f = callers[0]

    try :
        depth = int(request.GET.get('depth', -1))
    except ValueError:
        depth = -1

    # xref_to = request.GET.get("xref", True)
    # xref_to = False if request.GET.get('xref')=='1' else True

    if request.GET.get('xref', '1')=='1':
        xref_to = True
        base = settings.CACHED_SVG_FMT % (project.id, caller_f.id, caller_f.id, "up", depth)
    else:
        xref_to = True
        base = settings.CACHED_SVG_FMT % (project.id, caller_f.id, caller_f.id, "down", depth)
        
    
    basename = hashlib.sha256(base).hexdigest() + ".svg"
    pic_name = unipath.Path(settings.CACHE_PATH + "/" + basename).absolute()

    if not pic_name.isfile():
        # if no file in cache, create it
        ret, err = generate_graph(pic_name, project, caller_f, xref_to, depth)
        if ret==False :
            messages.error(request, "Failed to create png graph: %s" % err)
            return redirect( reverse("browser.views.project_detail", args=(project.id,)))

    return redirect(reverse("browser.views.get_cache", args=(basename,)))


def project_functions(request, project_id):
    """
    
    """
    project = get_object_or_404(Project, pk=project_id)
    functions = Function.objects.filter(project=project,
                                        file__isnull=False,
                                        line__gt = 0 ).order_by('file__name')
    paginator = Paginator(functions, 50)

    page = request.GET.get('page')
    try:
        functions = paginator.page(page)
        
    except PageNotAnInteger:
        functions = paginator.page(1)
        
    except EmptyPage:
        functions = paginator.page(paginator.num_pages)
        
    ctx = {'project' : project,
           'functions': functions}
    
    
    return render(request, 'project/functions.html', ctx)


def project_analysis(request, project_id):
    """
    
    """
    project = get_object_or_404(Project, pk=project_id)

    dbgs = []
    class D:
        category = None
        filename = None
        line = None
        message = None
        link = None
        
    for d in project.debug_set.iterator():
        o = D()
        o.category = Debug.level2str(d.category)
        o.filename = d.filepath.replace(settings.SRC_PATH+'/','')
        o.line = d.line
        o.message = d.message
        o.link = reverse("browser.views.project_detail", args=(project.id,))
        o.link+= "?file=%s&hl=%d" % (d.filepath, d.line)
        dbgs.append(o)
        
    ctx = {'project' : project , 
           'dbgs' :  dbgs}
    return render(request, 'project/analysis.html', ctx)


def get_cache(request, filename):
    """
    
    """
    fullpath = unipath.Path(settings.CACHE_PATH + '/' + filename)
    if not fullpath.isfile():
        raise Http404

    with open(fullpath, 'r') as f:
        data = f.read()

    http = HttpResponse(content_type="image/svg+xml")
    http.write(data)
        
    return http


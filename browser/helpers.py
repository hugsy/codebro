from django.http import Http404
from django.core.urlresolvers import reverse

from codebro import settings

from tempfile import mkstemp
from zipfile import ZipFile, is_zipfile
from tarfile import TarFile, is_tarfile

from os import fdopen, mkdir, unlink

from pydot import Dot, Node, Edge, InvocationException


class Archive:
    ZIP_FILE = 1
    TGZ_FILE = 2
    TBZ_FILE = 3
    
    handlers = {
        ZIP_FILE : [ZipFile, ZipFile.close, ZipFile.extractall, 'r', is_zipfile],
        TGZ_FILE : [TarFile.open, TarFile.close, TarFile.extractall, 'r:gz', is_tarfile],
        TBZ_FILE : [TarFile.open, TarFile.close, TarFile.extractall, 'r:bz2', is_tarfile],
        }

    extensions = {
        ZIP_FILE : [".zip",],
        TGZ_FILE : [".tar.gz", ".tgz"], 
        TBZ_FILE : [".tar.bz2", ".tbz2"],
        }
    
    
    def __init__(self, fname, t):
        self.name = fname
        self.type = t
        self.handler = Archive.handlers[self.type]
 
    def extract(self, path):
        handle_open, handle_close, handle_extract, handle_mode, handle_check = self.handler
        if not handle_check(self.name):
            raise Exception("Invalid file type (%#x) '%s'" % (self.type, self.name))
        
        p = handle_open(self.name, handle_mode)
        handle_extract(p, path)
        handle_close(p)
        return True

    
def is_valid_file(f):
    if f.size >= settings.MAX_UPLOAD_SIZE :
        return False

    ext = None
    for i in Archive.extensions :
        for extension in Archive.extensions[i]:
            if f.name.endswith(extension) :
                ext = i
                break

    if ext is None :
        return False

    return ext


def extract_archive(archive_name, project_name, extension):
    path = "%s/%s" % (settings.SRC_PATH, project_name)
    try:
        mkdir(path, 0755)
    except OSError:
        unlink(archive_name)
        return None
    
    archive = Archive(archive_name, extension)
    archive.extract(path)

    unlink(archive_name)
    return path


def handle_uploaded_file(file_o, project_name, extension):
    fd, fname = mkstemp(prefix="codebro_tmp")

    with fdopen(fd, 'w') as f:
        for chunk in file_o.chunks():
            f.write(chunk)

    return extract_archive(fname, project_name, extension)


def valid_method_or_404(request, methods):
    if not request.method in methods:
        raise Http404


def is_project_parsed(project):
    return project.function_definition_number != 0 \
        and project.file_number != 0

def is_project_xrefed(project):
    return is_project_parsed(project) \
        and project.xref_number != 0


    
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
        

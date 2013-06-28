import tempfile 
import zipfile
import tarfile 
import unipath
import os
import pydot

from django.http import Http404
from django.core.urlresolvers import reverse

from codebro import settings


class Archive:
    ZIP_FILE = 1
    TGZ_FILE = 2
    TBZ_FILE = 3
    
    handlers = {
        ZIP_FILE : [zipfile.ZipFile, zipfile.ZipFile.close, zipfile.ZipFile.extractall, 'r', zipfile.is_zipfile],
        TGZ_FILE : [tarfile.TarFile.open, tarfile.TarFile.close, tarfile.TarFile.extractall, 'r:gz',  tarfile.is_tarfile],
        TBZ_FILE : [tarfile.TarFile.open, tarfile.TarFile.close, tarfile.TarFile.extractall, 'r:bz2', tarfile.is_tarfile],
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
        if handle_check(self.name) == False:
            raise Exception("Invalid file type %#x '%s'" % (self.type, self.name))
        
        p = handle_open(self.name, handle_mode)
        handle_extract(p, path)
        handle_close(p)
        return True

    
def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

    
def get_file_extension(name):
    for ext in Archive.extensions :
        for suffix in Archive.extensions[ext]:
            if name.endswith(suffix) :
                return ext

    return None


def is_valid_file(f):
    return (f.size < settings.MAX_UPLOAD_SIZE) and (get_file_extension(f.name) is not None)


def extract_archive(archive_name, project_name, extension):
    try:
        path = unipath.Path( '/'.join([settings.SRC_PATH, project_name]) )
        path.mkdir(mode=0755)
        
    except OSError:
        unlink(archive_name)
        return None
    
    archive = Archive(archive_name, extension)
    archive.extract(path)

    os.unlink(archive_name)
    return path


def handle_uploaded_file(file_o, project_name, extension):
    fd, fname = tempfile.mkstemp(prefix="codebro_tmp")

    with os.fdopen(fd, 'w') as f:
        for chunk in file_o.chunks():
            f.write(chunk)

    return extract_archive(fname, project_name, extension)


def valid_method_or_404(request, methods):
    if not request.method in methods:
        raise Http404

    
def generate_graph(outfile, project, caller, xref, depth):
    """
    
    """

    title = "Callgraph"
    title+= "To" if xref==True else "From"
    title+= ": %s:%s" % (project.name, caller.name)
    
    graph = pydot.Dot(graph_type="graph", graph_name=title,
                      suppress_disconnected=False, simplify=False,)
    
    link_node(graph, project, caller, xref, depth)
    
    try :
        graph.write_svg(outfile)
        
    except pydot.InvocationException, ie:
        return (False, ie)

    return (True, None)
    
        
def link_node(graph, project, caller_f, xref_from, depth):
    """
    
    """
    if depth is not None :
        if depth == 0:
            return
        else:
            depth -= 1
        
    caller_n = pydot.Node(caller_f.name)
    graph.add_node(caller_n)

    if xref_from:
        xrefs = project.xref_set.filter(project=project, calling_function=caller_f)
    else:
        xrefs = project.xref_set.filter(project=project, called_function=caller_f)
        
    for xref in xrefs :
        if xref_from:
            called_function = xref.called_function
            callee_n = pydot.Node(called_function.name)
            sub_xrefs = project.xref_set.filter(project=project, calling_function=called_function)
        else:
            called_function = xref.calling_function
            callee_n = pydot.Node(called_function.name)
            sub_xrefs = project.xref_set.filter(project=project, called_function=called_function)

        if sub_xrefs.count():
            url_to_decl = reverse('browser.views.project_detail', args=(project.id, ))
            args = "?file=%s&hl=%d"
            args%= (called_function.file.name, called_function.line)
            callee_n.set_URL(url_to_decl)

            if xref_from:
                link_node(graph, project, xref.called_function, xref_from, depth)
            else:
                link_node(graph, project, xref.calling_function, xref_from, depth)
                
        graph.add_node(callee_n)
        if xref_from :
            edge = pydot.Edge(caller_n, callee_n)
        else:
            edge = pydot.Edge(callee_n, caller_n)

        # edge label
        lbl = xref.calling_function.file.name.replace(project.code_path+'/', '')
        lbl+= '+'
        lbl+= str(xref.called_function_line)
        edge.set_label(lbl)

        # edge url
        url = reverse('browser.views.project_detail', args=(project.id, ))
        args = "?file=%s&hl=%s"
        args%= (xref.calling_function.file.name, xref.called_function_line)
        edge.set_URL(url + args)
        
        edge.set_fontsize(8)
        
        graph.add_edge(edge)
        

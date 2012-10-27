from django.http import Http404

from codebro import settings
from tempfile import mkstemp
from time import time
from zipfile import ZipFile, is_zipfile
from tarfile import TarFile, is_tarfile
from codebro import settings

from os import fdopen, mkdir, unlink


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
    fd, fname = mkstemp()

    with fdopen(fd, 'w') as f:
        for chunk in file_o.chunks():
            f.write(chunk)

    return extract_archive(fname, project_name, extension)


def valid_method_or_404(request, methods):
    if not request.method in methods:
        raise Http404


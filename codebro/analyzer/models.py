import clang.cindex
import re

from django.db import models

from browser.validators import validate_PathNotEmpty
from browser.models import Project
from codebro.settings import SRC_PATH


class File(models.Model):
    """

    """
    name		 	= models.CharField(max_length = 1024,
                                       validators = [validate_PathNotEmpty])
    project 		= models.ForeignKey(Project)
    is_parsed		= models.BooleanField(default = False)
    
    
    def __unicode__(self):
        return self.name

    @property
    def relative_name(self):
        return self.name.replace(SRC_PATH+"/", "")
    
    def grep(self, pattern):
        """
        shitty under-optimized grep function : search a pattern inside a file
        """
        blocks = []

        with open(self.name, 'r') as fd :
        
            line_num = 1
            for line in fd.xreadlines():
                match = pattern.search(line)
                if match is not None:
                    blocks.append([line_num, match.string])
                line_num += 1

        return blocks

    
    @staticmethod
    def search(pattern, files, project=None):
        """
        search engine
        """

        blocks = {}
        compiled_pattern = re.compile(pattern, re.IGNORECASE)
        
        for file in files :
            ret = file.grep(compiled_pattern)
            if len(ret) > 0:
                if file.project not in blocks:
                    blocks[file.project] = {}
                    
                if file not in blocks[file.project]:
                    blocks[file.project][file] = {}
                blocks[file.project][file].update(ret) 

        total = 0
    
        for project in blocks.keys():
            for e in blocks[project].keys():
                total += len(blocks[project][e])
            
        ctx = {}
        ctx["pattern"] = pattern
        ctx["num_matches"] = total
        ctx["blocks"] = blocks

        if project is not None:
            ctx['project'] = project
        
        return ctx


class Function(models.Model):
    """

    """
    name 			= models.CharField(max_length=1024,
                                                   validators=[validate_PathNotEmpty])
    project 		= models.ForeignKey(Project)
    file 			= models.ForeignKey(File, null=True)
    line 			= models.PositiveIntegerField(null=True, default=0)
    rtype 			= models.CharField(max_length=16, null=True)
    
    def __unicode__(self):
        return "%s:%d - <%s> %s (%s)" % (self.file, self.line if self.line is not None else 0, self.rtype,
                                         self.name, self.args)

    @property
    def args(self):
        args = self.argument_set.iterator()
        return ', '.join([x.__unicode__() for x in args])

    
class Argument(models.Model):
    """

    """
    name 			= models.CharField(max_length=32)
    type 			= models.CharField(max_length=16)
    function 		= models.ForeignKey(Function)
    
    def __unicode__(self):
        return "<%s> %s" % (self.name, self.type)

        
class Xref(models.Model):
    """

    """
    project 				= models.ForeignKey(Project)
    calling_function 		= models.ForeignKey(Function, related_name='caller')
    called_function 		= models.ForeignKey(Function, related_name='callee')
    called_function_line 	= models.PositiveIntegerField()
    
    def __unicode__(self):
        return "%s -> %s (l.%d)" % (self.calling_function.name,
                                    self.called_function.name,
                                    self.called_function_line if self.called_function_line is not None else 0)

    

class Diagnostic(models.Model):
    """

    """
    filepath 	= models.CharField(max_length=1024)
    line 		= models.PositiveIntegerField()
    message 	= models.TextField()

    class Meta:
        abstract = True
        

class Debug(Diagnostic):
    """

    """
    DIAG_LEVELS = (
        (clang.cindex.Diagnostic.Ignored,  "IGNORED"),
        (clang.cindex.Diagnostic.Note,     "NOTE"),
        (clang.cindex.Diagnostic.Warning,  "WARNING"),
        (clang.cindex.Diagnostic.Error,    "ERROR"),
        (clang.cindex.Diagnostic.Fatal,    "FATAL"),
        )
    
    project 	= models.ForeignKey(Project)
    category 	= models.PositiveIntegerField(choices=DIAG_LEVELS,
                                              default=clang.cindex.Diagnostic.Note)

    
    @staticmethod
    def level2str(level):
        d = dict(Debug.DIAG_LEVELS)
        try:
            return d[level]
        except KeyError:
            return ""

        
    def __unicode__(self):
        return "[%d] %s:%s - %s" % (self.category, self.project.name,
                                    self.filepath, self.message)

    

class Module(models.Model):
    """

    """
    name 		= models.CharField(max_length=64)
    project 	= models.ForeignKey(Project)
    

        
class ModuleDiagnostic(Diagnostic):
    """

    """
    module 		= models.ForeignKey(Module)
    
    def __unicode__(self):
        return "[%d] %s:%s - %s" % (self.name, self.module.project.name,
                                    self.filepath, self.message)


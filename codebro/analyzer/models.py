import clang.cindex

from django.db import models

from browser.validators import validate_PathNotEmpty
from browser.models import Project


class File(models.Model):
    """

    """
    name		 	= models.CharField(max_length = 1024,
                                       validators = [validate_PathNotEmpty])
    project 		= models.ForeignKey(Project)

    def __unicode__(self):
        return self.name
    

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
    # uid  		= models.PositiveIntegerField()
    name 		= models.CharField(max_length=64)
    project 	= models.ForeignKey(Project)
    

        
class ModuleDiagnostic(Diagnostic):
    """

    """
    module 		= models.ForeignKey(Module)
    
    def __unicode__(self):
        return "[%d] %s:%s - %s" % (self.name, self.module.project.name,
                                    self.filepath, self.message)


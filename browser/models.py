from django.db import models
from django.core.exceptions import ValidationError

from codebro import settings

from os import path


def validate_not_empty(value):
    if len(value.strip()) == 0:
        raise ValidationError(u'String must not be empty')

def validate_path(value):
    abspath = path.abspath(value)
    if not abspath.startswith(settings.SRC_PATH) or not path.isdir(abspath):
        raise ValidationError(u'Invalid path for source code')

    
class Language(models.Model):
    name = models.CharField(max_length=64, validators=[validate_not_empty])
    extension = models.CharField(max_length=10)
    
    def __unicode__(self):
        return "%s (%s)" % (self.name, self.extension)


    
class Project(models.Model):
    name = models.CharField(max_length=64, unique=True, validators=[validate_not_empty])
    description = models.TextField(max_length=255)
    language = models.ForeignKey(Language)
    added_date = models.DateTimeField()
    file_number = models.PositiveIntegerField()
    function_definition_number = models.PositiveIntegerField()
    xref_number = models.PositiveIntegerField()
    
    def __unicode__(self):
        return self.name    

    def get_code_path(self):
        return path.abspath(settings.SRC_PATH + "/" + self.name)
    
class File(models.Model):
    name = models.CharField(max_length=1024, validators=[validate_not_empty])
    project = models.ForeignKey(Project)

    def __unicode__(self):
        return self.name
    

class Function(models.Model):
    name = models.CharField(max_length=1024, validators=[validate_not_empty])
    project = models.ForeignKey(Project)
    file = models.ForeignKey(File, null=True)
    line = models.PositiveIntegerField(null=True)
    rtype = models.CharField(max_length=16, null=True)
    
    def __unicode__(self):
        return "%s:%d - <%s> %s (%s)" % (self.file, self.line, self.rtype,
                                         self.name, self.get_arguments())
    
    def get_arguments(self):
        args = self.argument_set.iterator()
        return ', '.join([x.__unicode__() for x in args])

    
class Argument(models.Model):
    name = models.CharField(max_length=32)
    type = models.CharField(max_length=16)
    function = models.ForeignKey(Function)
    
    def __unicode__(self):
        return "<%s> %s" % (self.name, self.type)

    
class Xref(models.Model):
    project = models.ForeignKey(Project)
    calling_function = models.ForeignKey(Function, related_name='caller')
    called_function = models.ForeignKey(Function, related_name='callee')
    called_function_line = models.PositiveIntegerField()
    
    def __unicode__(self):
        return "%s -> %s (%d)" % (self.calling_function.name,
                                  self.function_called,
                                  self.function_called_line)

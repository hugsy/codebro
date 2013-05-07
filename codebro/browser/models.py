from django.db import models

from codebro import settings
from browser.validators import validate_IsValidName, validate_PathNotEmpty


class TimeStampedModel(models.Model):
    """
    
    """
    created			= models.DateTimeField(auto_now_add = True)
    modified 		= models.DateTimeField(auto_now = True)
    
    class Meta:
        abstract = True
        

class Language(models.Model):
    """

    """
    name 			= models.CharField(max_length=64)
    extension 		= models.CharField(max_length=10)
    
    def __unicode__(self):
        return "%s (%s)" % (self.name, self.extension)

    
class Project(TimeStampedModel):
    """

    """
    name 			= models.CharField(max_length = 64,
                                       unique = True,
                                       validators = [validate_IsValidName])
    description 	= models.TextField(max_length = 256)
    language 		= models.ForeignKey(Language)
    source_path		= models.TextField(max_length = 256)
    is_parsed 		= models.BooleanField(default = False)
        
    @property
    def code_path(self):
        return settings.SRC_PATH + "/" + self.source_path

    def __unicode__(self):
        return "%s (%s) : %s" % (self.name, self.language.name, self.code_path)


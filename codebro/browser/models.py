import unipath

from django.db import models
from django.db import transaction

from codebro import settings
from browser.validators import validate_IsValidName


class TimeStampedModel(models.Model):
    """
    
    """
    created		= models.DateTimeField(auto_now_add = True)
    modified 		= models.DateTimeField(auto_now = True)
    
    class Meta:
        abstract = True
        

class Language(models.Model):
    """

    """
    name 		= models.CharField(max_length=64)
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


    @staticmethod
    def create(values):
        project = Project()
        if project is None:
            return None

        for item in values.keys():
            setattr(project, item, values[item])
            
        project.full_clean()
        project.save()

        project.insert_files()
        
        return project
    

    def enumerate_files(self, extensions=[]):
        """
        enumerates all files in project path that match specified extensions
        if extensions is empty, then it matches all extensions
        """
        for path in unipath.Path(self.code_path).absolute().walk(filter=unipath.FILES_NO_LINKS):
            if (len(extensions)==0) or (path.ext in extensions):
                yield path
            

    @transaction.commit_manually
    def insert_files(self):
        """
        create all files objects in database
        """
        from analyzer.models import File

        try :
            for filename in self.enumerate_files( [self.language.extension, ".h"] ):
                ref, created = File.objects.get_or_create(name=filename, project=self)
                if created:
                    ref.save()
                    
        except Exception, e:
            if settings.DEBUG:
                print "An exception occured", e
            transaction.rollback()
            
        else:
            transaction.commit()
            
        return
    
    
    def list_directory(self, dir):
        subdirs = []
        files= []

        def arrange(e):
            relname = e.absolute().replace(settings.SRC_PATH+"/", "")
            
            if e.isfile():
                files.append((relname, e.absolute()))
            elif e.isdir:
                subdirs.append(("[d] " + relname + "/", e.absolute()))

        map(arrange, dir.listdir())
        
        subdirs.sort()
        files.sort()

        res = [("..", dir.parent.absolute()),]
        res+= subdirs
        res+= files
        return res

    
    def browse_file(self, filepath, highlight_lines=[]):
        from analyzer.renderer import CodeBroRenderer
        
        renderer = CodeBroRenderer(self, highlight_lines)
        return renderer.render(filepath)


    @transaction.commit_manually
    def remove_file_instances(self):
        try:
            self.file_set.all().delete()
                
        except Exception, e:
            if settings.DEBUG:
                print "An exception occured", e
            transaction.rollback()
            
        else:
            transaction.commit()
            
        return
    
            
    def remove_files(self):
        path = unipath.Path(self.code_path)
        path.rmtree(parents=False)
        return
        
        

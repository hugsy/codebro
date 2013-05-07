from django.forms import ModelForm
from django.forms import Textarea
from django.forms import FileField

from browser.models import Language
from browser.models import Project

class LanguageForm(ModelForm):
    class Meta:
        model = Language
    
class ProjectForm(ModelForm):
    
    class Meta:
        model = Project
        
        exclude = ("added_date",
                   "code_path",
                   "is_parsed"
                   )
        
        widgets = {
            "description": Textarea(attrs={"rows": 3}),
        }
    
class NewProjectForm(ProjectForm):
    file = FileField(required=False)

from django.forms import ModelForm
from django.forms import Textarea
from django.forms import FileField

from browser.models import Language
from browser.models import Project

class LanguageForm(ModelForm):
    class Meta:
        model = Language
    
class ProjectForm(ModelForm):
    file = FileField()
    
    class Meta:
        model = Project
        exclude = ("added_date",
                   "file_number",
                   "function_definition_number",
                   "xref_number")
        widgets = {
            "description": Textarea(attrs={"rows": 3}),
        }
    

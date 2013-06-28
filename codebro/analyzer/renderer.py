from django.core.urlresolvers import reverse
from django.utils.html import escape

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.formatters.html import _escape_html_table

from .models import File


class CodeBroHtmlFormatter(HtmlFormatter):
    """
        
    """
    
    def __init__(self, **options):
        """
        
        """
        HtmlFormatter.__init__(self, **options)
        self.project = options['codebro_project']
        self.is_xrefed = False
        self.file = None
        self.functions = []
        self.func_idx = 0
        
        
    def _wrap_lineanchors(self, inner):
        """
        
        """        
        s = self.lineanchors
        i = self.linenostart - 1
        for t, line in inner:
            if t:
                i += 1
                # shifting down 75px coz of header
                yield 1, '<a name="%s-%d" style="position:relative; top:-75px;"></a>' % (s, i) + line
                
            else:
                yield 0, line
    

    def set_filename(self, name):
        """
        
        """
        try :
            self.file = File.objects.get(name=name, project=self.project)
            self.is_xrefed = self.file.is_parsed
            
        except File.DoesNotExist:
            self.functions = []
            self.func_idx = 0
            self.file = None
            return
        
        self.functions = []
        self.func_idx = 0
        
        for f in self.file.function_set.iterator():
            self.functions.append(f)

        
    def is_called_function(self, funcname):
        """
        
        """
        for f in self.functions:
            if f.name == funcname :
                return True
            
        return False


    def get_called_function(self, funcname):
        """
        
        """
        for f in self.functions:
            if f.name == funcname :
                return f
            
        return None
    

    def insert_function_ref(self, funcname, cls, style, depth=1):
        """
        
        """
        self.func_idx += 1
        fmt_str = "?function={0}&file={1}&depth={2}"
        args = [ escape(x) for x in [funcname, self.file.name, depth] ]
        url_to_graph = reverse("browser.views.project_draw", args=(self.project.id,))
        url_to_graph+= fmt_str.format( *args )

        url_to_definition = ""
        f = self.get_called_function(funcname)
        if f is not None and (f.file is not None and f.line != 0):
            fmt_str = "?file={0}&hl={1}"
            args = [ escape(x) for x in [f.file.name, f.line] ]
            url_to_definition = reverse("browser.views.project_detail", args=(self.project.id,))
            url_to_definition+= fmt_str.format( *args )
            
        link = '<span class="%s" ' % cls
        link+= 'style="%s" ' % style
        link+= 'id="func-%s-%d" ' % (escape(funcname), self.func_idx)
        link+= 'onclick="function_menu(this.id, [\''+url_to_graph+'\', \''+url_to_definition+'\']); return false;" '
        link+= '>'
        return link
    
     
    def insert_calling_function_ref(self, funcname, cls):
        """
        
        """
        return self.insert_function_ref(funcname, cls, style="border: 1px solid blue")


    def insert_called_function_ref(self, funcname, cls):
        """
        
        """
        return self.insert_function_ref(funcname, cls, style="border: 1px dotted black")
    
    
    def _format_lines(self, tokensource):
        """
        
        """        
        nocls = self.noclasses
        lsep = self.lineseparator
        getcls = self.ttype2class.get
        c2s = self.class2style
        escape_table = _escape_html_table

        lspan = ''
        line = ''
        for ttype, value in tokensource:
            if nocls:
                cclass = getcls(ttype)
                while cclass is None:
                    ttype = ttype.parent
                    cclass = getcls(ttype)
                cspan = cclass and '<span style="%s">' % c2s[cclass][0] or ''
                
            else:
                cls = self._get_css_class(ttype)
                
                if cls=='nf' and self.is_xrefed and self.file is not None :
                    link = self.insert_calling_function_ref(value, cls)
                    cspan = cls and link or ''
                    
                elif cls=='n' and self.is_xrefed and self.is_called_function(value):
                    link = self.insert_called_function_ref(value, cls)
                    cspan = cls and link or ''
                   
                else:
                    cspan = cls and '<span class="%s">' % cls or ''
                    
            parts = value.translate(escape_table)
            parts = parts.split('\n')

            
            for part in parts[:-1]:             
                if line:
                    if lspan != cspan:
                        line += (lspan and '</span>') + cspan + part + \
                                (cspan and '</span>') + lsep
                        
                    else:
                        line += part + (lspan and '</span>') + lsep

                    yield 1, line
                    line = ''
                    
                elif part:
                    
                    yield 1, cspan + part + (cspan and '</span>') + lsep
                    
                else:
                    yield 1, lsep

            if line and parts[-1]:
                if lspan != cspan:
                    line += (lspan and '</span>') + cspan + parts[-1]
                    lspan = cspan
                else:
                    line += parts[-1]
            elif parts[-1]:
                line = cspan + parts[-1]
                lspan = cspan

        if line:
            yield 1, line + (lspan and '</span>') + lsep


class CodeBroRenderer:
    """
        
    """
    
    def __init__(self, codebro_project, highlight_lines = []):
        """
        
        """
        self.lexer = get_lexer_by_name("c", stripall=True)
        self.formatter = None
        self.project = codebro_project
        self.hl = highlight_lines

        
    def render(self, filename):
        self.formatter = CodeBroHtmlFormatter(linenos="inline",
                                              cssclass="codebro",
                                              anchorlinenos=True,
                                              lineanchors="line",
                                              codebro_project=self.project,
                                              hl_lines=self.hl)
        self.formatter.set_filename(filename)
        
        with open(filename, 'r') as f :
            data = highlight(f.read(), self.lexer, self.formatter)

        return data.split('\n')

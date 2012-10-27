from django.core.urlresolvers import reverse

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.formatters.html import _escape_html_table

from browser.helpers import is_project_xrefed

class CodeBroHtmlFormatter(HtmlFormatter):

    def __init__(self, **options):
        HtmlFormatter.__init__(self, **options)
        self.project = options['codebro_project']
        self.is_xrefed = is_project_xrefed(self.project)
        
    def _wrap_lineanchors(self, inner):
        s = self.lineanchors
        i = self.linenostart - 1
        for t, line in inner:
            if t:
                i += 1
                # shifting down 75px coz of header
                yield 1, '<a name="%s-%d" style="position:relative; top:-75px;"></a>' % (s, i) + line
                
            else:
                yield 0, line


    def _format_lines(self, tokensource):
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
                if cls=='nf' and self.is_xrefed:
                    url = reverse("browser.views.project_draw", args=(self.project.id,))
                    link = '<span class="'+cls+'"'
                    link+= 'style="border: 1px solid blue" '
                    link+= 'onclick="window.location=\''+url+'\';">'
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

    def __init__(self, codebro_project):
        self.lexer = get_lexer_by_name("c", stripall=True)
        self.formatter = CodeBroHtmlFormatter(linenos=True,
                                              cssclass="codebro",
                                              anchorlinenos=True,
                                              lineanchors="line",
                                              codebro_project=codebro_project)

    def render(self, filename):
        
        with open(filename, 'r') as f :
            data = highlight(f.read(), self.lexer, self.formatter)

        return data.split('\n')

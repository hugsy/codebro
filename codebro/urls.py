from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

# from django.contrib import admin
# admin.autodiscover()

from dajaxice.core import dajaxice_autodiscover, dajaxice_config
dajaxice_autodiscover()

urlpatterns = patterns('browser.views',
                       url(r'^[/]*$', 'index'),
                       url(r'^search/$', 'search'),
                       url(r'^about[/]?$', TemplateView.as_view(template_name="about.html"), name='about',),
                       url(r'^projects/list$', 'list'),                      
                       url(r'^projects/new$', 'project_new'),

                       url(r'^projects/(?P<project_id>\d+)/?$',          'project_detail'),
                       url(r'^projects/(?P<project_id>\d+)/edit$',      'project_edit'),
                       url(r'^projects/(?P<project_id>\d+)/delete$',    'project_delete'),
                       url(r'^projects/(?P<project_id>\d+)/draw$',      'project_draw'),
                       url(r'^projects/(?P<project_id>\d+)/functions$', 'project_functions'),
                       url(r'^projects/(?P<project_id>\d+)/analysis$',  'project_analysis'),
                       
                       url(r'^cache/(?P<filename>.+)$', 'get_cache'),
                           
                       url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),
                       )

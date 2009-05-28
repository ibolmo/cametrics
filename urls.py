from django.conf.urls.defaults import *
from ragendja.urlsauto import urlpatterns
from ragendja.auth.urls import urlpatterns as auth_patterns

handler500 = 'ragendja.views.server_error'

urlpatterns = auth_patterns + patterns('',
    
    (r'^about/?$', 'django.views.generic.simple.direct_to_template', {'template': 'about.html'}),
    (r'^$', 'django.views.generic.simple.direct_to_template', {'template': 'main.html'}, 'main'),
    
) + urlpatterns

from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^login/?', 'django.contrib.auth.views.login', {'template_name': 'user_create_form.html'}),
    (r'^logout/?$', 'django.contrib.auth.views.logout_then_login', {'login_url': '/'}),
    (r'^about/?$', 'django.views.generic.simple.direct_to_template', {'template': 'about.html'}),
) + patterns('myapp.views',
    (r'^create_admin_user/?$', 'create_admin_user'),
    (r'^register/?$', 'create_new_user'),
        
    (r'^campaign/?$', 'list_campaigns'),
    (r'^campaign/create/?$', 'add_campaign'),
    (r'^campaign/show/(?P<key>.+)$', 'show_campaign'),
    (r'^campaign/edit/(?P<key>.+)$', 'edit_campaign'),

    (r'^$', 'list_measurements'),
    (r'^(?P<key>([^/]+))/(?P<path>([^\.]+))(?:\.(?P<format>(.+)))?$', 'measurements')
)
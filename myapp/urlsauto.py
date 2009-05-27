from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^about/?$', 'django.views.generic.simple.direct_to_template', {'template': 'about.html'}),
) + patterns('myapp.views',
    (r'^tasks/clean_up_campaigns/?', 'clean_up_campaigns'),

    (r'^create_admin_user/?$', 'create_admin_user'),
    (r'^register/?$', 'create_new_user'),
        
    (r'^campaign/?$', 'list_campaigns'),
    (r'^campaign/create/?$', 'add_campaign'),
    (r'^campaign/show/(?P<key>.+)$', 'show_campaign'),
    (r'^campaign/edit/(?P<key>.+)$', 'edit_campaign'),
    (r'^campaign/delete/(?P<key>.+)$', 'delete_campaign'),

    (r'^$', 'list_measurements'),
)
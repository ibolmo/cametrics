from django.conf.urls.defaults import *

urlpatterns = patterns('myapp.views',
    (r'^tasks/clean_up_campaigns/?', 'clean_up_campaigns'),
        
    (r'^campaign/?$', 'list_campaigns'),
    (r'^campaign/create/?$', 'add_campaign'),
    (r'^campaign/show/(?P<key>.+)$', 'show_campaign'),
    (r'^campaign/edit/(?P<key>.+)$', 'edit_campaign'),
    (r'^campaign/delete/(?P<key>.+)$', 'delete_campaign'),
)
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^login/?$', 'django.contrib.auth.views.login', {'template_name': 'user_create_form.html'}),
    (r'^logout/?$', 'django.contrib.auth.views.logout_then_login', {'login_url': '/login'}),
) + patterns('myapp.views',
    (r'^create_admin_user/?$', 'create_admin_user'),
    (r'^register/?$', 'create_new_user'),
    (r'^$', 'list_measurements'),
    (r'^about/?', 'about'),
    (r'^(?P<key>([^/]+))/(?P<path>(.*))$', 'measurements')
)
# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('myapp.views',
    (r'^create_admin_user$', 'create_admin_user'),
    (r'^$', 'list_measurements'),
    (r'^(?P<key>([^/]+))/(?P<path>(.*))', 'measurements')
)

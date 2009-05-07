# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.models import User
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import ugettext_lazy as _, ugettext as __
#from myapp.models import Person, File, Contract
from ragendja.auth.models import UserTraits
from ragendja.forms import FormWithSets, FormSetField
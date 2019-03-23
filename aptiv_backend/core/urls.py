from django.conf.urls import url
from django.http import HttpResponseRedirect

from aptiv_backend.core.views import aptiv_validate

urlpatterns = [
    url(r'^$', lambda r: HttpResponseRedirect('aptiv-validate')), # Redirects home page to core app
    url(r'^aptiv-validate$', aptiv_validate, name='aptiv_validate'),
]

from django.conf.urls import patterns, include, url

from django.contrib import admin
from django.contrib.auth.views import login, logout
admin.autodiscover()
from django.conf.urls.i18n import i18n_patterns

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'stacksync_manager.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^admin/', include(admin.site.urls)),
)


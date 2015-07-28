from django.contrib import admin
from django.core.urlresolvers import reverse
from oauth.models import Consumer, RequestToken, AccessToken, Nonce


class RequestTokenAdmin(admin.ModelAdmin):
    list_display = ('request_token', 'request_token_secret', 'verifier')
    search_fields = ['user__email', 'consumer__consumer_key']


class RequestTokenInLine(admin.TabularInline):
    model = RequestToken
    extra = 0


class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'access_token', 'access_token_secret', 'modified_at')
    list_filter = ['modified_at']
    search_fields = ['user__email', 'consumer__consumer_key']


class AccessTokenInLine(admin.TabularInline):
    model = AccessToken
    extra = 0
    fields = ('consumer','access_token', 'access_token_secret')


class NonceAdmin(admin.ModelAdmin):
    list_display = ('consumer_key','nonce', 'timestamp')
    search_fields = ['consumer_key', 'token']


class ConsumerAdmin(admin.ModelAdmin):
    list_display = ('user', 'consumer_key', 'consumer_secret')
    search_fields = ['user__email', 'consumer_key']
    inlines = [RequestTokenInLine, AccessTokenInLine]


class ConsumerInLine(admin.TabularInline):
    model = Consumer
    extra = 0
    fields = ('consumer_key', 'consumer_secret')

#Comented lines are unnecessary to super-admin use
#admin.site.register(Consumer, ConsumerAdmin)
#admin.site.register(RequestToken, RequestTokenAdmin)
admin.site.register(AccessToken, AccessTokenAdmin)
#admin.site.register(Nonce, NonceAdmin)

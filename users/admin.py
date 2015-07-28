from django.contrib import admin
from oauth.admin import ConsumerInLine, RequestTokenInLine, AccessTokenInLine
from users.forms import StacksyncUserForm
from users.models import StacksyncUser, StacksyncWorkspace, StacksyncMembership
from django.utils.translation import ugettext_lazy as _

class StacksyncMembershipInline(admin.StackedInline):
    model = StacksyncMembership
    fields = ['name']
    extra = 1


class StacksyncWorkspaceAdmin(admin.ModelAdmin):
    inlines = [StacksyncMembershipInline]


class StacksyncUserAdmin(admin.ModelAdmin):
    inlines = [ConsumerInLine, RequestTokenInLine, AccessTokenInLine]
    form = StacksyncUserForm
    fields = ['name', 'email', 'password']
    list_display = ('name', 'email', 'swift_user', 'swift_account', 'quota_limit', 'quota_used_logical', 'quota_used_real')
    search_fields = ['name', 'email', 'swift_user', 'swift_account']
    actions = ['custom_delete']

    def get_actions(self, request):
        actions = super(StacksyncUserAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def custom_delete(self, request, queryset):
            for user in queryset:
                user.delete()
    custom_delete.short_description = _("Delete selected stacksync users")

    def save_model(self, request, obj, form, change):
        if form.cleaned_data['password']:
            obj.save(password=form.cleaned_data['password'])
        else:
            obj.save()

#super-administrator doesn't needs this information
#admin.site.register(StacksyncUser, StacksyncUserAdmin)
#admin.site.register(StacksyncWorkspace, StacksyncWorkspaceAdmin)

from django.contrib import admin
from users.models import StacksyncUser, StacksyncWorkspace, StacksyncMembership

class StacksyncMembershipInline(admin.StackedInline):
    model = StacksyncMembership
    fields = ['name']
    extra = 1

class StacksyncWorkspaceAdmin(admin.ModelAdmin):
    inlines = [StacksyncMembershipInline]

class StacksyncUserAdmin(admin.ModelAdmin):
    #inlines = [StacksyncMembershipInline]
    fields = ['name', 'email']
    list_display = ('name', 'email', 'swift_user')

admin.site.register(StacksyncUser, StacksyncUserAdmin)
admin.site.register(StacksyncWorkspace, StacksyncWorkspaceAdmin)

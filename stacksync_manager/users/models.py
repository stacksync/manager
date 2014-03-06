from django.db import models
from keystoneclient.v2_0 import client
from swiftclient import client as swift
from django.conf import settings
import uuid

def prefix():
    return str(uuid.uuid4()).split('-')[0]

class StacksyncUser(models.Model):

    name = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    swift_user = models.CharField(max_length=200)
    swift_account = models.CharField(max_length=200)
    quota_limit = models.IntegerField(default=0)
    quota_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = settings.USER_TABLE
         
    def __init__(self, *args, **kwargs):
        self.keystone = client.Client(username=settings.KEYSTONE_ADMIN_USER, password=settings.KEYSTONE_ADMIN_PASSWORD, tenant_name=settings.KEYSTONE_TENANT, auth_url=settings.KEYSTONE_AUTH_URL)
        tenants = self.keystone.tenants.list()
        self.stacksync_tenant = [x for x in tenants if x.name==settings.KEYSTONE_TENANT][0]
        super(StacksyncUser, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        
        keystone_password = 'testpass'
        keystone_username = settings.KEYSTONE_TENANT + '_' + prefix() + '_' + self.name
        
        keystone_user = self.keystone.users.create(name=keystone_username, password=keystone_password, tenant_id=self.stacksync_tenant.id)

        self.swift_account = 'AUTH_' + self.stacksync_tenant.id
        self.swift_user = keystone_username
        
        super(StacksyncUser, self).save(*args, **kwargs)
        
        workspace = StacksyncWorkspace(name='default')
        workspace.swift_container = settings.KEYSTONE_TENANT + '_' + prefix() + '_' + self.name
        workspace.swift_url = settings.SWIFT_URL + '/' + self.swift_account
        workspace.is_shared = False
        
        # creates the container in swift with read and write permissions
        user_and_tenant = settings.KEYSTONE_TENANT + ':' + keystone_username
        headers = {'x-container-read': user_and_tenant, 'x-container-write': user_and_tenant}
        swift.put_container(workspace.swift_url, self.keystone.get_token('id'), workspace.swift_container, headers=headers)
        
        workspace.save()
        
        membership = StacksyncMembership(user=self, workspace=workspace, name='default')
        membership.save()

    def __unicode__(self):
        return self.email

class StacksyncWorkspace(models.Model):
    users = models.ManyToManyField(StacksyncUser, through='StacksyncMembership', related_name='stacksyncworkspace_users')
    name = models.CharField(max_length=200)
    latest_revision = models.IntegerField(default=0)
    is_shared = models.BooleanField(default=False)
    swift_container = models.CharField(max_length=200)
    swift_url = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
         db_table = settings.WORKSPACE_TABLE
    
    def __unicode__(self):
         return self.name
    
    
class StacksyncMembership(models.Model):
    user = models.ForeignKey(StacksyncUser, related_name='stacksyncmembership_user')
    is_owner = models.BooleanField(default=False)
    workspace = models.ForeignKey(StacksyncWorkspace)
    name = models.CharField(max_length=200)
    parent_item_id = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
         db_table = settings.MEMBERSHIP_TABLE

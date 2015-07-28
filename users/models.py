from django.core.urlresolvers import reverse
from django.db import models
from django_pg.models import UUIDField
from django_pg.models.fields.uuid import UUIDAdapter
from keystoneclient.v2_0 import client
from swiftclient import client as swift
from django.conf import settings
import uuid
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import default


def prefix():
    return str(uuid.uuid4()).split('-')[0]


class SwiftClient():
    def __init__(self):
        self.keystone = client.Client(username=settings.KEYSTONE_ADMIN_USER,
                                      password=settings.KEYSTONE_ADMIN_PASSWORD,
                                      tenant_name=settings.KEYSTONE_TENANT,
                                      auth_url=settings.KEYSTONE_AUTH_URL,
                                      insecure=True)

    def create_container(self, keystone_username=None, swift_url=None, swift_container=None):
        """creates the container in swift with read and write permissions"""
        user_and_tenant = settings.KEYSTONE_TENANT + ':' + keystone_username
        headers = {'x-container-read': user_and_tenant, 'x-container-write': user_and_tenant}

        swift_connection = swift.HTTPConnection(url=swift_url, insecure=True)
        swift.put_container(swift_url, self.keystone.get_token('id'), swift_container,
                            headers=headers, http_conn=(swift_connection.parsed_url, swift_connection))

    def delete_container(self, swift_url=None, swift_container=None):
        swift_connection = swift.HTTPConnection(url=swift_url, insecure=True)
        swift.delete_container(swift_url, self.keystone.get_token('id'), swift_container,
                               http_conn=(swift_connection.parsed_url, swift_connection))

    def get_container_metadata(self, swift_url, swift_container):
        swift_connection = swift.HTTPConnection(url=swift_url, insecure=True)
        return swift.head_container(swift_url, self.keystone.get_token('id'), swift_container,
                                    http_conn=(swift_connection.parsed_url, swift_connection))

    def set_container_quota(self, swift_url=None, swift_container=None, quota_limit=0):
        """sets the physical quota limit on the container"""
        headers = {'X-Container-Meta-Quota-Bytes': quota_limit*settings.B_2_MBY}
        swift_connection = swift.HTTPConnection(url=swift_url, insecure=True)
        swift.post_container(swift_url, self.keystone.get_token('id'), swift_container, headers=headers,
                             http_conn=(swift_connection.parsed_url, swift_connection))


class StacksyncUser(models.Model):
    id = UUIDField(auto_add=True, primary_key=True)
    name = models.CharField(max_length=25, help_text=_('25 characters max.'), verbose_name=_("User Name"))
    # email = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    swift_user = models.CharField(max_length=100, unique=True)
    swift_account = models.CharField(max_length=100)
    quota_limit = models.BigIntegerField(default=0)
    quota_used_logical = models.BigIntegerField(default=0)
    quota_used_real = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    # objects = StacksyncUserManager()

    class Meta:
        db_table = settings.USER_TABLE

    def __init__(self, *args, **kwargs):

        self.keystone = client.Client(username=settings.KEYSTONE_ADMIN_USER,
                                      password=settings.KEYSTONE_ADMIN_PASSWORD,
                                      tenant_name=settings.KEYSTONE_TENANT,
                                      auth_url=settings.KEYSTONE_AUTH_URL,
                                      insecure=True)
        self.keystone.management_url = settings.KEYSTONE_MANAGEMENT_URL

        # self.keystone = kwargs.pop('keystone', self.keystone)

        self.stacksync_tenant = self.get_keystone_tenant()
        try:
            super(StacksyncUser, self).__init__(*args, **kwargs)
        except:
            print("error")
        self.swift_account = 'AUTH_' + self.stacksync_tenant.id

        # Cambio de By a MBy
        self.quota_limit /= settings.B_2_MBY

    @property
    def keystone(self):
        """Get the keystone client"""
        return self._keystone_client

    @keystone.setter
    def keystone(self, value):
        self._keystone_client = value

    @property
    def stacksync_tenant(self):
        return self._stacksync_tenant

    @stacksync_tenant.setter
    def stacksync_tenant(self, value):
        self._stacksync_tenant = value

    def create_new_keystone_user(self, keystone_password):
        keystone_username = settings.KEYSTONE_TENANT + '_' + prefix() + '_' + self.name
        self.swift_user = keystone_username
        self.keystone.users.create(email=self.email, name=keystone_username, password=keystone_password,
                                   tenant_id=self.stacksync_tenant.id)
        return keystone_username

    def update_keystone_fields(self, keystone_password):
        self.keystone.users.update_password(self.get_keystone_user(), keystone_password)

    def save(self, aux, *args, **kwargs):
        self.quota_limit *= settings.B_2_MBY
        print('De donde venimos: ' + str(aux))
        if aux != 2:
            keystone_password = kwargs.pop('password', None)
            if not self.pk:
                self.create_new_keystone_user(keystone_password)
            elif keystone_password:
                self.update_keystone_fields(keystone_password)
            super(StacksyncUser, self).save(*args, **kwargs)
        else:
            print("ningun cambio")


    def delete(self, using=None):
        keystone_user = self.get_keystone_user()
        if keystone_user:
            if keystone_user.delete():
                super(StacksyncUser, self).delete()
        workspaces = self.get_workspaces()
        for workspace in workspaces:
            workspace.delete()

    def __unicode__(self):
        return self.email

    def get_keystone_user(self):
        keystone_users = self.keystone.users.list()
        return next((user for user in keystone_users if user.name == self.swift_user), None)

    def get_keystone_tenant(self):
        tenants = self.keystone.tenants.list()
        return next((x for x in tenants if x.name == settings.KEYSTONE_TENANT), None)

    def get_workspaces(self):
        return list(StacksyncWorkspace.objects.filter(owner=self))

    def get_absolute_url(self):
        return reverse('admin:users_stacksyncuser_change', args=[str(self.id)])


class StacksyncWorkspaceManager(models.Manager):
    def __init__(self):
        self.swift_client = SwiftClient()
        super(StacksyncWorkspaceManager, self).__init__()

    def setup_swift_container(self, stacksync_user, workspace):
        self.swift_client.create_container(stacksync_user.swift_user, workspace.swift_url, workspace.swift_container)

        if stacksync_user.quota_limit:
            self.swift_client.set_container_quota(workspace.swift_url,
                                                  workspace.swift_container,
                                                  stacksync_user.quota_limit)

    def create_workspace(self, stacksync_user):
        swift_url = settings.SWIFT_URL + '/' + stacksync_user.swift_account
        swift_container = settings.KEYSTONE_TENANT + '_' + prefix() + '_' + stacksync_user.name

        workspace = self.create(owner=stacksync_user,
                                swift_container=swift_container,
                                swift_url=swift_url,
                                is_shared=False)

        membership = StacksyncMembership.objects.create(user=stacksync_user, workspace=workspace, name='default')

        self.setup_swift_container(stacksync_user, workspace)

        return workspace


class StacksyncWorkspace(models.Model):
    id = UUIDField(verbose_name='UUID', auto_add=True, primary_key=True)
    users = models.ManyToManyField(StacksyncUser, through='StacksyncMembership',
                                   related_name='stacksyncworkspace_users')
    latest_revision = models.IntegerField(default=0)
    owner = models.ForeignKey(StacksyncUser)
    is_shared = models.BooleanField(default=False)
    is_encrypted = models.BooleanField(default=False)
    swift_container = models.CharField(max_length=45)
    swift_url = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = StacksyncWorkspaceManager()
    swift_client = SwiftClient()

    class Meta:
        db_table = settings.WORKSPACE_TABLE

    def __unicode__(self):
        return UUIDAdapter(self.id).getquoted()

    def delete(self, using=None):
        self.swift_client.delete_container(self.swift_url, self.swift_container)
        super(StacksyncWorkspace, self).delete()

    def get_container_metadata(self):
        return self.swift_client.get_container_metadata(self.swift_url, self.swift_container)

    def get_container_quota_limit(self):
        """
        Gets quota limit of container in bytes
        :return int:
        """
        container_metadata = (self.get_container_metadata())
        return int(container_metadata.get('x-container-meta-quota-bytes', 0))

    def set_container_quota_limit(self, quota):
        """
        Sets a quota for a container in bytes
        :param quota:
        :return:
        """
        return self.swift_client.set_container_quota(self.swift_url, self.swift_container, quota)

    def get_size_used(self):
        """
        Gets size of container in bytes
        :return int:
        """
        container_metadata = self.get_container_metadata()
        return int(container_metadata.get('x-container-bytes-used', 0))


class StacksyncMembership(models.Model):
    id = UUIDField(auto_add=True, primary_key=True)
    user = models.ForeignKey(StacksyncUser, related_name='stacksyncmembership_user')
    workspace = models.ForeignKey(StacksyncWorkspace)
    name = models.CharField(max_length=200, db_column="workspace_name")
    parent_item_id = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = settings.MEMBERSHIP_TABLE
        unique_together = (("user", "workspace"),)
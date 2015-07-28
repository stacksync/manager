from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.db import models
from django.db.models import Sum
from django_pg.models import UUIDField
from stacksync_manager import settings
from users.models import StacksyncUser
from django.utils.translation import ugettext_lazy as _


class StacksyncGroupUser(StacksyncUser):
    @property
    def physical_quota_used_logical(self):
        """
        Get space used in swift containers by the user
        :return in:
        """

        total = 0
        for workspace in self.get_workspaces():
            total += workspace.get_size_used()
            # total /= settings.B_2_MBY
        return total

    @property
    def physical_quota(self):
        quota_used_logical = StacksyncGroupUserQuota.objects.filter(user=self).aggregate(Sum('quota'))
        return quota_used_logical['quota__sum'] or 0

    class Meta:
        proxy = True
        verbose_name = _("Stacksync User")
        verbose_name_plural = _("Stacksync Users")

class StacksyncGroup(models.Model):
    users = models.ManyToManyField(StacksyncGroupUser, through='StacksyncGroupUserQuota')
    name = models.CharField(max_length=200, unique=True, verbose_name=_("Group"))
    quota = models.BigIntegerField(verbose_name=_("Group Quota Limit (MBy)"))
    admins = models.ManyToManyField(User, verbose_name=_("Admins."))

    def __unicode__(self):
        return self.name

    def clean(self):
        self.quota *= settings.B_2_MBY
        quota_used_logical = StacksyncGroupUserQuota.objects.filter(group=self).aggregate(Sum('quota'))
        if self.quota / settings.B_2_MBY < quota_used_logical['quota__sum']:
            raise ValidationError({
                # NON_FIELD_ERRORS:('Quota must be greater than the used quota',self.quota,quota_used_logical['quota__sum'])
                NON_FIELD_ERRORS: (_('Quota must be greater than the used quota'),
                                   _('You are trying to set a group Quota limit of: ') + str(
                                       self.quota / settings.B_2_MBY) + _(' with a Quota assigned of: ') + str(
                                       quota_used_logical['quota__sum']))
            })

    @property
    def quota_used_logical(self):
        quota_used_logical = StacksyncGroupUserQuota.objects.filter(group=self).aggregate(Sum('quota'))
        return quota_used_logical['quota__sum'] or 0

    @property
    def quota_occupied(self):
        quota_occupied = StacksyncGroupUser.objects.filter(stacksyncgroup=self).aggregate(Sum('quota_used_logical'))
        return quota_occupied['quota_used_logical__sum'] or 0

    def get_users(self):
        aux = ""
        for i in range(self.users.all().count()):
            if i + 1 < self.users.all().count():
                aux += (str(self.users.all()[i]) + ",<br/> ")
            else:
                aux += (str(self.users.all()[i]))
        return aux
    get_users.short_description = _('Users in this Group')
    get_users.allow_tags = True

    def get_users2(self):
        aux = ""
        for i in range(self.users.all().count()):
            if i + 1 < self.users.all().count():
                aux += (str(self.users.all()[i]) + "\n")
            else:
                aux += (str(self.users.all()[i]))
        return aux

    def get_admins(self):
        aux = ""
        for i in range(self.admins.all().count()):
            if i + 1 < self.admins.all().count():
                aux += (str(self.admins.all()[i]) + ", ")
            else:
                aux += (str(self.admins.all()[i]))
        return aux
    get_admins.short_description = _('Adminstrator Users')
    get_admins.allow_tags = True

    class Meta:
        verbose_name = _("Stacksync Group")
        verbose_name_plural = _("Stacksync Groups")


class StacksyncGroupUserQuota(models.Model):
    id = UUIDField(auto_add=True, primary_key=True)
    user = models.ForeignKey(StacksyncGroupUser, related_name='stacksyncgroupuserquota_user')
    group = models.ForeignKey(StacksyncGroup, verbose_name=_("Group"))
    quota = models.BigIntegerField(verbose_name=("Quota") + " (MegaBytes)")

    def __unicode__(self):
        #self.quota = round(self.quota / settings.B_2_MBY, 4)
        self.quota = round(self.quota, 4)
        #return "- User: " + str(self.user) + " - Group: " + str(self.group) + " - User Quota (MBy): " + str(self.quota)
        #Buscar solucion a por que no se traduce el MBy de abajo, da error al ntentar encasquetar un proxy object con un string, con la traduccion NO lazzy funciona
        return str(self.group) + " - MBy: " + str(self.quota)

        # quota_occupied, other way to see the user occupied space on disk
        #@property
        #def quota_occupied(self):
        #   return float(self.user.physical_quota_used_logical)/float(settings.B_2_MBY)

    def clean(self):
        old_quota = 0
        if self.pk:
            old_quota = StacksyncGroupUserQuota.objects.get(pk=self.pk).quota

        if (self.group.quota / settings.B_2_MBY) < self.group.quota_used_logical + self.quota - old_quota:
            raise ValidationError({
                NON_FIELD_ERRORS: (_('Quota exceeds limit '), _('Quota group: ') + str(self.group.quota / settings.B_2_MBY),
                                   _('Quota used: ') + str(self.group.quota_used_logical), _('Introduced quota: ') + str(self.quota),
                                   _('Quota modified: ') + str(old_quota), )
            })

        """
        This is for debug purposes only:
        """
        """
        if 1:
            raise ValidationError({
                NON_FIELD_ERRORS:('Quota exceeds limit ', 'Quota group: '+str(self.group.quota/settings.B_2_MBY), 'Quota used: '+str(self.group.quota_used_logical), 'Introduced quota: '+str(self.quota), 'Quota modified: '+str(old_quota), 'Cool: '+str(self.quota_occupied),)
                })
        """

class StacksyncGroupMember(models.Model):
    user = models.ForeignKey(StacksyncGroupUser)
    group = models.ForeignKey(StacksyncGroup)

    def __unicode__(self):
        return _("User: ") + str(self.user) + _(" Group:") + str(self.group)

    class Meta:
        unique_together = (("user", "group"),)

    # class StacksyncGroupAdmin(User):
    # @property
    # def user(self):
    # return self._user
    #
    # @user.setter
    # def user(self, user):
    #     self._user = user
    #
    # def __init__(self, user):
    #     self.user = user

    # def groups_managed(self):
    #     pass
    #
    # def quotas_managed_by_admin(current_user):
    #     groups_managed_by_admin = current_user.stacksyncgroup_set.all()
    #     return StacksyncGroupUserQuota.objects.filter(group__in=groups_managed_by_admin).distinct()
    #
    # def memberships_managed_by_admin(current_user):
    #     groups_managed_by_admin = current_user.stacksyncgroup_set.all()
    #     return StacksyncGroupMember.objects.filter(group__in=groups_managed_by_admin).distinct()
    #
    # class Meta:
    #     proxy = True

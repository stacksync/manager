from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.core.mail import send_mail

# Register your models here.
import psycopg2
from groups.forms import StacksyncGroupUserForm, RequiredFormSet
from groups.models import StacksyncGroup, StacksyncGroupUserQuota, StacksyncGroupUser, StacksyncGroupMember
from stacksync_manager import settings
from users.admin import StacksyncUserAdmin
from django.contrib.auth.tests.custom_user import groups
from decimal import Decimal

global is_super
is_super = False


def get_objects_managed_by_admin(request, obj, admin_class, parameters, group_or_user):
    """
    Returns a queryset of all objects, or a queryset depending on parameters

    :param request:
    :param obj: Object
    :param admin_class: Example StacksyncGroupAdmin
    :param parameters: dict
    :return:
    """
    if request.user.is_superuser & (request.user.username == 'admin'):
        is_super = True
    if group_or_user == 1:
        qs = super(admin_class, obj).queryset(request)
    else:
        qs = super(admin_class, obj).queryset(request).defer('created_at', 'swift_account')
        #qs = super(admin_class, obj).queryset(request).only('id', 'name', 'swift_user', 'email', 'quota_limit', 'quota_used_logical')
    if request.user.is_superuser:
        return qs
    return qs.filter(**parameters)


def setup_fields_for_forms(db_field, request, kwargs):
    if not request.user.is_superuser:
        if db_field.name == "user":
            groups_managed_by_user = {
                'stacksyncgroup__in': request.user.stacksyncgroup_set.all().prefetch_related('name')}
            kwargs["queryset"] = StacksyncGroupUser.objects.filter(**groups_managed_by_user).distinct()
        if db_field.name == "group":
            kwargs["queryset"] = StacksyncGroup.objects.filter(admins=request.user)
            
#Dibuja los grupos
class StacksyncGroupAdmin(admin.ModelAdmin):
    model = StacksyncGroup
    search_fields = ['name']
  
    # fieldsets = ('name', ('quota', 'quota_used_logical'), 'admins',)
    fieldsets = (
        (None, {
            'fields': (('name','admins'),'quota',),
        }),
        (None, {
            'fields': (('_my_quota_used_logical','_get_quota_occupied', '_get_quota_price'),),
        }),
        (None, {
            'fields': ('_get_users',),
        }),
    )
    
    def _get_name(self, obj):
        print obj.get_admins()
        return obj.name
        
    # list_display = ('name', '_get_quota', '_my_quota_used_logical')
    list_display = ('_get_name','get_admins', '_get_quota', '_my_quota_used_logical', '_get_quota_occupied', '_get_real_quota_occupied',   '_get_quota_price', '_get_users',)

    def _get_quota(self, obj):
        obj.get_admins()
        return round(float(obj.quota) / float(settings.B_2_MBY), 3)
    _get_quota.short_description = _("Group Quota Limit (MBy)")
    

    def _my_quota_used_logical(self, obj):
        return round(float(obj.quota_used_logical), 3)
    _my_quota_used_logical.short_description = _('Total Quota Assigned to Group Users (MBy)')

    def _get_quota_occupied(self, obj):
        return round(float(obj.quota_occupied) / float(settings.B_2_MBY), 3)
    _get_quota_occupied.short_description = _("Occupied Quota by User's Files (MBy)")
    
    
    def _get_real_quota_occupied(self, obj):
        users = obj.get_users2().split()
        email = users[0]
        print str(email)
        con_up = None
        try:
            con_up = psycopg2.connect(database=settings.MANAGER_DATABASE, user=settings.MANAGER_USER,
                                    host=settings.MANAGER_HOST, port=settings.MANAGER_PORT,
                                password=settings.MANAGER_PASS)
            con_up.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cur_up = con_up.cursor()
            sum = 0
            for mail in users: 
                query = "SELECT sum(quota_used_real) FROM user1 WHERE email = %s"
                cur_up.execute(query, (str(mail),))
                row = cur_up.fetchone()
                con_up.commit()
                sum += round(row[0] / Decimal(settings.B_2_MBY), 3)
            return sum
        except psycopg2.DatabaseError as e:
            print('Error %s' % e)
        finally:
            if con_up:
                con_up.close()
    _get_real_quota_occupied.short_description = _("Real Occupied Quota by User's Files (MBy)")
    
    

    #Precio de 2 ctmos por mega de euro puesto a boleo
    def _get_quota_price(self, obj):
        aux = float(obj.quota_occupied) / float(settings.B_2_MBY)
        if aux < 0:
            aux *= -1
        return round(aux * 0.02,2)
    _get_quota_price.short_description = _("Month Amount (Euros)")

    def _get_users(self, obj):
        return obj.get_users2()
    _get_users.short_description = _("Users in this group")

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            if obj:
                # Search where is a 1024 division before this point, to see quota in Mby its need to do this division and not other,
                # maybe its called twice (!?)
                obj.quota /= 1024
            return 'name', 'admins', 'quota', '_my_quota_used_logical', '_get_quota_occupied', '_get_quota_price', '_get_users'
        else:
            if obj:
                #WHY up there its need a 1024 division, but here, we need the complete division
                obj.quota /= settings.B_2_MBY
            return 'quota_used_logical', '_my_quota_used_logical', '_get_quota_occupied', '_get_quota_price', '_get_users'

    def queryset(self, request):
        """
        Filter the objects displayed in the change_list to only
        display those for the currently signed in user.
        """
        filter_parameters = {'admins': request.user}
        return get_objects_managed_by_admin(request, self, StacksyncGroupAdmin, filter_parameters, 1)


class GroupListFilter(admin.SimpleListFilter):
    title = _('Group')
    parameter_name = _('group')

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            groups = set(StacksyncGroup.objects.all())
        else:
            groups = set(request.user.stacksyncgroup_set.all())
        return [(g.id, g.name) for g in groups]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(group__id__exact=self.value())
        else:
            return queryset


class StacksyncGroupUserQuotaInLine(admin.StackedInline):
    model = StacksyncGroupUserQuota
    extra = 1
    formset = RequiredFormSet

    def get_queryset(self, request):
        filter_parameters = {'group__in': request.user.stacksyncgroup_set.all()}
        return get_objects_managed_by_admin(request, self, StacksyncGroupUserQuotaInLine, filter_parameters,
                                            1).distinct()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        setup_fields_for_forms(db_field, request, kwargs)
        return super(StacksyncGroupUserQuotaInLine, self).formfield_for_foreignkey(db_field, request, **kwargs)

    verbose_name = _("User's Group")
    verbose_name_plural = _("User's Groups")

class StacksyncGroupUserQuotaAdmin(admin.ModelAdmin):
    model = StacksyncGroupUserQuota
    search_fields = ['user__name', 'group__name']
    list_display = ('user', 'group', 'quota')
    fields = ('user', 'group', 'quota')
    readonly_fields = ('user',)
    list_filter = (GroupListFilter, )

    def queryset(self, request):
        
        if request.user.username == 'admin':
            global is_super
            is_super = True
        """
        Filter the objects displayed in the change_list to only
        display those for the currently signed in user.
        """
        filter_parameters = {'group__in': request.user.stacksyncgroup_set.all()}
        return get_objects_managed_by_admin(request, self, StacksyncGroupUserQuotaAdmin, filter_parameters,
                                            1).distinct()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        setup_fields_for_forms(db_field, request, kwargs)
        return super(StacksyncGroupUserQuotaAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

class StacksyncGroupInLine(admin.StackedInline):
    model = StacksyncGroup
    extra = 1


#Dibuja los usuarios
class StacksyncGroupUserAdmin(StacksyncUserAdmin):
    fields = ['name', 'email', 'password']


    search_fields = ['name', 'email', 'quota_limit']
    #list_filter = ['email']
    form = StacksyncGroupUserForm
    #inlines = [StacksyncGroupMemberInLine, StacksyncGroupUserQuotaInLine]
    inlines = [StacksyncGroupUserQuotaInLine]
    
    list_display = ('name', 'email', '_get_quota_limit', '_get_quota_used_logical', '_my_quota_used_real', 'query_get_group')


    def _get_quota_limit(self, obj):
        return round(obj.quota_limit,4)
    _get_quota_limit.short_description = _("Quota Limit (MegaBytes)")

    def _get_quota_used_logical(self, obj):
        return round(float(obj.quota_used_logical) / float(settings.B_2_MBY), 2)
    _get_quota_used_logical.short_description = _("Quota Used (MegaBytes)")
    
    def _my_quota_used_real(self, obj):
        return round(float(obj.quota_used_real) / float(settings.B_2_MBY), 3)
    _my_quota_used_real.short_description = _("Real quota used (MegaBytes)")
    

    def query_get_group(self, request):
        """
        Returns user group
        """
        if not request.stacksyncgroup_set.all():
            group = _("-> NO GROUP ASSIGNED <-")
            return group
        else:
            group = request.stacksyncgroup_set.all()
            if not len(group) <= 1:
                #aux = str(group[0])+", "+str(group[1])
                aux = ""
                for i in range(0, len(group)):
                    if i == len(group) - 1:
                        aux += str(group[i])
                    else:
                        aux += str(group[i]) + ", "
                return aux
            else:
                return group[0]
    query_get_group.short_description = _("Group")

    def queryset(self, request):
        
        if request.user.username == 'admin':
            global is_super
            is_super = True
        """
        Filter the objects displayed in the change_list to only
        display those for the currently signed in user.
        """
        if is_super:
            self.list_display = ('name', 'email', '_get_quota_limit', '_get_quota_used_logical', '_my_quota_used_real', 'query_get_group')
        else:
            self.list_display = ('name', 'email', '_get_quota_limit', '_get_quota_used_logical', 'query_get_group')

    
        groups_managed_by_admin = request.user.stacksyncgroup_set.all()
        filter_parameters = {'stacksyncgroup__in': groups_managed_by_admin}

        return get_objects_managed_by_admin(request, self, StacksyncGroupUserAdmin, filter_parameters, 2).distinct()

    def save_model(self, request, obj, form, change):
        #Caso en que cambiemos la contrasena
        if form.cleaned_data['password']:
            obj.save(0, password=form.cleaned_data['password'])
            """INICIO pruebas mensaje de bienvenida"""
            message1 = 'Hola ' + obj.name + ',\n\nComo usuario del e-mail: ' + obj.email + ', has sido dado de alta en nuestro sistema seguro para compartir y gestionar archivos, Stacksync.\nPara acceder, entra en: (--link a la pagina de login--) e introduce como username: ' + obj.email + ' y como password: ' + str(form.cleaned_data['password']) + '\nSi tienes cualquier duda, contacta con tu administrador (' + str(request.user) + '): ' + str(request.user.email) + '\n\nSaludos.'
            message2 = 'Hello ' + obj.name + ',\n\nAs owner of the e-mail: ' + obj.email + ', you have been registered in Stacksync, the secure file sharing system.\nTo log in, click in: (--link a la pagina de login--) introduce the username: ' + obj.email + ' and password: ' + str(form.cleaned_data['password']) + '\nIf you have any question, please ask to your administrator (' + str(request.user) + '): ' + str(request.user.email) + '\n\nKind regards.'
            message = message1  + '\n\n------------------------------------------------\n\n' + message2
            if send_mail('Dado de alta en Stacksync',
                         message,
                         settings.EMAIL_HOST_USER, [obj.email], fail_silently=False):
                print('e-mail enviado correctamente')
            else:
                print('error al enviar mensaje')
            """FINAL pruebas mensaje de bienvenida"""
        #caso en que no lo hagamos
        else:
            con_up = None
            try:
                con_up = psycopg2.connect(database=settings.MANAGER_DATABASE, user=settings.MANAGER_USER,
                                          host=settings.MANAGER_HOST, port=settings.MANAGER_PORT,
                                          password=settings.MANAGER_PASS)
                con_up.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                cur_up = con_up.cursor()
                query = "SELECT name, email, quota_limit FROM user1 WHERE id = %s"
                cur_up.execute(query, (str(obj.id),))
                row = cur_up.fetchone()
                con_up.commit()
            except psycopg2.DatabaseError as e:
                print('Error %s' % e)
            finally:
                if con_up:
                    con_up.close()
            #caso en que se haya cambiado o el nombre o el e-mail del usuario
            if form.cleaned_data['name'] != row[0] or form.cleaned_data['email'] != row[1]:
                #caso en que se haya cambiado el email
                if form.cleaned_data['email'] != row[1]:
                    obj.save(11)
                    """INICIO pruebas mensaje de cambio de correo"""
                    message1 = 'Hola ' + obj.name + ',\n\nComo usuario del e-mail: ' + obj.email + ', has sido dado de alta en nuestro sistema seguro para compartir y gestionar archivos, Stacksync.\nPara acceder, entra en: (--link a la pagina de login--) e introduce como username: ' + obj.email + ' y como password: \nDispones de una cuota de ' + str(row[2]) + ' MBy.\nSi tienes cualquier duda, contacta con tu administrador (' + str(request.user) + '): ' + str(request.user.email) + '\n\nSaludos.'
                    message2 = 'Hello ' + obj.name + ',\n\nAs owner of the e-mail: ' + obj.email + ', you have been registered in Stacksync, the secure file sharing system.\nTo log in, click in: (--link a la pagina de login--) introduce the username: ' + obj.email + ' and password: ' + str(form.cleaned_data['password']) + '\nYou got a limit quote of: ' + str(row[2]) + ' MBy.\nIf you have any question, please ask to your administrator (' + str(request.user) + '): ' + str(request.user.email) + '\n\nKind regards.'
                    message = message1  + '\n\n------------------------------------------------\n\n' + message2
                    if send_mail('Dado de alta en Stacksync',
                                 message,
                                 settings.EMAIL_HOST_USER, [obj.email], fail_silently=False):
                        print('e-mail enviado correctamente')
                    else:
                        print('error al enviar mensaje')
                    """FINAL pruebas mensaje de cambio de correo"""
                #caso en que solo se haya cambiado el nombre
                else:
                    obj.save(1)
            else:
                obj.save(2)

class StacksyncGroupMemberAdmin(admin.ModelAdmin):
    model = StacksyncGroupMember
    search_fields = ['user__name', 'group__name']
    list_display = ('user', 'group')

    def get_queryset(self, request):
        groups_managed_by_admin_user = request.user.stacksyncgroup_set.all()
        filter_parameters = {'group__in': groups_managed_by_admin_user}
        return get_objects_managed_by_admin(request, self, StacksyncGroupMemberAdmin, filter_parameters).distinct()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        setup_fields_for_forms(db_field, request, kwargs)
        return super(StacksyncGroupMemberAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


class StacksyncGroupMemberInLine(admin.StackedInline):
    model = StacksyncGroupMember
    extra = 1
    formset = RequiredFormSet

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "group":
                kwargs["queryset"] = StacksyncGroup.objects.filter(admins=request.user)
        return super(StacksyncGroupMemberInLine, self).formfield_for_foreignkey(db_field, request, **kwargs)


# admin.site.register(StacksyncGroupMember, StacksyncGroupMemberAdmin)
admin.site.register(StacksyncGroup, StacksyncGroupAdmin)
#admin.site.register(StacksyncGroupUserQuota, StacksyncGroupUserQuotaAdmin)
admin.site.register(StacksyncGroupUser, StacksyncGroupUserAdmin)
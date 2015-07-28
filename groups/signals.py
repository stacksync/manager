from django.core.mail import send_mail
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import psycopg2
from groups.models import StacksyncGroupUserQuota, StacksyncGroupUser, StacksyncGroupMember
from stacksync_manager import settings
from users.models import StacksyncWorkspace


@receiver(post_save, sender=StacksyncGroupUser)
def create_default_workspace_for_user(sender, instance, created, **kwargs):
    if created:
        StacksyncWorkspace.objects.create_workspace(instance)

"""
def update_used_quota(physical_quota, my_user_id):
    print('Charly 1')
    con_up = None
    try:
        print('Charly 2')
        con_up = psycopg2.connect(database=settings.MANAGER_DATABASE, user=settings.MANAGER_USER,
                                  host=settings.MANAGER_HOST, port=settings.MANAGER_PORT,
                                  password=settings.MANAGER_PASS)
        print('Charly 2.1, connection')

        con_up.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        #con_up.autocommit = True
        print('Charly 2.2, isolation')

        cur_up = con_up.cursor()
        print('Charly 2.3, cursor')

        #Funciona solo si no es sobre el usuario que esta en el user id
        #cur_up.execute("UPDATE groups_stacksyncgroupuserquota SET quota = " + str(physical_quota) + " WHERE user_id = 'f87654cd-6f0b-48e7-8f8b-173ce9738e0d'")

        query = "UPDATE user1 SET (quota_limit) = (%s) WHERE id = %s"
        cur_up.execute(query, (physical_quota,my_user_id,))

        #query = "SELECT * FROM groups_stacksyncgroupuserquota WHERE user_id = %s"
        #cur_up.execute(query, (my_user_id,))
        #rows = cur_up.fetchone()
        #print('Charly 2.4, after FIRST query ' + str(rows[2]))

        #query2 = "DELETE FROM groups_stacksyncgroupuserquota WHERE id = %s"
        #cur_up.execute(query2, (str(rows[0]),))
        #print('Charly 2.4, after SECOND query ')

        #query3 = "INSERT INTO groups_stacksyncgroupuserquota (id, user_id, group_id, quota) VALUES (%s, %s, %s, %s)"
        #cur_up.execute(query3, (str(rows[0]), my_user_id, str(rows[2]), physical_quota,))

        con_up.commit()
        print('Charly 2.5')

    except psycopg2.DatabaseError as e:
        print('Error %s' % e)

    finally:
        print('Charly 3')
        if con_up:
            con_up.close()
    return 1
"""

@receiver(post_delete, sender=StacksyncGroupUserQuota)
@receiver(post_save, sender=StacksyncGroupUserQuota)
def update_quota_for_user(sender, instance, created=None, **kwargs):
    physical_quota = instance.user.physical_quota
    my_user_id = str(instance.user.id)
    # This is -NOT- the correct place to take the integer from the quotas form fields, and multiply it to transform bytes in Megabytes (use 1073741824 to use Gigabytes)
    # The very correct place is in function safe of USERS/MODELS
    #physical_quota *= settings.B_2_MBY

    instance.user.quota_limit = physical_quota
    instance.user.save(4)

    for workspace in instance.user.get_workspaces():
        workspace.set_container_quota_limit(physical_quota)

    #print('Checkpoint Charly: ' + my_user_id)
    #update_used_quota(str(physical_quota), str(my_user_id))
    #print(physical_quota)


@receiver(post_delete, sender=StacksyncGroupMember)
def delete_user_after_zero_memberships(sender, instance, **kwargs):
    current_user = instance.user
    if current_user.stacksyncgroup_set.count() < 1:
        current_user.delete()






manager
=======

StackSync user manager

sudo apt-get install libpq-dev
sudo apt-get install python-dev

To create the database tables:
```
manage.py syncdb
```

Better update your current working stacksync database with:
```
ALTER TABLE workspace_user add column id uuid;
```

To install requirements necessary for the project to run:
```pip install -r requirements.txt```

pkill -9 -f stacksync_user
do syncdb

Update correct content_types for proxy model
```
from django.contrib.contenttypes.models import ContentType
group_user_type = ContentType.objects.filter(name='StacksyncGroupUser').first()

from django.contrib.auth.models import Permission
Permission.objects.filter(name__contains='StacksyncGroupUser')
Permission.objects.filter(name__contains='StacksyncGroupUser').update(content_type=group_user_type)
```

Restart services:
service stacksync-server restart
swift-init proxy restart

------------------------------------------------------
```
from django.contrib.auth.models import Group, Permission, User
p = Permission.objects.filter(content_type__app_label='groups').exclude(name='Can add stacksync group').exclude(name='Can delete stacksync group')
stacksync = Group.objects.create(name='stacksync')
stacksync.permissions = p
stacksync.save()

valencia_ad = User.objects.create(username='valencia', is_staff=True)
valencia_ad.groups.add(stacksync)
valencia_ad.set_password('valencia')
valencia_ad.save()
```
--------------------------------------
This is an example to get a Group admin called 'valencia', creating a group 'valencia' with a quota of 100, and assign the admin to the quota
```
from groups.models import StacksyncGroup
valencia_ad = User.objects.get(username='valencia', is_staff=True)
group = StacksyncGroup.objects.create(name='valencia', quota=100)
group.admins.add(valencia_ad)
group.save()
group.admins.first()
```
----------------------------------------------------------






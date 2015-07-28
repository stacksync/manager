import csv
from django.test import TestCase
import unicodedata
from groups.models import StacksyncGroupUserQuota, StacksyncGroupMember, StacksyncGroup, StacksyncGroupUser
from users.models import StacksyncUser
import codecs

class StacksyncGroupTest():

    #def assert_user_OK(self, testuser):
     #   self.assertIsNotNone(testuser.swift_account)
      #  self.assertIsNotNone(testuser.swift_user)
       # self.assertIsNotNone(testuser.stacksync_tenant)

    def getUserFromCSV(self, row):
        nombre = row[0].split(";")[1]
        email = row[0].split(";")[0]
        return email.strip(), nombre.strip()

    def test_create_pass(self):
        #with open('Listado_nombres_tissat.csv') as f:
            #reader = csv.reader(f)
        my_group = StacksyncGroup.objects.filter(name='valencia').first()

        reader = csv.reader(open('Listado_nombres_tissat.csv', 'rb'))
        for row in reader:
            #row = normalizar(row)
            password = "tissat14"
            email, nombre = self.getUserFromCSV(row)

            testuser = StacksyncGroupUser(name=nombre, email=email)
            testuser.save(password=password)

            StacksyncGroupMember.objects.create(user=testuser, group=my_group)
            StacksyncGroupUserQuota.objects.create(group=my_group, user=testuser, quota=1)

            #self.assert_user_OK(testuser)

            print(nombre)
            print(email)
            print(my_group)
        users = list(StacksyncUser.objects.all())
        print(users)



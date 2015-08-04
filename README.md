StackSync Web Manager
=======

The StackSync web manager is a tool that allows to create and manage groups and users for StackSync.

# Installation

First, install dependencies:

    sudo apt-get install libpq-dev
    sudo apt-get install python-dev
    pip install -r requirements.txt

Once the requirements are installed, we have to create database tables for the manager. Before to sync the database, you have to change the settings.py file located [here](stacksync_manager/settings.py). After that, you just need to run the following command:

    sudo python manage.py syncdb

This command will create necessary tables in the StackSync database. Furthermore, if it is the first time that you execute it, you will have to create an admin user. This user will be used to access the manager interface and create other admins/groups.

# Execution

To run the manager interface you can configure the django project on top of Apache or you can execute directly the following command:

    sudo python manage.py runserver 0.0.0.0:80

When the manager is running, you can access it from the browser with the following URL:

    http://127.0.0.1:80/admin

or

    http://PUBLIC-IP:80/admin

# Manual

## Create admin group and administrator

In a StackSync deploy we can manage different groups. A group can be a company, institution or university. In this example, we will create the Universtitat Rovira i Virgili (urv) group.

First of all, the admin of StackSync has to log in into the manager interface. The following image shows the login interface and the admin menu of the management web.

<p align="center">
  <img width="400" src="https://raw.githubusercontent.com/stacksync/manager/master/manual/login.png">
  <img width="400" src="https://raw.githubusercontent.com/stacksync/manager/master/manual/menu.png">
</p>

Once it is done, the admin has to create the URV group with the necessary permissions:

<p align="center">
  <img width="600" src="https://raw.githubusercontent.com/stacksync/manager/master/manual/addgroup.png">
</p>
<p align="center">
   <img width="320" src="https://raw.githubusercontent.com/stacksync/manager/master/manual/listgroup.png">
</p>

Next step is to create an admin user for this new group. In our case, we will create the urv_admin user. This user will have the rights to create subgroups inside the urv group, i.e. departments, create users and set their quota.

<p align="center">
  <img width="300" src="https://raw.githubusercontent.com/stacksync/manager/master/manual/createadminuser.png">
  <img width="500" src="https://raw.githubusercontent.com/stacksync/manager/master/manual/adminusercreated.png">
</p>

It is also necessary to set the permissions to that admin user. It is important to select only the urv as the group to administrate. Otherwise, this user will have access to others groups in the platform.

<p align="center">
  <img width="600" src="https://raw.githubusercontent.com/stacksync/manager/master/manual/adminuserpermissions.png">
</p>

## Create subroups and StackSync users

In the following images we will show how this admin user can create subgroups in the urv group. We can understand these groups as departments of a company.

<p align="center">
  <img width="500" src="https://raw.githubusercontent.com/stacksync/manager/master/manual/stacksyncgroup.png">
  <img width="300" src="https://raw.githubusercontent.com/stacksync/manager/master/manual/listgroup.png">
</p>

As you can see in the next image, the admin has to specify a total quota for that group. Next, we are going to create a user in this group.

<p align="center">
  <img width="400" src="https://raw.githubusercontent.com/stacksync/manager/master/manual/createuser.png">
</p>

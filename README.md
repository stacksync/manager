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

This command will create necessary tables in the StackSync database.

# Execution

To run the manager interface you can configure the django project on top of Apache or you can execute directly the following command:

    sudo python manage.py runserver 0.0.0.0:80

# Manual

TBD





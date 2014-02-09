nautilus
========

An easily extendible, module-based python IRC bot framework.

Usage
========
Simply edit ```config.json``` and run ```bot.py```. Make sure the nickname you assign to your bot is free, you'll want to query it for the initial setup.

The default username and password for nautilus are admin:12345.

To login to your bot query him with:

```auth admin 12345```

After that you'll want to change your password. Type:

```users changepass 12345 <new password>```

You can list available commands with ```users``` ```perform``` or by looking at the source code of any of the running modules.
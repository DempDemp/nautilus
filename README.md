nautilus
========

An easily extendible, module-based python IRC bot framework.

Usage
-----
Simply edit `config.json` and run `bot.py`. Make sure the nickname you assign to your bot is free, you'll want to query it for the initial setup.

The default username and password for nautilus are admin:12345.

To login to your bot query him with:

```
auth admin 12345
```

After that you'll want to change your password. Type:

```
users changepass 12345 <new password>
```

You can list available commands with `users` `perform` or by looking at the source code of any of the running modules.

Modules
-----
Included modules:

`youtube` Youtube announcer.

`twitter` Follow twitter users.

`rss` Follow RSS feeds.

`ideone` Runs code with ideone.

`titles` Whitelist based URL titles announcer.

`tinysong` Song finder.

`tvrage` TV series next and last episode information.

`imdb` IMDB search.

`ircpaint` Spams ascii art (from [http://ircpaint.randomlab.info](http://ircpaint.randomlab.info "Very cool IRC art generator")).

`truerandom` Fetches true random numbers from random.org.

And more. Writing modules is *very* easy. Just take a look at any of the included modules.

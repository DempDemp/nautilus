BOTS = [
    {
        'id': 'nautilus',
        'nickname': 'nautilus',
        'realname': 'nautilus',
        'server': 'irc.freenode.net',
        'port': 6667,
        'ssl': False,
        'flood_buffer': 1024,
        'modules': [
            'checkboxes',
            'dfeojm',
            'ideone',
            'imdb',
            'ircpaint',
            'titles',
            'truerandom',
            'tvrage',
        ]
    },
]

DEBUG = False
DATABASE = 'sqlite:///nautilus.db'

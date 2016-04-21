import wolframalpha
from core import base
from core.conf import settings

class WolframAlpha(base.baseClass):
    client = None
    show_pods = 3
    results = None
    titles = None

    def __init__(self, *args, **kwargs):
        super(WolframAlpha, self).__init__(*args, **kwargs)
        self.client = wolframalpha.Client(settings.WOLFRAMALPHA_API_KEY)

    def query(self, query):
        response = self.client.query(query)
        count = 1
        self.results = []
        self.titles = []
        if len(response.pods) == 0:
            return False
        for pod in response.pods:
            if pod.text != 'None' and pod.text is not None:
                self.results.append(u'{bold}({count}) {title}:{bold} {result}'.format(bold=chr(2), count=count, title=pod.title, result=pod.text.replace('\n', ' | ')))
                self.titles.append(u'{bold}({count}) {title}'.format(bold=chr(2), count=count, title=pod.title))
                count += 1
        return True

    def on_privmsg(self, address, target, text):
        if text[0] in base.prefix and text.strip().split(' ', 1)[0][1:] == 'wa':
            second_word = text.strip().split()[1]
            if len(text.strip().split()) == 2 and second_word.isdigit():
                num = int(second_word)
                if num > 0 and num <= len(self.results):
                    self.irc.msg(target, self.results[num - 1])
            else:
                query = ' '.join(text.strip().split()[1:])
                if self.query(query):
                    if len(self.results) <= self.show_pods:
                        self.irc.msg(target, ' '.join(self.results))
                    else:
                        self.irc.msg(target, ' '.join(self.results[:self.show_pods]))
                        self.irc.msg(target, u'Additional results: {}'.format(' | '.join(self.titles[self.show_pods:])))
                else:
                    self.irc.msg(target, u'{bold}WolframAlpha{bold} Unable to compute'.format(bold=chr(2)))

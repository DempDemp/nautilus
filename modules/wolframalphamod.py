import wolframalpha
from core.base import baseClass, command
from core.conf import settings

class WolframAlpha(baseClass):
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

    @command(['wa', 'wolframalpha'], min_params=1)
    def wolframalpha(self, target, params, **kwargs):
        param = params[0]
        if len(params) == 2 and param.isdigit():
            num = int(param)
            if num > 0 and num <= len(self.results):
                self.irc.msg(target, self.results[num - 1])
        else:
            query = ' '.join(params)
            if self.query(query):
                if len(self.results) <= self.show_pods:
                    self.irc.msg(target, ' '.join(self.results))
                else:
                    self.irc.msg(target, ' '.join(self.results[:self.show_pods]))
                    self.irc.msg(target, u'Additional results: {}'.format(' | '.join(self.titles[self.show_pods:])))
            else:
                self.irc.msg(target, u'{bold}WolframAlpha{bold} Unable to compute'.format(bold=chr(2)))

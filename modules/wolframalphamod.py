import wolframalpha
from core.base import baseClass, command
from core.conf import settings

SHOW_PODS = 3

class NoResults(Exception):
    pass

class WolframAlpha(baseClass):
    client = None

    def __init__(self, *args, **kwargs):
        super(WolframAlpha, self).__init__(*args, **kwargs)
        self.client = wolframalpha.Client(settings.WOLFRAMALPHA_API_KEY)

    def query(self, query):
        response = self.client.query(query)
        if not response.pods:
            raise NoResults
        return response.pods[0], [pod for idx, pod in enumerate(response.pods) if idx and pod.text]

    @command(['wa'], min_params=1)
    def wolframalpha_short(self, target, params, **kwargs):
        if len(params) == 2 and params[0].isdigit():
            num = int(params.pop(0))
        else:
            num = 1
        try:
            query, results = self.query(' '.join(params))
        except NoResults:
            return self.irc.msg(target, u'{bold}WolframAlpha{bold}: Unable to compute'.format(bold=chr(2)))
        if num > len(results):
            num = len(results)
        pod = results[num - 1]
        result = u''
        if pod.title != 'Result':
            result = u'{italics}({title}){italics} '.format(italics=chr(29), title='; '.join(pod.title.splitlines()))
        self.irc.msg(target, u'[{num}/{max_num}] {query}: {result}'.format(
            num=num,
            max_num=len(results),
            query='; '.join(query.text.splitlines()),
            result=result + '; '.join(pod.text.splitlines())[:150],
        ))

    @command(['wa-ext', 'wolframalpha'], min_params=1)
    def wolframalpha_ext(self, target, params, **kwargs):
        try:
            query, results = self.query(' '.join(params))
        except NoResults:
            return self.irc.msg(target, u'{bold}WolframAlpha{bold}: Unable to compute'.format(bold=chr(2)))
        msg = []
        additional = []
        for idx, pod in enumerate(results):
            if idx >= SHOW_PODS:
                additional.append(u'{}. {}'.format(idx + 1, '; '.join(pod.title.splitlines())))
            else:
                msg.append(u'{idx}. {bold}{title}{bold}: {result}'.format(
                    bold=chr(2),
                    idx=idx + 1,
                    title='; '.join(pod.title.splitlines()),
                    result='; '.join(pod.text.splitlines())[:150],
                ))
        msg = u'{}: '.format('; '.join(query.text.splitlines())) + u' '.join(msg)
        if additional:
            msg += u' {bold}More{bold}: {additional}'.format(bold=chr(2), additional=u' '.join(additional))
        self.irc.msg(target, msg)

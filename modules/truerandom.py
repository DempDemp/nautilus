import urllib
import urllib2
from core import base

class truerandomClass(base.baseClass):
    @staticmethod
    def truerandom(low, high, base = 10, num = 1):
        if low < -1000000000 or high > 1000000000 or high <= low or (base != 2 and base != 8 and base != 10 and base != 16) or num < 1 or num > 10000:
            return {'error': 'error'}
        params = {
            'num': num,
            'min': low,
            'max': high,
            'col': 1,
            'base': base,
            'format': 'plain',
            'rnd': 'new'
        }
        req  = urllib2.Request('http://www.random.org/integers/?' + urllib.urlencode(params))
        try:
            response = urllib2.urlopen(req)
        except:
            return {'error': 'error'}
        data = response.read()
        return {'result': ' '.join(data.split('\n'))}

    def privmsg_format(self, result):
        if 'error' in result:
            msg = ['[Random] an error occurred']
        elif 'result' in result:
            result['result'] = result['result'].split('\n')[0]
            prefix = '[Random] '
            maxlength = 430 - len(prefix)
            if (len(result['result']) > maxlength):
                result['result'] = result['result'][0:maxlength-1]
            msg = '[Random] ' + result['result']
        return msg.strip()

    def on_privmsg(self, address, target, text):
        if text[0] in base.prefix and text.strip().split(' ', 1)[0][1:] in ('random', 'rand', 'rnd') and len(text.split()) >= 2:
            length = len(text.split())
            rnd_low = 0
            rnd_high = 100000
            rnd_base = 10
            rnd_num = 1
            sp = text.split()
            if length >= 2 and sp[1].isdigit():
                rnd_low = 0
                rnd_high = int(sp[1])
            if length >= 3 and sp[1].isdigit() and sp[2].isdigit():
                rnd_low = int(sp[1])
                rnd_high = int(sp[2])
            if length >= 4 and sp[3].isdigit():
                rnd_base = int(sp[3])
            if length == 5 and sp[4].isdigit() and int(sp[4]) <= 20:
                rnd_num = int(sp[4])
            self.irc.msg(target, self.privmsg_format(self.truerandom(rnd_low, rnd_high, rnd_base, rnd_num)))

'''
Copyright 2014 Demp <lidor.demp@gmail.com>
This file is part of nautilus.

nautilus is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

nautilus is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with nautilus. If not, see <http://www.gnu.org/licenses/>.
'''

import urllib, urllib2
from core import botutils

try:
	import json
except ImportError:
	import simplejson as json

langs = ['ada', 'assembler', 'awk', 'bash', 'bc', 'brainf**k', 'c', 'c#', 'cpp', 'c99', 'clips', 'clojure', 'cobol', 'clisp', 'd', 'erlang', 'factor', 'forth', 'fortran', 'go', 'groovy', 'haskell', 'icon', 'intercal', 'java', 'rhino', 'javascript', 'lua', 'nemerle', 'nice', 'nimrod', 'ocaml', 'oz', 'pascal', 'perl', 'php', 'pike', 'prolog', 'python', 'python3', 'r', 'ruby', 'scala', 'scheme', 'smalltalk', 'tcl', 'unlambda', 'vbasic', 'whitespace']

class ideoneClass(botutils.baseClass):
	def ideone(self, lang, code):
		if not len(code) or not len(lang):
			return {'error': 'error'}
		headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11',
			'Content-Type': 'application/x-www-form-urlencoded',
			'Origin': 'http://run-this.appspot.com',
			'Referer': 'http://run-this.appspot.com/'
		}
		prependcode = ''
		appendcode = ''
		if lang.lower() == 'c' or lang.lower() == 'c99':
			prependcode = '#include <stdio.h>\n'
			if code.replace('main ()', 'main()').replace('main (void)', 'main()').replace('main(void)', 'main()').find(' main()') < 0 or code.find('#include') < 0:
				prependcode += 'int main() {'
				appendcode = 'return 0; }'
		elif lang.lower() == 'php' and code.find('<?php') < 0:
			prependcode = '<?php '
		code = prependcode + code + appendcode
		values = {'code': code, 'lang': lang, 'input': ''}
		data = urllib.urlencode(values)
		req = urllib2.Request('http://run-this.appspot.com/runthis', data, headers)
		try:
			response = urllib2.urlopen(req)
		except urllib2.HTTPError:
			return {'error': 'error'}
		data = response.read()
		try:
			data = json.loads(data)
		except ValueError:
			return {'error': 'error'}
		return data

	def privmsg_format(self, result):
		if 'error' in result:
			print 'Error occured - ideone'
			msg = ''
		else:
			if 'time' in result:
				msg = '> t: ' + str(result['time']) + ' m: ' + str(result['memory']) + ' o: '
				out = result['output'].split('\n')
			elif 'stderr' in result:
				msg = '> stderr: '
				out = result['stderr'].split('\n')
			maxlength = 430 - len(msg)
			tback = False
			output = ''
			for line in out:
				if len(line) == 0:
					continue
				if line[0:10] == 'Traceback ':
					tback = True
				elif tback:
					if line[0:2] != '  ':
						tback = False
						output += 'Exception: ' + line + '; '
				else:
					output += line + '; '
			if len(output) > maxlength:
				output = output[0:maxlength-7] + '...'
			msg += output
		return msg
	
	def onPRIVMSG(self, address, target, text):
		words = text.strip().split(' ')
		if len(words) < 3:
			return None
		first_word = words[0]
		second_word = words[1]
		if first_word == '>>' and second_word.lower() in langs and len(text.split(' ')) >= 3:
			result = self.ideone(second_word.replace('-', ' '), ' '.join(words[2:]).decode('string_escape'))
			self.irc.msg(target, self.privmsg_format(result))
			
MODCLASSES = [ideoneClass]
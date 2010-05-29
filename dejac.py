# encoding: utf-8
from numbers import Number
import sys

class DejaVuError(Exception):
	def __str__(self):
		return 'error: '+self.val()
class DejaVuCompilationError(DejaVuError):
	def __init__(self, name, line, context):
		self.name = name
		self.line = line
		self.context = context
	def __str__(self):
		return '%s on line %s (%s)' % (self.name, self.context.line_i, self.line.strip())
class DejaVuIndentationError(DejaVuCompilationError):
	pass

def strip_comments(line):
	try:
		return line[:line.index('#')]
	except ValueError:
		return line

def split_words(line):
	return line.split()

def general_type(word):
	if word.isdigit():
		return 'num'
	if word.startswith("'") and word.endswith("'"):
		return 'ident'
	if word.startswith('-') and word[1:].isdigit():
		return 'negnum'
	return 'word'

bytecode = {'push word': '\x01',
            'push number': '\x02',
            'push ident': '\x03',
            'push function': '\x04',
            'jmp': '\x11',
            'jmp if zero': '\x12',
            'jmp if not zero': '\x13',
           #'jmp back': '\x21',
           #'jmp back if zero': '\x22',
           #'jmp back if not zero': '\x23',
            'line': '\xff',
            }

bytecodename = {}
for k in bytecode:
	bytecodename[bytecode[k]] = k

statements = ('func', 'labda', 'if', 'else',
              #'elseif',
              'while', 'until')

class Context(object):
	def __init__(self):
		self._acc = []
		self._stmts = []
		self.colon = False
		self.indent = 0
		self.line_i = 0
	def add(self, *args):
		self._acc.append(args)
	def header(self):
		return 'Déjà Vu\x00 Byte Code v0.2\n'
	def encodenumber(self, number, minsize=1):
		neg = number < 0
		number = abs(number)
		tmp = []
		while number:
			tmp.append(chr(number%256))
			number /= 256
		while len(tmp) < minsize:
			tmp.append('\x00')
		tmp.insert(0, chr(neg and 255 - len(tmp) or len(tmp)))
		return ''.join(tmp)
	def encodestring(self, string, minsize=1):
		return chr(max(len(string), minsize))+string.ljust(minsize)
	def bytecode(self):
		self.finishstatements(0, '')
		acc = [self.header()]
		refs = {}
		i = 0
		l = 0
		for t in self._acc:
			T, t = t[0], t[1:]
			refs[i] = l
			min = (T.startswith('jmp') or T=='push function') and 2 or 1
			l += sum((len((isinstance(x, Number) and self.encodenumber or self.encodestring)(x,min)) for x in t), 1)
			i += 1
		refs[i] = l
		for i in range(len(self._acc)):
			T = self._acc[i][0]
			if (T.startswith('jmp') or T=='push function'):
				loc=self._acc[i][1]
				self._acc[i] = (T, refs[i+loc]-refs[i+1])
				#sys.stderr.write(str(loc))
				#sys.stderr.write('\n')
		for t in self._acc:
			#sys.stderr.write(str(t))
			#sys.stderr.write('\n')
			T, t = t[0], list(t[1:])
			for i in range(len(t)):
				if isinstance(t[i], Number):
					t[i] = self.encodenumber(t[i], T.startswith('jmp') and 2 or 1)
				else:
					t[i] = self.encodestring(t[i])
			acc.append(bytecode[T] + ''.join(t))
		return ''.join(acc)
	def clear(self):
		self._acc = []
	def expected_indentation(self):
		return self.indent + self.colon
	def statement(self, *args):
		self._stmts.append(args)
	def finishstatements(self, tabs, line):
		while self._stmts and self._stmts[-1][2] >= tabs:
			stmt, pos, indent, prefacc = self._stmts.pop()
			sys.stdout.write(str((stmt, pos, indent, prefacc)))
			sys.stdout.write('\n')
			#if stmt in ('if', 'else', 'elseif'):
			p = 0
			if stmt == 'if':
				line = line.strip()
				if line.endswith(':') and line[:-1].strip() == 'else':
					sys.stdout.write('ELSE-CLAUSE\n')
					p = 1
			if stmt in ('while', 'until'):
				#self.add('jmp if not zero', prefacc - len(self._acc))
				self.add('jmp', prefacc - len(self._acc))
				#self.add('jmp back if not zero', len(self._acc) - prefacc)
			self._acc[pos] = self._acc[pos] + (len(self._acc) - pos + p,) #resume here
			#print('###',self._acc[pos])
			if stmt == 'func':
				self.add('push word', 'swap')
				self.add('push word', 'set')
			#if stmt == 'until':
			#	self.add('jmp back if zero', len(self._acc) - pos - 2)
	def parse_line(self, line):
		self.line_i += 1
		line = strip_comments(line)
		if line.strip():
			self.add('line', self.line_i, line.strip())
			prefacc = len(self._acc)
			tabs = line.count('\t')
			while tabs:
				if line.startswith('\t'*tabs):
					break
				tabs = tabs - 1
			if tabs > self.expected_indentation():
				raise DejaVuIndentationError('unexpected indent', line, self)
			if tabs < self.indent:
				#finish up previous statements
				self.finishstatements(tabs, line)
			self.indent = tabs
			line = line.strip()
			if line[-1] == ':':
				self.colon = True
				line = line[:-1]
				if not line:
					raise DejaVuCompilationError('loose colon', line, self)
			else:
				self.colon = False
			words = split_words(line)
			for i in range(len(words)-1, self.colon-1, -1):
				t = general_type(words[i])
				if t in ('num', 'negnum'):
					self.add('push number', int(words[i]))
				elif t == 'ident':
					self.add('push ident', words[i][1:-1])
				#elif t == 'negnum':
				#	self.add('push number', 0)
				#	self.add('push number', int(words[i]))
				#	self.add('push word', '-')
				else: #word
					self.add('push word', words[i])
			if self.colon:
				keyword = words[0]
				if keyword in statements:
					if keyword == 'if':
						self.add('jmp if zero')#, 'IF_REF')
					elif keyword == 'else':
						#self.add('jmp', 2)
						self.add('jmp')#, 'ELSE_REF')
					#elif keyword == 'elseif':
					#	self.add('jmp', 'ELSE_REF')
					#	self.add('jmp if zero', 'IF_REF') #maybe later?
					elif keyword == 'while':
						self.add('jmp if zero')#, 'IF_REF')
					elif keyword == 'until':
						self.add('jmp if not zero')#, 2)
						#self.add('jmp')#, 'IF_REF')
					elif keyword == 'func':
						self.add('push function')#, len(self._acc)+5)
						#self.add('push word', 'swap')
						#self.add('push word', 'set')
						#self.add('jmp')#, 'END_FUNC_REF')
					elif keyword == 'labda':
						self.add('push function')#, len(self._acc)+3)
						#self.add('jmp')#, 'END_FUNC_REF')
					self.statement(keyword, len(self._acc)-1, self.indent, prefacc)
				elif len(words) == 1 and general_type(keyword) == 'word':
					#act as if "func 'keyword':" was given
					self.add('push ident', keyword)
					self.add('push function')#, len(self._acc)+5)
					#self.add('push word', 'set')
					#self.add('jmp')#, 'END_FUNC_REF')
					self.statement('func', len(self._acc)-1, self.indent, prefacc)
				else:
					raise DejaVuCompilationError('illegal statement', line, self)

def compile(text):
	context = Context()
	for line in text.splitlines():
		context.parse_line(line)
	return context.bytecode()

if __name__ == '__main__':
	import sys
	sys.stdout.write(compile(sys.stdin.read()))
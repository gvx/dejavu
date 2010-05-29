#!/usr/bin/env python
#encoding: utf-8
import sys
import dejac
import words
import readline
import os
histfile = os.path.join(os.environ["HOME"], ".dv_hist")
try:
    readline.read_history_file(histfile)
except IOError:
    pass
import atexit
atexit.register(readline.write_history_file, histfile)
del os, histfile

from optparse import OptionParser
#from numbers import Number

class DejaVuRunTimeError(dejac.DejaVuError):
	def __init__(self, name, env):
		self.name = name
		self.env = env
	def val(self):
		try:
			return '%s on line %s (%s)' % (self.name, self.env.line_i, self.env.line)
		except AttributeError:
			return self.name
class DejaVuVersionError(DejaVuRunTimeError):
	def __init__(self, name):
		self.name = name
	def val(self):
		return self.name

curver = '0.2'

ps1 = ': '
ps2 = '- '

class Ref(object):
	def __init__(self, func):
		self.func = func
		self.locals = {}
		self.index = 0
		self.line = None
		self.line_i = 0

class Func(object):
	def __init__(self, code):
		self.code = code
		#self.locals = {}
	def __call__(self, env):
		env.returnstack.append(Ref(self))

class Env(object):
	def __init__(self):
		self.idents = default_idents()
		self.stack = []
		self.returnstack = []
	def decodenumber(self, string):
		n = 0
		exp = 0
		for char in string:
			n += ord(char) * 256**exp
			exp += 1
		return n
	def readnum(self, bytecode, index):
		size = ord(bytecode[index])
		neg = False
		if size > 127:
			size = 255-size
			neg = True
		n = self.decodenumber(bytecode[index+1:index+1+size])
		return neg and -n or n, index+1+size
	def readstr(self, bytecode, index):
		size = ord(bytecode[index])
		return bytecode[index+1:index+1+size], index+1+size
	def get(self, ident):
		#first check locals... not currently implemented
		if False:
			pass
		#then check globals
		elif ident in self.idents:
			return self.idents[ident]
		else:
			return 0
	def set(self, ident, val):
		self.idents[ident] = val
	def pop(self):
		if self.stack:
			return self.stack.pop()
		print('stack empty!')
		ref = self.returnstack[-1]
		print(ref.index)
		print(repr(ref.func.code[ref.index - 12: ref.index + 13]))
		raise DejaVuRunTimeError("Stack empty", self)
		return 0
	def push(self, n):
		self.stack.append(n)
	def call(self, st):
		id = self.get(st)
		if callable(id):
			id(self)
		elif isinstance(id, Ref):
			pass #call Deja Vu function
		else:
			self.push(id)
	def exit(self):
		exit()
	def run(self, bytecode):
		Func(bytecode)(self)
		self.runframe()
	def runframe(self):
		while self.returnstack:
			ref = self.returnstack[-1]
			while self.returnstack and ref == self.returnstack[-1]:
				ref.index = self.runfragment(ref.func.code, ref.index)
				if ref.index >= len(ref.func.code):
					self.returnstack.pop()
	def runfragment(self, bytecode, index):
		try:
			c = dejac.bytecodename[bytecode[index]]
		except KeyError as e:
			raise DejaVuRunTimeError('wrong bytecode %s (%s) on position %s'%(ord(e.args[0]), e.args[0], index), self)
		print(index, bytecode[index], c, c.startswith('jmp') and self.readnum(bytecode,index+1)[0] or None)
		index += 1
		if c == 'push word':
			st, index = self.readstr(bytecode, index)
			print(st)
			self.call(st)
		elif c == 'push number':
			n, index = self.readnum(bytecode, index)
			self.push(n)
		elif c == 'push ident':
			s, index = self.readstr(bytecode, index)
			self.push(s)
		elif c == 'push function':
			n, index = self.readnum(bytecode, index)
			self.push(Func(bytecode[index:index+n]))
			index += n
		elif c == 'jmp':
			n, index = self.readnum(bytecode, index)
			index += n
			print('JMP', n)
		elif c == 'jmp if zero':
			n, index = self.readnum(bytecode, index)
			if self.pop() == 0:
				index += n
		elif c == 'jmp if not zero':
			n, index = self.readnum(bytecode, index)
			if self.pop() != 0:
				index += n
		elif c == 'line':
			self.line_i, index = self.readnum(bytecode, index)
			self.line, index = self.readstr(bytecode, index)
			print(self.line_i, self.line)
			self.returnstack[-1].line_i = self.line_i
			self.returnstack[-1].line = self.line
			#print('LINE', self.line, self.line_i)
		return index

def default_idents():
	return {'>': words.more, 'more': words.more,
	        '<': words.less, 'less': words.less,
	        '=': words.equals, 'equals': words.equals,
	        'set': words.set, 'eat': words.set,
	        '+': words.add, 'add': words.add,
	        '-': words.sub, 'sub': words.sub,
	        '*': words.mul, 'mul': words.mul,
	        '/': words.div, 'div': words.div,
	        '^': words.pow, '**': words.pow, 'pow': words.pow,
	        '.': words.dot, 'dot': words.dot,
	        '!': words.not_, 'not': words.not_,
	        'dup': words.dup, 'swap': words.swap, 'over': words.over,
	        'pop': words.pop, 'drop': words.pop, 'rot': words.rot,
	        '(S)': words.print_stack, '(W)': words.print_words,
	        'nop': words.nop, '(W-L)': words.print_word_list,
	        'if': words.if_, 'then': words.nop, 'else': words.nop,
	        'exit': words.exit, 'return': words.return_,
	       }

header = 'Déjà Vu\x00 Byte Code v'
def run(bctext):
	env = Env()
	if not bctext.startswith(header):
		bctext = dejac.compile(bctext)
	ver = bctext[len(header):len(header)+3]
	if ver < curver:
		#compat?
		pass
	elif ver > curver:
		raise DejaVuVersionError("byte code version (%s) newer than vm version (%s)" %(ver,curver))
	env.run(bctext[len(header)+4:])
	if options.interactive:
		interactive(env)

def interactive(env=None):
	env = env or Env()
	context = dejac.Context()
	while True:
		#sys.stdout.write(ps1)
		context.clear()
		try:
			context.parse_line(raw_input(ps1))
			while context.expected_indentation() > 0:
				#sys.stdout.write(ps2)
				input = raw_input(ps2)
				if not input:
					break
				context.parse_line(input)
		except dejac.DejaVuCompilationError as e:
			print(e)
		else:
			try:
				env.run(context.bytecode()[len(header)+4:])
			except DejaVuRunTimeError as e:
				print(e)

parser = OptionParser(prog = 'deja', usage = '%prog [options] file',
                      version = '%prog 0.0',
                      description = u'Déjà Vu is a general purpose '
                                     'stack-based programming language.')
parser.add_option("-i", "--interactive", action = 'store_true',
                  default = False, help="launch an interactive session after running the supplied files")
parser.add_option("-t", dest="total", action = 'store_true',
                  default = False, help="show the total of all rolls")
parser.add_option("-l", dest="lowest", action = 'store_true',
                  default = False, help="show the lowest of each roll")
parser.add_option("-s", dest="sort", action = 'store_true',
                  default = False, help="sort the results of each roll"
                                        "(from lowest to highest)")
parser.add_option("-S", "--separator", dest="separator", default = 'nl',
				metavar = 'SEP',
				#type = 'choice', choices=['null', 'nl'],
				help="change the separator (use 'null' for a null character and 'nl' for a newline, anything else is literal separator) (default: %default)")
(options, args) = parser.parse_args()
if not len(args):
	interactive()
else:
	if args[0] == '-':
		f = sys.stdin
	else:
		f = open(args[0])
	try:
		run(f.read())
	except DejaVuRunTimeError as e:
		print(e)
	if options.interactive:
		interactive()

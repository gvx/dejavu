#!/usr/bin/env python
#encoding: utf-8
from __future__ import print_function
import dejac
import deja
import sys

shortcodes = {'word': 'push word',
              'ident': 'push ident',
              'num': 'push number',
              'func': 'push function',
              'jz': 'jmp if zero',
              'jnz': 'jmp if not zero',
              'jmp': 'jmp',
              'line': 'line',}
shortcodename = {}
for k in shortcodes:
	shortcodename[shortcodes[k]] = k
address_codes = set(('JZ', 'JNZ', 'FUNC', 'JMP'))

args = {'word': str, 'ident': str, 'num': int, 'func': int,
        'jz': int, 'jnz': int, 'jmp': int}
funcs = {str: deja.Env.readstr, int: deja.Env.readnum}

def dis_asm(bytecode): #disassembler
	bytecode = bytecode[bytecode.find('\n')+1:]
	index = 0
	acc = []
	ref = {}
	refr = {}
	labels = {}
	lacc = 1
	while index < len(bytecode):
		ref[len(acc)] = index
		refr[index] = len(acc)
		d = shortcodename[dejac.bytecodename[bytecode[index]]]
		#print(d, index)
		if d == 'line':
			n, index = deja.Env.readnum(bytecode, index+1)
			line, index = deja.Env.readstr(bytecode, index)
			acc.append(('LINE',n,line))
		else:
			val, index = funcs[args[d]](bytecode, index+1)
			acc.append((d.upper(),val))
	ref[len(acc)] = index
	refr[index] = len(acc)
	print(ref, file=sys.stderr)
	print(refr, file=sys.stderr)
	print([(x, refr[x]) for x in refr if 40 <= x <= 50], file=sys.stderr)
	for i in range(len(acc)):
		if acc[i][0] in address_codes:
			j = acc[i][1] + (acc[i][0] != 'FUNC' and ref[i] or 0)
			#print(ref[i], ref[i]+acc[i][1], (ref[i]+acc[i][1]) in refr and refr[ref[i]+acc[i][1]], acc[i], i, file=sys.stderr)
			lid = i + refr[j]
			if lid not in labels:
				lbl = 'label' + str(lacc)
				labels[lid] = lbl
			else:
				lbl = labels[lid]
			lacc += 1
			acc[i] = acc[i][0], lbl
	for i in range(len(acc)):
		#if i in labels:
		#	acc[i] = (labels[i] + ':', acc[i][0]), acc[i][1]
		acc[i] = ' '.join(str(x) for x in acc[i])
	return '\n'.join(acc)+'\n'

def asm(assembler): #assembler
	pass

if __name__ == '__main__':
	text = sys.stdin.read()
	sys.stdout.write(
	(text.startswith('Déjà Vu') and dis_asm or asm)(text)
	)

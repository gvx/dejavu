#!/usr/bin/env python
#encoding: utf-8
import dejac
import sys

def dis_asm(bytecode): #disassembler
	pass

def asm(assembler): #assembler
	pass

if __name__ == '__main__':
	text = sys.stdin.read()
	sys.stdout.write((text.startswith('Déjà Vu') and dis_asm or asm)(text))

def equals(env):
	env.push(env.pop() == env.pop() and 1 or 0)

def not_(env):
	env.push(not env.pop() and 1 or 0)

def less(env):
	env.push(env.pop() >= env.pop() and 1 or 0)

def more(env):
	env.push(env.pop() <= env.pop() and 1 or 0)

def set(env):
	tmp = env.pop()
	tmp2 = env.pop()
	env.set(tmp, tmp2)

def get(env):
	env.push(env.get(env.pop()))

def add(env):
	env.push(env.pop() + env.pop())

def sub(env):
	env.push(-env.pop() + env.pop())

def mul(env):
	env.push(env.pop() * env.pop())

def pow(env):
	env.push(env.pop() ** env.pop())

def div(env):
	tmp = env.pop()
	env.push(env.pop() / tmp)

def dot(env):
	print(env.pop())

def call(env):
	env.call(env.pop())

def dup(env):
	tmp = env.pop()
	env.push(tmp)
	env.push(tmp)

def swap(env):
	a = env.pop()
	b = env.pop()
	env.push(a)
	env.push(b)

def pop(env):
	env.pop()

def over(env):
	b = env.pop()
	a = env.pop()
	env.push(a)
	env.push(b)
	env.push(a)

def rot(env):
	a = env.pop() #abc
	b = env.pop() #^top
	c = env.pop()
	print(a,b,c,env.stack)
	env.push(b) #cab
	env.push(a) #^top
	env.push(c)

def print_stack(env):
	print(', '.join(str(x) for x in env.stack))

def prstr(obj):
	if callable(obj):
		return '(Function)'
	return str(obj)

def print_words(env):
	print('\n'.join(str(k)+': '+prstr(env.idents[k]) for k in env.idents))

def print_word_list(env):
	print(', '.join(str(k) for k in env.idents))

def nop(env):
	pass

def if_(env):
	a = env.pop()
	b = env.pop()
	c = env.pop()
	if a:
		env.push(b)
	else:
		env.push(c)

def exit(env):
	env.exit()

def return_(env):
	env.returnstack.pop()

def alias(env):
	tmp = env.pop()
	tmp2 = env.get(env.pop())
	env.set(tmp, tmp2)

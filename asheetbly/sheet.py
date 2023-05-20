import csv, re, random
from string import ascii_uppercase as ALPHABET

A1_NOTATION = re.compile("^([A-Za-z]+)([0-9]+)$")

class InvalidA1Notation(Exception):
	"""Invalid A1 notation given."""
	pass

class InvalidOpcode(Exception):
	"""Invalid opcode given."""
	pass

class ArithmeticError(Exception):
	"""Error while performing arithmetic."""
	pass

class InvalidArgument(Exception):
	"""Invalid argument given."""
	pass

def _letters_to_numbers(letters):
	n = 0
	for c in letters:
		tmp = ALPHABET.index(c.upper())+1
		n = n*26+tmp
	return n

def _numbers_to_letters(numbers):
	s=""
	q,r = divmod(numbers,len(ALPHABET))
	if r==0:
		q=q-1
		r=26
	if q==0:
		return ALPHABET[r-1]
	elif q<=len(ALPHABET):
		return ALPHABET[q-1]+ALPHABET[r-1]
	else:
		return _numbers_to_letters(q)+ALPHABET[r-1]

def _safe_float(n):
	try:
		return float(n)
	except:
		return None

class Stack:
	"""A stack, with builtin underflow protection."""
	def __init__(self,values=None):
		self.values=values or []
		self.frames=[]

	def push(self,value):
		"""Push a value onto the stack."""
		self.values.append(value)

	def pop(self):
		"""Pop a value from the stack, enforcing frames if necessary."""
		if self.frames: # need to assure we don't underflow
			if len(self.values)<=self.frames[-1]:
				raise IndexError("pop from empty list")
		return self.values.pop(-1)

	def popn(self,n):
		if self.frames: # need to assure we don't underflow
			assert (len(self.values)-n+1)>self.frames[-1], "Stack underflow!"
		assert len(self.values)>=n, "Stack underflow!"
		ret = self.values[-n:]
		self.values[-n:]=[]
		return ret

	def push_frame(self,args=None):
		if not args: args=0
		frametop = len(self.values)-args
		if self.frames:
			assert frametop>=self.frames[-1],"Frame overflow!"
		else:
			assert frametop>=0,"Frame overflow!"
		self.frames.append(len(self.values)-args)

	def pop_frame(self):
		if self.frames: self.frames.pop()

	def peek(self,n):
		index=len(self.values)-n
		if self.frames:
			if index<=self.frames[1]: raise IndexError()
		if index<0: raise IndexError()
		return self.values[index]

class Sheet:
	"""An asheetbly sheet. Contains code."""
	def __init__(self,values=None):
		self.values=values if values else {}

	@staticmethod
	def a1_to_index(a1):
		"""Converts A1 syntax into (column, row) index."""
		if (m:=A1_NOTATION.match(a1)):
			letters, numbers = m.groups()
			return _letters_to_numbers(letters), int(numbers)
		else:
			raise InvalidA1Notation(a1)

	@staticmethod
	def index_to_a1(index):
		"""Converts (column, row) index into A1 syntax."""
		assert len(index)==2 and all([type(x)==int and x>0 for x in index]), f"Invalid index {index!r}!"
		return _numbers_to_letters(index[0])+str(index[1])

	def interpret_value(self,val):
		"""Interprets floats/ints as floats and strings as strings."""
		val=str(val)
		if (n:=_safe_float(val)):
			return n
		return val

	def read(self,index,default=''):
		"""Reads the value at index, defaulting to default."""
		return self.interpret_value(self.values.get(tuple(index),default))

	def write(self,index,value):
		"""Writes value at index."""
		self.values[tuple(index)]=self.interpret_value(value)

	def load_csv(self,csvfile,dialect="excel",**fmtparams):
		"""Loads the CSV file into the Sheet. Accepts anything that csv.reader would accept."""
		rows = csv.reader(csvfile,dialect,**fmtparams)
		rown=1
		for row in rows:
			coln=1
			for col in row:
				self.write((coln,rown),col)
				coln+=1
			rown+=1

class Interpreter:
	def __init__(self,sheet,start=None):
		self.sheet=sheet
		if start is None: start=[1,1]
		if type(start)==str: start=Sheet.a1_to_index(start)
		self._start=start
		self.reset()

	def reset(self):
		self.ip=list(self._start)
		self.stack=Stack()
		self.cond=False
		self.ret_stack=[]

	def run(self,start=None):
		"""Runs the asheetbly program. If start is not given, assumes A1."""
		while True:
			opcode = self.sheet.read(self.ip,"HALT")
			if opcode=="HALT" or type(opcode)!=str:
				return
			method = getattr(self,"do_"+opcode.upper())
			if not method:
				raise InvalidOpcode(opcode.upper())
			if not method(self.ip,self.stack):
				self.ip[1]+=1

	@staticmethod
	def argument(index,n):
		"""Gets the index of the n-th argument to the instruction at index."""
		assert len(index)==2 and all([type(x)==int and x>0 for x in index]), f"Invalid index {index!r}!"
		return index[0]+n,index[1]

	# Memory

	def do_LOAD_CELL(self,ip,stack):
		address = Sheet.a1_to_index(self.sheet.read(self.argument(ip,1)))
		value = self.sheet.read(address)
		stack.push(value)

	def do_STORE_CELL(self,ip,stack):
		address = Sheet.a1_to_index(self.sheet.read(self.argument(ip,1)))
		value = stack.pop()
		self.sheet.write(address,value)

	# Stack operations

	def do_DROP(self,ip,stack):
		stack.pop()

	def do_DUP(self,ip,stack):
		stack.push(stack.peek(1))

	def do_OVER(self,ip,stack):
		stack.push(stack.peek(2))

	def do_SWAP(self,ip,stack):
		for item in stack.popn(2)[::-1]:
			stack.push(item)

	# Arithmetic

	def _binary_arithmetic_check(self,stack):
		items = stack.popn(2)
		if not all([type(item)==float for item in items]): raise ArithmeticError(f"Attempt to perform arithmetic on strings (items: {items!r})")
		return items

	def do_ADD(self,ip,stack):
		item1,item2 = self._binary_arithmetic_check(stack)
		stack.push(item1+item2)

	def do_SUB(self,ip,stack):
		item1,item2 = self._binary_arithmetic_check(stack)
		stack.push(item1-item2)

	def do_MULT(self,ip,stack):
		item1,item2 = self._binary_arithmetic_check(stack)
		stack.push(item1*item2)

	def do_DIV(self,ip,stack):
		item1,item2 = self._binary_arithmetic_check(stack)
		stack.push(item1/item2)

	def do_FDIV(self,ip,stack):
		item1,item2 = self._binary_arithmetic_check(stack)
		stack.push(item1/item2)

	def do_MOD(self,ip,stack):
		item1,item2 = self._binary_arithmetic_check(stack)
		stack.push(item1%item2)

	# String operations

	def do_UPPER(self,ip,stack):
		stack.push(str(stack.pop()).upper())

	def do_LOWER(self,ip,stack):
		stack.push(str(stack.pop()).lower())

	def do_CONCAT(self,ip,stack):
		item1,item2 = map(str,stack.popn(2))
		stack.push(self.sheet.interpret_value(item1+item2))

	# I/O Operations

	def do_IN(self,ip,stack):
		prompt=self.sheet.read(self.argument(ip,1)).rstrip()
		stack.push(self.sheet.interpret_value(input(prompt+" ")))

	def do_OUT(self,ip,stack):
		print(stack.pop())

	# Control Flow

	def do_TEST(self,ip,stack):
		self.cond=(stack.peek(1)==0)

	def do_COMPARE(self,ip,stack):
		address = self.sheet.read(self.argument(ip,1))
		try:
			address = self.sheet.a1_to_index(address)
			value = self.sheet.read(address)
			self.cond=(stack.peek(1)==value)
		except:
			self.cond=(stack.peek(2)==stack.peek(1))

	def do_LT(self,ip,stack):
		address = self.sheet.read(self.argument(ip,1))
		try:
			address = self.sheet.a1_to_index(address)
			value = self.sheet.read(address)
			self.cond=(stack.peek(1)<value)
		except:
			self.cond=(stack.peek(2)<stack.peek(1))

	def do_GT(self,ip,stack):
		address = self.sheet.read(self.argument(ip,1))
		try:
			address = self.sheet.a1_to_index(address)
			value = self.sheet.read(address)
			self.cond=(stack.peek(1)>value)
		except:
			self.cond=(stack.peek(2)>stack.peek(1))

	def do_INVERT_COND(self,ip,stack):
		self.cond=not self.cond

	def do_JUMP(self,ip,stack):
		address = self.sheet.a1_to_index(self.sheet.read(self.argument(ip,1)))
		self.ip = list(address)
		return True # don't auto-increment

	def do_JUMP_IF(self,ip,stack):
		if self.cond: return self.do_JUMP(ip,stack)

	def do_CALL(self,ip,stack):
		address = self.sheet.a1_to_index(self.sheet.read(self.argument(ip,1)))
		args = self.sheet.read(self.argument(ip,2),0)
		if type(args)==str: args=0
		self.stack.push_frame(args)
		self.ret_stack.append(self.ip)
		self.ip = list(address)
		return True # don't auto-increment

	def do_CALL_IF(self,ip,stack):
		if self.cond: return self.do_CALL(ip,stack)

	def do_RETURN(self,ip,stack):
		self.ip = self.ret_stack.pop()
		self.stack.pop_frame()
		# let auto-increment happen, since the IP we pushed was the CALL instruction

	# Random Number Generation

	def do_RAND(self,ip,stack):
		m = self.sheet.read(self.argument(ip,1),0)
		n = self.sheet.read(self.argument(ip,2),1)
		if type(m)!=float: m=0
		if type(n)!=float: n=1
		if m==0 and n==1:
			stack.push(random.random())
		else:
			stack.push(random.uniform(m,n))

	def do_RANDINT(self,ip,stack):
		m = self.sheet.read(self.argument(ip,1))
		n = self.sheet.read(self.argument(ip,2))
		if type(m)!=float: raise InvalidArgument(f"Argument #1 to RANDINT must be number (is {m!r}).")
		m=int(m)
		if type(n)!=float: n=None
		else: n=int(n)
		if m and not n:
			n=m
			m=1
		stack.push(random.randint(m,n))

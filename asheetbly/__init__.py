from asheetbly.sheet import Sheet, Interpreter

def run(file):
	if type(file)==str:
		with open(file) as f:
			file=f.readlines()
	s = Sheet()
	s.load_csv(file)
	i = Interpreter(s)
	i.run()

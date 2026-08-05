import re, sys, string

debug = False
symbol_table = { }
tokens = [ ]


#  Expression class and its subclasses
class Expression( object ):
	def __str__(self):
		return ""

class BinaryExpr( Expression ):
	def __init__(self, op, left, right):
		self.op = op
		self.left = left
		self.right = right

	def __str__(self):
		return str(self.op) + " " + str(self.left) + " " + str(self.right)

class Number( Expression ):
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return str(self.value)

class Identifier( Expression ):
	def __init__(self, name):
		self.name = name

	def __str__(self):
		return str(self.name)

class AssignStmt( Expression ):
	def __init__(self, name, expr):
		self.name = name
		self.expr = expr

	def __str__(self):
		return "= " + str(self.name) + " " + str(self.expr)

class PrintStmt( Expression ):
	def __init__(self, expr):
		self.expr = expr

	def __str__(self):
		return "print " + str(self.expr)

class IfStmt( Expression ):
	def __init__(self, cond, body, elsebody=None):
		self.cond = cond
		self.body = body
		self.elsebody = elsebody

	def __str__(self):
		# "if <cond>\n<body lines>\nelse\n<elsebody lines>\nendif"
		# 'else' and 'endif' always appear regardless of whether there is an else body
		s = "if " + str(self.cond) + "\n"
		s += str(self.body) + "\n"
		s += "else\n"
		if self.elsebody:
			s += str(self.elsebody) + "\n"
		s += "endif"
		return s

class WhileStmt( Expression ):
	def __init__(self, cond, body):
		self.cond = cond
		self.body = body

	def __str__(self):
		return "while " + str(self.cond) + "\n" + str(self.body) + "\nendwhile"

class Block( Expression ):
	def __init__(self, stmts):
		self.stmts = stmts

	def __str__(self):
		return "\n".join(str(s) for s in self.stmts)


def error( msg ):
	sys.exit(msg)


def match(matchtok):
	tok = tokens.peek( )
	if (tok != matchtok): error("Expecting " + matchtok + " but got " + str(tok))
	tokens.next( )
	return tok


def factor( ):
	"""factor = number | identifier | '(' expression ')'"""

	tok = tokens.peek( )
	if debug: print("Factor: ", tok)
	if tok is None:
		error("Unexpected end of input in factor")
	if re.match(Lexer.number, tok):
		expr = Number(tok)
		tokens.next( )
		return expr
	if re.match(Lexer.identifier, tok):
		expr = Identifier(tok)
		tokens.next( )
		return expr
	if tok == "(":
		tokens.next( )
		expr = addExpr( )
		match(")")
		return expr
	error("Invalid operand: " + str(tok))


def term( ):
	"""term = factor { ('*' | '/') factor }"""

	tok = tokens.peek( )
	if debug: print("Term: ", tok)
	left = factor( )
	tok = tokens.peek( )
	while tok == "*" or tok == "/":
		tokens.next()
		right = factor( )
		left = BinaryExpr(tok, left, right)
		tok = tokens.peek( )
	return left


def addExpr( ):
	"""addExpr = term { ('+' | '-') term }"""

	tok = tokens.peek( )
	if debug: print("addExpr: ", tok)
	left = term( )
	tok = tokens.peek( )
	while tok == "+" or tok == "-":
		tokens.next()
		right = term( )
		left = BinaryExpr(tok, left, right)
		tok = tokens.peek( )
	return left


def relExpr( ):
	"""relExpr = addExpr [ relop addExpr ]"""

	tok = tokens.peek( )
	if debug: print("relExpr: ", tok)
	left = addExpr( )
	tok = tokens.peek( )
	if tok in ("==", "!=", "<", "<=", ">", ">="):
		tokens.next()
		right = addExpr( )
		return BinaryExpr(tok, left, right)
	return left


def parseBlock( ):
	"""block = '@' { statement } '~'
	   '@' signals an indent, '~' signals an undent (added by mklines).
	   The header line (if/while/else) ends with ':;' before the '@', so skip them.
	"""
	if tokens.peek( ) == ":": tokens.next( )
	if tokens.peek( ) == ";": tokens.next( )
	match("@")
	stmts = []
	tok = tokens.peek( )
	while tok is not None and tok != "~":
		stmt = parseStmt( )
		stmts.append(stmt)
		tok = tokens.peek( )
	match("~")
	return Block(stmts)


def parseStmt( ):
	"""
	statement = assignStmt | printStmt | ifStmt | whileStmt | exprStmt

	assignStmt  ->  identifier '=' expression ';'
	printStmt   ->  'print' expression ';'
	ifStmt      ->  'if' relExpr block [ 'else' block ]
	whileStmt   ->  'while' relExpr block
	exprStmt    ->  expression ';'
	"""

	tok = tokens.peek( )
	if debug: print("parseStmt: ", tok)

	# if statement
	if tok == "if":
		tokens.next( )
		cond = relExpr( )
		body = parseBlock( )
		elsebody = None
		if tokens.peek( ) == "else":
			tokens.next( )
			elsebody = parseBlock( )
		return IfStmt(cond, body, elsebody)

	# while statement
	if tok == "while":
		tokens.next( )
		cond = relExpr( )
		body = parseBlock( )
		return WhileStmt(cond, body)

	# print statement
	if tok == "print":
		tokens.next( )
		expr = relExpr( )
		match(";")
		return PrintStmt(expr)

	# assignment:  identifier = expr ;
	if tok is not None and re.match(Lexer.identifier, tok):
		next_tok = tokens.tokens[tokens.position + 1] if tokens.position + 1 < len(tokens.tokens) else None
		if next_tok == "=":
			name = tok
			tokens.next( )  # consume identifier
			tokens.next( )  # consume '='
			expr = relExpr( )
			match(";")
			return AssignStmt(name, expr)

	# fallthrough: expression statement
	expr = relExpr( )
	match(";")
	return expr


def parseStmtList( ):
	"""parseStmtList = { statement }"""
	stmts = []
	tok = tokens.peek( )
	while tok is not None:
		ast = parseStmt( )
		print(str(ast))
		stmts.append(ast)
		tok = tokens.peek( )
	return stmts


def parse( text ):
	global tokens
	tokens = Lexer( text )
	stmtlist = parseStmtList( )
	return stmtlist


# Lexer class
class Lexer:

	special    = r"\(|\)|\[|\]|,|:|;|@|~|;|\$"
	relational = r"<=?|>=?|==?|!="
	arithmetic = r"\+|\-|\*|\/"
	string     = r"'[^']*'" + "|" + r'"[^"]*"'
	number     = r"\-?\d+(?:\.\d+)?"
	literal    = string + "|" + number
	identifier = r"[a-zA-Z]\w*"
	lexRules   = literal + "|" + special + "|" + relational + "|" + arithmetic + "|" + identifier

	def __init__( self, text ):
		self.tokens   = re.findall( Lexer.lexRules, text )
		self.position = 0
		self.indent   = [ 0 ]

	def peek( self ):
		if self.position < len(self.tokens):
			return self.tokens[ self.position ]
		else:
			return None

	def next( self ):
		self.position = self.position + 1
		return self.peek( )

	def __str__( self ):
		return "<Lexer at " + str(self.position) + " in " + str(self.tokens) + ">"


def chkIndent(line):
	ct = 0
	for ch in line:
		if ch != " ": return ct
		ct += 1
	return ct


def delComment(line):
	pos = line.find("#")
	if pos > -1:
		line = line[0:pos]
		line = line.rstrip()
	return line


def mklines(filename):
	inn   = open(filename, "r")
	lines = [ ]
	pos   = [0]
	ct    = 0
	for line in inn:
		ct  += 1
		line = line.rstrip( ) + ";"
		line = delComment(line)
		if len(line) == 0 or line == ";": continue
		indent = chkIndent(line)
		line   = line.lstrip( )
		if indent > pos[-1]:
			pos.append(indent)
			line = '@' + line
		elif indent < pos[-1]:
			while indent < pos[-1]:
				del(pos[-1])
				line = '~' + line
		print(ct, "\t", line)
		lines.append(line)
	undent = ""
	for i in pos[1:]:
		undent += "~"
	lines.append(undent)
	return lines


def main():
	"""main program for testing"""
	global debug
	ct = 0
	for opt in sys.argv[1:]:
		if opt[0] != "-": break
		ct = ct + 1
		if opt == "-d": debug = True
	if len(sys.argv) < 2 + ct:
		print("Usage:  %s filename" % sys.argv[0])
		return
	parse("".join(mklines(sys.argv[1 + ct])))
	return


main()
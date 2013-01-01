import collections
import os.path
import re


TOKEN_PATTERNS = (
    ('comment', r'/\*([^*]|\*+[^*/])*\*+/'),
    ('symbol', '&&|[#{()!<.>;*,}/\[\]]'),
    ('word', '[a-zA-Z_][a-zA-Z0-9_]*'),
    ('string', r'"([^\\"]|\\.)*"'),
    ('integer', '[0-9]+'),
    )

TOKEN_REGEXP = re.compile('|'.join('(?P<{0}>{1})'.format(name, pattern)
                                   for name, pattern in TOKEN_PATTERNS))
NEWLINE_REGEXP = re.compile('\n')


Token = collections.namedtuple('Token', ['type', 'str', 'line'])


def tokenize_file(filename):
    with open(filename, 'r') as f:
        contents = f.read()
    line_num = 1
    pos = 0
    for m in TOKEN_REGEXP.finditer(contents):
        for _ in NEWLINE_REGEXP.finditer(contents[pos:m.start()]):
            line_num += 1
        pos = m.start()
        for name, pattern in TOKEN_PATTERNS:
            if m.group(name):
                yield Token(name, m.group(name), line_num)
                break


class Parser(object):
    def __init__(self, filename):
        self.tokens = list(tokenize_file(filename))
        self.pos = 0
        self.functions = {}

    def fail(self):
        raise Exception(
            'Parse failure.  Remaining tokens: {0!r}'.format(
                self.tokens[self.pos:]))

    def is_at_end(self):
        return self.pos >= len(self.tokens)

    def peek(self, index = 0):
        index += self.pos
        if index >= len(self.tokens):
            return Token('end', '', -1)
        else:
            return self.tokens[index]

    def skip(self, count = 1):
        self.pos += count

    def skip_line(self):
        line_num = self.peek().line
        if line_num < 0:
            return
        while self.peek().line == line_num:
            self.skip()

    def skip_to(self, target):
        while True:
            if self.is_at_end():
                self.fail()
            if self.peek().str == target:
                self.skip()
                return
            if self.peek().type == 'symbol':
                if self.peek().str == '(':
                    self.skip()
                    self.skip_to(')')
                    continue
                elif self.peek().str == '[':
                    self.skip()
                    self.skip_to(']')
                    continue
                elif self.peek().str == '{':
                    self.skip()
                    self.skip_to('}')
                    continue
            self.skip()

    def parse_entity(self):
        if self.peek().type == 'comment':
            self.skip()
        elif self.peek().str == '#':
            self.skip_line()
        elif self.peek(0).str == 'extern' and self.peek(1).str == '"C"' \
                and self.peek(2).str == '{':
            self.skip(3)
            self.parse_brace_contents()
        elif self.peek().str == 'typedef':
            self.skip_to(';')
        elif self.peek().str in ('GLAPI', 'GL_API', 'GL_APICALL'):
            self.parse_function()
        else:
            self.fail()

    def parse_function(self):
        # Consume return type, ignoring modifiers
        return_type_tokens = []
        # Consume initial modifiers
        while True:
            if self.peek().str in ('GLAPI', 'GL_API', 'GL_APICALL'):
                pass
            elif self.peek().str == 'const':
                return_type_tokens.append('const')
            else:
                break
            self.skip()
        # Consume return type
        if self.peek().type != 'word':
            self.fail()
        return_type = self.peek().str
        self.skip()
        # Consume additional modifiers
        while True:
            if self.peek().str in ('APIENTRY', 'GL_APIENTRY'):
                pass
            elif self.peek().str == '*':
                return_type_tokens.append('*')
            else:
                break
            self.skip()
        # Consume function name
        if self.peek().type != 'word':
            self.fail()
        function_name = self.peek().str
        self.skip()
        # Skip args
        if self.peek().str != '(':
            self.fail()
        self.skip()
        self.skip_to(')')
        if self.peek().str != ';':
            self.fail()
        self.skip()
        self.functions[function_name] = {}

    def parse_brace_contents(self):
        while True:
            if self.is_at_end():
                return
            if self.peek().str == '}':
                self.skip()
                return
            self.parse_entity()

    def parse_all(self):
        while True:
            if self.is_at_end():
                return
            self.parse_entity()


def parse_c_file(filename):
    parser = Parser(filename)
    parser.parse_all()
    return parser.functions

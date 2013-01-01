import hashcomments
import re


INITIAL_DECLARATION_REGEXP = re.compile('^[a-z-]+:')
SIGNATURE_REGEXP = re.compile(
    r'^(?P<name>[A-Za-z0-9_]+)\((?P<params>[A-Za-z0-9_, ]*)\)$')


# Parse a gl.spec file
def parse_spec_file(filename):
    functions = {}
    with open(filename, 'r') as f:
        for func in group_functions(f):
            function_name, param_names = parse_signature(func[0])
            if function_name in functions:
                raise Exception(
                    'Function {0!r} seen twice'.format(function_name))
            properties = {}
            for line in func[1:]:
                keyvalue = line.lstrip().split(None, 1)
                if len(keyvalue) == 2:
                    key, value = keyvalue
                else:
                    key = keyvalue[0]
                    value = ''
                if key not in properties:
                    properties[key] = []
                properties[key].append(value)
            functions[function_name] = {
                'param_names': param_names, 'properties': properties}
    return functions


def group_functions(lines):
    """Yield lists of lines, where each list constitutes a single
    function declaration.
    """
    current_function = []
    for line in hashcomments.filter_out_comments(lines):
        if INITIAL_DECLARATION_REGEXP.match(line):
            continue
        if not line[0].isspace() and current_function:
            yield current_function
            current_function = []
        current_function.append(line)
    if current_function:
        yield current_function


def parse_signature(sig):
    m = SIGNATURE_REGEXP.match(sig)
    name = m.group('name')
    params = m.group('params')
    if params:
        param_names = [p.strip() for p in m.group('params').split(',')]
    else:
        param_names = []
    return name, param_names

import xml.etree.ElementTree as etree


# Categories that appear in Mesa XML but shouldn't be added to the
# master database, and why.
MESA_EXTRA_CATEGORIES = set([
        # This extension is supported by Mesa, but it's undocumented,
        # and the one function it contains
        # (glBlendEquationSeparateATI) does not exist in the official
        # glext.h header, so it seems prudent to leave it out.
        'GL_ATI_blend_equation_separate',

        # This extension is described in Mesa's XML files, but it's
        # not implemented by Mesa, and the only documentation for it
        # that exists for it is marked as "obsolete".
        'GL_MESA_shader_debug',
        ])


class Reader(object):
    def __init__(self, filename):
        self.tree = etree.parse(filename)
        self.functions = {}

    def process_all(self):
        if self.tree.getroot().tag != 'OpenGLAPI':
            raise Exception(
                'Unexpected root element {0!r}; expected {1!r}'.format(
                    tree.getroot().tag, 'OpenGLAPI'))
        self.process_OpenGLAPI(self.tree.getroot())

    def process_OpenGLAPI(self, elem):
        for child in elem:
            if not isinstance(child, etree.Element):
                continue
            if child.tag == 'category':
                self.process_category(child)

    def process_category(self, elem):
        category_name = elem.attrib['name']
        if category_name in MESA_EXTRA_CATEGORIES:
            return
        window_system = elem.attrib.get('window_system', None)
        if window_system is not None:
            # We don't worry about windowsystem-specific functions.
            return
        for child in elem:
            if not isinstance(child, etree.Element):
                continue
            if child.tag == 'function':
                self.process_function(child)

    def process_function(self, elem):
        name = elem.attrib['name']
        if name in self.functions:
            raise Exception('Duplicate function {0!r}'.format(name))
        self.functions[name] = {}

def parse_xml_file(filename):
    reader = Reader(filename)
    reader.process_all()
    return reader.functions

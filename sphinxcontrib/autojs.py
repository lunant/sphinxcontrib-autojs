import os
import os.path
import re
from docutils import nodes
from docutils.statemachine import ViewList
from pygments.lexers import JavascriptLexer, LEXERS
from pygments.token import *
from sphinx import addnodes
from sphinx.domains.javascript import *
from sphinx.util.compat import Directive
from sphinx.util.nodes import nested_parse_with_titles
from sphinx.ext.autodoc import members_option, bool_option, identity, ALL


# for docstrings
START = "/**"
END = "*/"
PROMPT = ">>> "
CONTINUED = "... "


def text_indent(indent, text):
    return re.compile("^", re.MULTILINE).sub(indent, text)


def text_outdent(indent, text):
    return re.compile("^" + re.escape(indent), re.MULTILINE).sub("", text)


class JavascriptConsoleLexer(JavascriptLexer):
    """For Javascript console output or doctests, such as:

    .. sourcecode:: jscon

        >>> var a = "foo";
        >>> a;
        foo
        >>> 1 / 0;
        Infinity
    """

    name = "Javascript console session"
    CONSOLE_RULES = [(r"(?:(?<=\n)|^)(>>>|\.\.\.)(?= )", Generic.Prompt),
                     # for popular Javascript frameworks
                     (r"\$|jQuery|MooTools|Class|Browser|Array|Function" \
                      r"String|Hash|Event|Element|JSON|Cookie|Fx|Request",
                      Name.Class)]
    EXCEPTIONS = ["Error", "KeyError", "HTTPError", "ReferenceError"]
    tokens = JavascriptLexer.tokens.copy()
    tokens["root"] = CONSOLE_RULES + tokens["root"][:]
    aliases = ["jscon"]
    mimetypes = ["text/x-javascript-doctest"]
    filenames = []
    alias_filenames = []

    def get_tokens_unprocessed(self, text):
        is_example = False
        is_output = False
        for item in JavascriptLexer.get_tokens_unprocessed(self, text):
            if item[1] is Generic.Prompt:
                is_example = True
                is_output = False
            elif is_example and item[2].endswith(u"\n"):
                is_example = False
                is_output = True
            elif is_output:
                item = item[0], Generic.Output, item[2]
            elif item[2] in self.EXCEPTIONS:
                item = item[0], Name.Exception, item[2]
            yield item


class JSClassmember(JSObject):

    doc_field_types = JSCallable.doc_field_types

    @property
    def has_arguments(self):
        return self.objtype.endswith("method")

    def handle_signature(self, sig, signode):
        if self.objtype in ("staticmethod", "attribute"):
            sig_prefix = "static "
            signode += addnodes.desc_annotation(sig_prefix, sig_prefix)
        sig = sig.split(".")[-1]
        names = super(JSClassmember, self).handle_signature(sig, signode)
        name_prefix = self.env.temp_data.get("js:class")
        if name_prefix:
            return self.make_prefix(name_prefix) + names[0], names[1]
        else:
            return names

    def make_prefix(self, name_prefix):
        if self.objtype == "method":
            name_prefix += ".prototype"
        return name_prefix + "."


# Holds a last signed class name
def before_js_constructor(self):
    super(JSConstructor, self).before_content()
    if self.names:
        self.env.temp_data['js:class'] = self.names[0][0]
JSConstructor.before_content = before_js_constructor

# Adds js:method directive and js:meth role
JavaScriptDomain.directives.update({"member": JSClassmember,
                                    "attribute": JSClassmember,
                                    "method": JSClassmember,
                                    "staticmethod": JSClassmember})
JavaScriptDomain.roles.update({"meth": JSXRefRole(fix_parens=True)})


class JavaScriptDocstring(object):

    def __init__(self, indent, body, name=None, sig=None, directive=None):
        self.indent = indent
        self.body = body
        self.name = name
        self.sig = sig
        self.directive = directive
        self._member_re = re.compile("^" + re.escape(self.name) + \
                                     "(?:\.prototype)?\.([^.]+)$")

    def guess_objtype(self, in_parent=True):
        if self.directive:
            return self.directive
        static = ".prototype." not in self.sig
        if "(" in self.sig and self.sig.endswith(")"):
            if not in_parent:
                return "function"
            elif static:
                return "staticmethod"
            else:
                return "method"
        elif not in_parent:
            return "data"
        elif static:
            return "attribute"
        else:
            return "member"

    def to_rst(self, docstrings=[], indent="", parent=None, is_member=None):
        rst = []
        in_parent = isinstance(parent, type(self))
        if self.sig:
            objtype = self.guess_objtype(in_parent=in_parent)
            sig = self.sig
            if in_parent:
                sig = parent._member_re.sub(r"\1", sig)
            subject = "\n%s.. js:%s:: %s\n" % (indent, objtype, sig)
            indent += "   "
            rst.append(subject)
        body = text_indent(indent, self.body)
        rst.append(body)
        try:
            if objtype == "class" or not objtype.endswith("method"):
                included = []
                members = self.find_members(docstrings, is_member)
                for i, mem in members:
                    rst.append(mem.to_rst(docstrings, indent, parent=self))
                    included.append(i)
                for i in reversed(included):
                    del docstrings[i]
        except NameError:
            pass
        return "\n".join(rst)

    def find_members(self, docstrings, is_member=None):
        _is_member = is_member
        def is_member(doc):
            if callable(_is_member) and not _is_member(doc):
                return False
            return self._member_re.match(doc.sig)
        for i, mem in enumerate(docstrings):
            if mem.directive in (None, "attribute") and is_member(mem):
                yield i, mem

    @classmethod
    def from_match(cls, match):
        interaction_re = re.compile(r"""
            \n\s*?\n
            (?P<codeblock> \s*?
                (?P<prompt> \>\>\>)
            )
        """, re.VERBOSE | re.MULTILINE)
        codeblock_re = re.compile(r"""
            ::\s*?\n\s*?\n
        """, re.VERBOSE | re.MULTILINE)
        try:
            indent = match.group("indent")
            name = match.group("name")
            sig = match.group("signature")
            directive = match.group("directive")
        except IndexError:
            name = sig = directive = None
            indent = ""
        body = text_outdent(indent, match.group("body"))
        body = interaction_re.sub("\n\n.. sourcecode:: jscon" \
                                  "\n\n\g<codeblock>", body)
        body = codeblock_re.sub(":\n\n.. sourcecode:: js\n\n", body)
        return cls(indent, body, name, sig, directive)


class JavaScriptDocument(object):

    _MODULE_DOCSTRING_RE = re.compile(r"""
        ^
        (?P<docprefix> /\*\*)
        \s*\n+
        (?P<body> .+?)
        \s*
        (?P<docsuffix> \*/)
    """, re.VERBOSE | re.MULTILINE | re.DOTALL)
    _DOCSTRING_RE = re.compile(r"""
        (?P<indent> [ ]*)
        (?P<docprefix> /\*\*)
        (?P<subject>
            (?P<directive>
                class|function|data|member|attribute|method|staticmethod
            )?
            :\s*
            (?P<signature>
                (?P<name> .+?)
                (?P<params> \(.*?\))?
            )
        )
        \s*\n+
        (?P<body> .+?)
        \s*
        (?P<docsuffix> \*/)
    """, re.VERBOSE | re.MULTILINE | re.DOTALL)

    def __init__(self, path):
        with open(path) as f:
            self.source = "".join(f.readlines())

    def get_description(self):
        match = self._MODULE_DOCSTRING_RE.match(self.source)
        if not match:
            raise ValueError("There is no docstring for the module.")
        return JavaScriptDocstring.from_match(match)

    def get_docstrings(self):
        matches = self._DOCSTRING_RE.finditer(self.source)
        if not matches:
            raise ValueError("There is no any named docstring.")
        for match in matches:
            yield JavaScriptDocstring.from_match(match)

    def auto_include_desc(self, rst, options):
        if not options.get("exclude-desc"):
            try:
                rst.append(self.get_description().to_rst())
            except ValueError:
                pass

    def auto_include_members(self, rst, options):
        members = options.get("members")
        compare = self._make_comparer(options.get("member-order"))
        docstrings = list(self.get_docstrings())
        docstrings.sort(cmp=compare)
        if members is not None:
            exclude_members = options.get("exclude-members", [])
            is_member = self._make_member_checker(members, exclude_members)
            for doc in docstrings:
                if is_member(doc):
                    rst.append(doc.to_rst(docstrings, is_member=is_member))
        else:
            for doc in docstrings:
                rst.append(doc.to_rst(docstrings))

    def _make_member_checker(self, members, exclude_members):
        __members__ = members
        def is_member(doc, members=None):
            if members is None:
                members = __members__
            if members is not exclude_members and \
               is_member(doc, exclude_members):
                return False
            elif members is ALL or doc.name in members:
                return True
            for mem in members:
                if doc.name.startswith(mem):
                    return True
            return False
        return is_member

    def _make_comparer(self, member_order):
        if not member_order or member_order == "alphabetical":
            return lambda d1, d2: cmp(d1.name, d2.name)
        elif member_order == "groupwise":
            order = ["class", "member", "attribute", "method", "staticmethod",
                     "data", "function"]
            def compare(d1, d2):
                return cmp(order.index(d1.guess_objtype()),
                           order.index(d2.guess_objtype())) or \
                       self._make_comparer(None)(d1, d2)
            return compare
        elif member_order == "bysource":
            return lambda d1, d2: 1

    def to_rst(self, options={}):
        rst = []
        self.auto_include_desc(rst, options)
        self.auto_include_members(rst, options)
        return "\n".join(rst)


class AutoJavaScript(Directive):
    """ Generate reStructuredText from JavaScript file.

    .. sourcecode:: rest

       DocTest.js internals
       --------------------

       .. autojs:: doctest.js
       .. autojs:: section.js
       .. autojs:: example.js
       .. autojs:: comment.js

    """

    required_arguments = 1
    option_spec = {"exclude-desc": bool_option,
                   "members": members_option,
                   "exclude-members": members_option,
                   "member-order": identity}

    def add_line(self, line):
        self.result.append(line, "<autojs>")

    def add_lines(self, lines):
        if isinstance(lines, basestring):
            lines = lines.split("\n")
        for line in lines:
            self.add_line(line)

    def run(self):
        self.result = ViewList()
        path = self.arguments[0]
        filename = os.path.basename(path)
        node = nodes.section()
        node.document = self.state.document
        self.add_lines(JavaScriptDocument(path).to_rst(self.options))
        nested_parse_with_titles(self.state, self.result, node)
        return node.children


def setup(app):
    app.add_directive('autojs', AutoJavaScript)
    app.add_lexer("jscon", JavascriptConsoleLexer())

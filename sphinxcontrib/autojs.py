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


__all__ = ["AutoJavaScript"]


START = "/**"
END = "*/"
PROMPT = ">>> "
CONTINUED = "... "


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


class JSClassmember(JSCallable):

    def handle_signature(self, sig, signode):
        if self.objtype in ("staticmethod", "attribute"):
            self.objtype = "staticmethod"
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


class JavaScriptDocument(object):

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
    _INTERACTION_RE = re.compile(r"""
        \n\s*?\n
        (?P<codeblock> \s*?
            (?P<prompt> \>\>\>)
        )
    """, re.VERBOSE | re.MULTILINE)

    def __init__(self, path):
        with open(path) as f:
            self.source = "".join(f.readlines())

    def _indent(self, indent, text):
        return re.compile("^", re.MULTILINE).sub(indent, text)

    def _unindent(self, indent, text):
        return re.compile("^" + re.escape(indent), re.MULTILINE).sub("", text)

    def to_rst(self, options={}):
        docs = []
        matches = self._DOCSTRING_RE.finditer(self.source)
        for match in matches:
            indent = match.group("indent")
            directive = match.group("directive")
            sig = match.group("signature")
            name = match.group("name")
            body = self._unindent(indent, match.group("body"))
            body = self._indent("   ", body)
            body = self._INTERACTION_RE.sub(
                "\n\n   .. sourcecode:: jscon\n\n\g<codeblock>", body
            )
            docs.append((sig, name, directive, body)) 
        rst = []
        doc_bodies = []
        members = options.get("members")
        for doc in docs:
            sig, name, directive, body = doc
            if members:
                if name not in members:
                    continue
                elif directive is None:
                    directive = self.get_objtype(sig, False)
            if directive is not None:
                subject = "\n.. js:%s:: %s\n\n" % (directive, sig)
                doc_bodies.append(subject + body)
            if directive == "class":
                for child in self.get_children(doc, docs):
                    doc_bodies.append(child)
        for body in doc_bodies:
            rst.append(body)
        with open("test.rst", "w") as f:
            print>>f, "\n".join(rst)
        return "\n".join(rst)

    def get_children(self, doc, docs, depth=1):
        sig, name, directive, body = doc
        classmember_re = re.compile(r"^" + name + "(\.prototype)?\.[^.]+$")
        members = (mem for mem in docs if mem[2] is None and \
                                          classmember_re.match(mem[0]))
        for mem in members:
            objtype = self.get_objtype(mem[0])
            indent = "   " * depth
            subject = "\n%s.. js:%s:: %s\n\n" % (indent, objtype, mem[0])
            body = self._indent(indent, mem[3])
            yield subject + body
            if not objtype.endswith("method"):
                for child in self.get_children((None, mem[0], objtype, mem[3]),
                                               docs, depth + 1):
                    yield child

    def get_objtype(self, sig, in_parent=True):
        static = ".prototype." not in sig
        if "(" in sig and sig.endswith(")"):
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


ALL = dict()
def members_option(arg):
    if arg is None:
        return ALL
    return [x.strip() for x in arg.split(',')]


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
    option_spec = {"members": members_option}

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


indent = "    "

def parse_numeric(s):
    a = [str()]
    for c in s:
        if c.isnumeric():
            a[-1] += c
        else:
            if a[-1]: a.append(str())
    if not a[-1]: a.pop(-1)
    return list(map(int, a))


class ASTBlock:
    def __init__(self):
        self.stype = str()
        self.addr = [-1, -1]
        self.parent = None

    def parse(self, s):
        w = s.split(" ")
        print(w) # shows that everything is ok
        self.stype = w[0].strip(":")
        self.addr = parse_numeric(w[-1])

    def set_parent(self, n):
        self.parent = n

    def __str__(self):
        return self.stype+" "+str(self.addr)

    def __repr__(self):
        return str(self)


class ASTNode(ASTBlock):
    def __init__(self):
        super().__init__()
        self.children = list()
        self.fields = list()

    def add_child(self, n):
        self.children.append(n)

    def add_field(self, f):
        self.fields.append(f)

    def __getitem__(self, i):
        return self.children[i]

    def __repr__(self):
        s = super().__repr__()
        return s + " ({0} children, {1} fields)".format(len(self.children),
                                                          len(self.fields))

class ASTField(ASTBlock):
    def __init__(self):
        super().__init__()
        self.text = str()

    def parse(self, s):
        super().parse(s)
        w = s.split(" ")
        self.text = " ".join(w[1:-1])

    def __str__(self):
        return self.stype+": "+self.text+" "+str(self.addr)

    def __repr__(self):
        return str(self)


def prepare_line(l):
    indent_level = len(l.split(indent))-1
    pure_line = l.lstrip(" ").strip("\n")
    return (indent_level, pure_line)


def parse_line(parent, l):
    if l.split(" ")[0].endswith(":"):
        f = ASTField()
        f.parse(l)
        parent.add_field(f)
        return f
    else:
        n = ASTNode()
        n.parse(l)
        parent.add_child(n)
        return n


class ASTree:
    def __init__(self):
        self.blocks = dict()
        self.root = None

    def __getitem__(self, addr):
        return self.blocks[addr]

    def _add_block(self, b):
        self.blocks[tuple(b.addr)] = b
    
    def add_root(self, n):
        self.root = n
        self._add_subtree(self.root)

    def _add_subtree(self, v):
        self._add_block(v)
        for f in v.fields: self._add_block(f)
        for c in v.children: self._add_subtree(c)

    def parse_file(self, fn):
        f = open(fn)
        self.root = ASTNode()
        hierarchy = [self.root]
        for l in f.readlines():
            level, pl = prepare_line(l)
            b = parse_line(hierarchy[level], pl)
            self._add_block(b)
            if type(b) == ASTNode:
                if len(hierarchy) > level + 1:
                    hierarchy[level+1] = b
                else:
                    hierarchy.append(b)
        self.root = self.root[0]

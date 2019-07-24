import os
indent = "    "

def parse_numeric(s):
    a = [str()]
    for c in s:
        if c.isnumeric():
            a[-1] += c
        else:
            if a[-1]: a.append(str())
    if not a[-1]: a.pop(-1)
    return tuple(map(int, a))


class ASTBlock:
    def __init__(self):
        self.stype = str()
        self.addr = (-1, -1)
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
        n.set_parent(self)
        self.children.append(n)

    def add_field(self, f):
        f.set_parent(self)
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


def address_in(child_a, parent_a):
    return (child_a[0] >= parent_a[0]) and (child_a[1] <= parent_a[1])


def name_of(node):
    return next(filter(lambda f: f.stype == 'SimpleName', node.fields)).text


def in_which(addr_list, addr):
     return next(filter(lambda a: in_address(addr, a), addr_list))


class ASTree:
    def __init__(self):
        self.blocks = dict()
        self.root = None
        self.classes = dict()
        self.methods = dict()

    def __getitem__(self, addr):
        return self.blocks[addr]

    def _add_block(self, b):
        self.blocks[b.addr] = b
        if b.stype == 'TYPE_DECLARATION_KIND':
            if b.text == 'class':
                self.classes[b.parent.addr] = b.parent
        if b.stype == 'MethodDeclaration':
            self.methods[b.addr] = b
    
    def add_root(self, n):
        self.root = n
        self._add_subtree(self.root)

    def _add_subtree(self, v):
        self._add_block(v)
        for f in v.fields: self._add_block(f)
        for c in v.children: self._add_subtree(c)

    def parse_file(self, fn):
        with open(os.path.expanduser(fn)) as f:
            self.parse_lines(f.readlines())

    def parse_lines(self, lines):
        self.root = ASTNode()
        hierarchy = [self.root]
        for l in lines:
            level, pl = prepare_line(l)
            b = parse_line(hierarchy[level], pl)
            self._add_block(b)
            if type(b) == ASTNode:
                if len(hierarchy) > level + 1:
                    hierarchy[level+1] = b
                else:
                    hierarchy.append(b)
        self.root = self.root[0]
    
    def in_which_class(self, node):
        return self.blocks[in_which(self.classes.keys(), node.addr)]

    def in_which_method(self, node):
        return self.blocks[in_which(self.methods.keys(), node.addr)]


class ASTDiff:
    def __init__(self, src=None, dest=None):
        self.a = src
        self.b = dest
        self.matches = list()
        self.actions = list()

    def load_json_file(self, fn):
        import json
        with open(os.path.expanduser(fn)) as f:
            d = json.loads(f.read())
            self.load_matches(d["matches"])
            self.load_actions(d["actions"])

    def load_all_files(self, a_fn, b_fn, diff_fn):
        self.a, self.b = ASTree(), ASTree()
        self.a.parse_file(a_fn)
        self.b.parse_file(b_fn)
        self.load_json_file(diff_fn)

    def load_matches(self, match_list):
        parse_addr = lambda s: parse_numeric(s.split(" ")[-1])
        for m in match_list:
            am_addr = parse_addr(m["src"])
            bm_addr = parse_addr(m["dest"])
            self.a[am_addr], self.b[bm_addr] # check
            self.matches.append((am_addr, bm_addr))

    def load_actions(self, action_list):
        for a in action_list:
            self.actions.append(DiffAction(a))
    
    def src2dest(self, src_a):
        return next(filter(lambda m: m[0] == src_a, self.matches))[1]
    
    def dest2src(self, dest_a):
        return next(filter(lambda m: m[1] == dest_a, self.matches))[0]
        
    def new_methods(self):
        ml = list()
        for ma, m in self.b.methods.items():
            try:
                self.dest2src(ma)
            except StopIteration:
                ml.append(m)
        return ml
    
    def removed_methods(self):
        ml = list()
        for ma, m in self.a.methods.items():
            try:
                self.src2dest(ma)
            except StopIteration:
                ml.append(m)
        return ml
    
    def updated_methods(self):
        ml = list()
        for a in self.actions:
            if a.stype == 'update-node':
                for ma, m in self.a.methods.items():
                    if m in ml: continue
                    if address_in(a.addr, ma): ml.append(m)
        return ml
    
    def actions_in_block(self, b):
        return filter(lambda a: address_in(a.addr, b.addr), self.actions)


class DiffAction:
    def __init__(self, data):
        self.raw = data
        self.stype = data['action']
        self.addr = parse_numeric(data['tree'].split(' ')[-1])
    
    def __repr__(self):
        return self.stype + " " + str(self.addr)

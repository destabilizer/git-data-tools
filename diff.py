ident = "    "

def parse_numeric(s):
    a = [str()]
    for c in s:
        if c.isnumeric():
            a[-1] += c
        else:
            if a[-1]: a.append(str())
    return list(map(int, a))

class ASTNode:
    def __init__(self):
        self.children = []
        self.parent = None
        self.stype = ""
        self.sattr = ""
        self.addr = [-1, -1]

    def parse_string(self, s):
        w = s.split(" ")
        if w[0].endswith(":"):
            self.stype = w[0].strip(":")
            self.sattr = " ".join(w[1:-1])
            self.addr = parse_numeric(w[-1])
        else:
            self.stype = w[0]
            self.addr = parse_numeric(w[-1])

    def set_parent(self, n):
        self.parent = n

    def add_child(self, n):
        self.children.append(n)

class ASTree:
    def __init__(self):
        self.nodes = list()
        self.addrs = dict()
        self.root = None

    def set_root(self, n):
        self.root = n

    def load_from_root(self, cur = self.root):
        self.addrs[cur.addr] = len(self.nodes)
        self.nodes.append(cur)
        for c in cur.children:
            self.load_from_root(cur=c)

    def parse_file(self, fn):
        f = open(fn)
        


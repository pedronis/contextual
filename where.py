import os, stat

class WhereCond(object):

    def __init__(self, relative):
        self.relative = relative

    def test(self, p):
        p = os.path.join(p, self.relative)
        return self.check(p)

class WhereDir(WhereCond):
    syn = '-d'

    check = staticmethod(os.path.isdir)

class WhereExists(WhereCond):
    syn = '-e'

    check = staticmethod(os.path.exists)

class WhereFile(WhereCond):
    syn = '-f'

    check = staticmethod(os.path.isfile)

class WhereNonEmpty(WhereCond):
    syn = '-s'

    @staticmethod
    def check(p):
        return os.path.isfile(p) and os.path.getsize(p) > 0

class WhereExecutable(WhereCond):
    syn = '-x'

    @staticmethod
    def check(p):
       return os.access(p, os.X_OK)

WOTH = stat.S_IWGRP | stat.S_IWOTH

class WhereMine(WhereCond):
    syn = '--mine'

    @staticmethod
    def check(p):
        st = os.stat(p)
        return st.st_uid == os.getuid() and (st.st_mode & WOTH) == 0


WHERE_CONDS = {}
for v in globals().values():
    if hasattr(v, 'syn'):
        WHERE_CONDS[v.syn] = v

class WhereClause(object):

    def __init__(self):
        self.conds = []

    def push_cond(self, cond):
        self.conds.append(cond)

    def test(self, p):
        for cond in self.conds:
            if not cond.test(p):
                return False
        return True

def segs(p):
    if p == '/':
        return []
    p_segs = p.split('/')
    if p_segs[0] == '':
        p_segs.pop(0)
    return p_segs

class Landmark(object):

    def __init__(self, prefix, wildcard_child, where, context):
        if prefix is None:
            self.prefix_segs = None
        else:
            self.prefix_segs = segs(prefix)
        self.wildcard_child = wildcard_child
        self.where = where
        self.context = context

    def match_shortcut(self, shortcut, _):
        if self.prefix_segs is None:
            return None, None
        if self.wildcard_child:
            lmark_p = os.path.join('/', '/'.join(self.prefix_segs), shortcut)
            if not os.path.isdir(lmark_p):
                return None, None
        else:
            if not self.prefix_segs or shortcut != self.prefix_segs[-1]:
                return None, None
            lmark_p = os.path.join('/', '/'.join(self.prefix_segs))
        if self.where is None or self.where.test(lmark_p):
            return lmark_p, self.context
        return None, None

    def match_unanchored(self, p, p_segs):
        where = self.where
        if where is None:
            return None, None
        i = len(p_segs)
        while i >= 1:
            lmark_p = os.path.join('/', '/'.join(p_segs[0:i]))
            if where.test(lmark_p):
                return lmark_p, self.context
            i -= 1
        return None, None

    def match(self, p, p_segs):
        if self.prefix_segs is None:
            return self.match_unanchored(p, p_segs)

        where = self.where
        n_prefix_segs = len(self.prefix_segs)
        if p_segs[0:n_prefix_segs] != self.prefix_segs:
            return None, None
        if self.wildcard_child:
            if len(p_segs) <= n_prefix_segs:
                return None, None
            lmark_p = os.path.join('/', '/'.join(p_segs[0:n_prefix_segs+1]))
        else:
            lmark_p = os.path.join('/', '/'.join(self.prefix_segs))
        if where:
            if not where.test(lmark_p):
                return None, None
        return lmark_p, self.context

def parse(config):
    landmarks = []
    for line in config:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        landmark_def, context = line.split(':=')
        parts = landmark_def.split()
        context = context.strip()
        wildcard_child = False
        if parts[0] != 'where':
            prefix = os.path.expanduser(parts[0])
            parts.pop(0)
            if prefix.endswith('/*'):
                prefix = prefix[:-2]
                wildcard_child = True
        else:
            prefix = None
        where = None
        if parts:
            assert parts[0] == 'where'
            parts.pop(0)
            where = WhereClause()
            next_part = iter(parts).next
            while True:
                try:
                    cond_op = next_part()
                except StopIteration:
                    break
                WhereCondClass = WHERE_CONDS[cond_op]
                relative = next_part()
                where.push_cond(WhereCondClass(relative))
        lmark = Landmark(prefix, wildcard_child, where, context)
        lmark.src = line
        landmarks.append(lmark)
    return landmarks

# ________________________________________________________________

def test_landmark():
    p = os.path.dirname(__file__)
    HOME = os.getenv('HOME')
    nempty = WhereNonEmpty('.bashrc')
    s = segs(p)
    where = WhereClause()
    where.push_cond(nempty)
    l = Landmark(None, False, where, 'foo')
    res = l.match(p, s)
    assert res == (HOME, 'foo')

    l = Landmark(os.path.dirname(HOME), True, where, 'foo')
    res = l.match(p, s)
    assert res == (HOME, 'foo')

    l = Landmark(HOME, False, where, 'foo')
    res = l.match(p, s)
    assert res == (HOME, 'foo')

    l = Landmark(HOME, False, None, 'foo')
    res = l.match(p, s)
    assert res == (HOME, 'foo')

    l = Landmark('/', False, None, 'foo')
    res = l.match(p, s)
    assert res == ('/', 'foo')

    # match shortcut
    l = Landmark(os.path.dirname(HOME), True, where, 'foo')
    res = l.match_shortcut(os.path.basename(HOME), None)
    assert res == (HOME, 'foo')

    l = Landmark(HOME, False, where, 'foo')
    res = l.match_shortcut(os.path.basename(HOME), None)
    assert res == (HOME, 'foo')

def test_parse():
    l = parse(['#test', '', 'where -s .bashrc := zzz'])[0]
    assert l.prefix_segs is None
    assert not l.wildcard_child
    c = l.where.conds[0]
    assert isinstance(c, WhereNonEmpty)
    assert c.relative == '.bashrc'
    assert l.context == 'zzz'
    assert l.src == 'where -s .bashrc := zzz'

    l = parse(['#test', '', '/home/* where -e .bashrc := zzz'])[0]
    assert l.prefix_segs == ['home']
    assert l.wildcard_child
    c = l.where.conds[0]
    assert isinstance(c, WhereExists)
    assert c.relative == '.bashrc'

    l = parse(['#test', '', '/home/pedronis where -f .bashrc := zzz'])[0]
    assert l.prefix_segs == ['home', 'pedronis']
    assert not l.wildcard_child
    c = l.where.conds[0]
    assert isinstance(c, WhereFile)
    assert c.relative == '.bashrc'

    l = parse(['#test', '', '/home/pedronis := zzz'])[0]
    assert l.prefix_segs == ['home', 'pedronis']
    assert not l.wildcard_child
    assert l.where is None

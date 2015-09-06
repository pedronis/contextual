"""
Parse directory landmark to context definitions, directory landmark matching.
"""
import os
import shlex

WHERE_CHECKS = {}


def register_check(syn):
    """Register syntax (e.g. -e) to check(path) function."""
    def _register(check):
        WHERE_CHECKS[syn] = check
        return check
    return _register

register_check('-d')(os.path.isdir)
register_check('-e')(os.path.exists)
register_check('-f')(os.path.isfile)


@register_check('-s')
def check_is_non_empty(p):
    return os.path.isfile(p) and os.path.getsize(p) > 0


@register_check('-x')
def check_is_executable(p):
    return os.access(p, os.X_OK)


class WhereCond(object):
    """Represents and tests one directory landmark condition."""

    def __init__(self, check, relative):
        self.check = check
        self.relative = relative

    def test(self, p):
        p = os.path.join(p, self.relative)
        return self.check(p)


class WhereClause(object):
    """Represent and tests all directory landmark conditions."""

    def __init__(self):
        self.conds = []

    def push_cond(self, check, relative):
        self.conds.append(WhereCond(check, relative))

    def test(self, p):
        for cond in self.conds:
            if not cond.test(p):
                return False
        return True


def segs(p):
    """Segment a path."""
    if p == '/':
        return []
    p_segs = p.split('/')
    if p_segs[0] == '':
        p_segs.pop(0)
    return p_segs


class Landmark(object):
    """Directory landmark representation and matching."""

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


def parse(cfg_lines):
    """Parse config lines into directory landmark to context definitions."""
    landmarks = []
    for line in cfg_lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        landmark_def, context = line.split(':=')
        parts = shlex.split(landmark_def)
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
                    check_op = next_part()
                except StopIteration:
                    break
                check = WHERE_CHECKS[check_op]
                relative = next_part()
                where.push_cond(check, relative)
        lmark = Landmark(prefix, wildcard_child, where, context)
        lmark.src = line
        landmarks.append(lmark)
    return landmarks

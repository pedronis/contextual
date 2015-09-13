"""
Parse directory landmark to context definitions, directory landmark matching.
"""
import glob
import os
import shlex
import sys

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


class WhereError(Exception):
    """Error while fulfilling where clause"""


class WhereCond(object):
    """Represents and tests for one directory landmark condition."""

    def __init__(self, check, relative):
        self.check = check
        self.relative = relative

    def matching(self, matched):
        p = matched[0]
        try:
            rel = self.relative.format(*matched, ctxdir=p)
        except (IndexError, KeyError):
            raise WhereError("{!r} has unbound/unknown placeholder".format(self.relative))
        for cand in glob.glob(os.path.join(p, rel)):
            if self.check(cand):
                yield cand


class WhereClause(object):
    """Represent and tests for matches all directory landmark conditions."""

    def __init__(self):
        self.conds = []

    def push_cond(self, check, relative):
        self.conds.append(WhereCond(check, relative))

    def find_matches(self, cond_index, matched):
        if cond_index >= len(self.conds):
            return matched
        cond = self.conds[cond_index]
        for cand in cond.matching(matched):
            got = self.find_matches(cond_index+1, matched+[cand])
            if got:
                return got
        return None

    def test(self, p):
        return self.find_matches(0, [p])


class Succeed(object):
    """Always test true."""

    def test(self, p):
        return [p]


def segs(p):
    """Segment a path."""
    if p == '/':
        return []
    p_segs = p.split('/')
    if p_segs[0] == '':
        p_segs.pop(0)
    return p_segs


class TooUnconstrained(Exception):
    """Landmark is too unconstrained."""


class Landmark(object):
    """Directory landmark representation and matching."""

    def __init__(self, prefix, wildcard_descendant, where, context):
        if prefix is None:
            self.prefix_segs = []
            wildcard_descendant = 'rec'
        else:
            self.prefix_segs = segs(prefix)
        if where is None:
            if wildcard_descendant == 'rec':
                raise TooUnconstrained()
            where = Succeed()
        self.wildcard_descendant = wildcard_descendant
        self.where = where
        self.context = context

    def _test_where(self, p):
        try:
            return self.where.test(p)
        except WhereError as e:
            print >>sys.stderr, "contextual: [rule: %s] %s" % (self.src, e)
            return None

    def match_shortcut(self, shortcut, _):
        if self.wildcard_descendant:
            lmark_p = os.path.join('/', '/'.join(self.prefix_segs), shortcut)
            if not os.path.isdir(lmark_p):
                return None, None
        else:
            shortcut_segs = segs(shortcut)
            if shortcut_segs != self.prefix_segs[-len(shortcut_segs):]:
                return None, None
            lmark_p = os.path.join('/', '/'.join(self.prefix_segs))
        matched = self._test_where(lmark_p)
        if matched:
            return matched, self.context
        return None, None

    def match(self, p, p_segs):
        n_prefix_segs = len(self.prefix_segs)
        if p_segs[0:n_prefix_segs] != self.prefix_segs:
            return None, None
        if self.wildcard_descendant is None:
            up_to = start = n_prefix_segs
        elif self.wildcard_descendant == 'one':
            up_to = start = n_prefix_segs+1
        elif self.wildcard_descendant == 'rec':
            start = n_prefix_segs
            up_to = len(p_segs)
        i = up_to
        while i >= start and i <= len(p_segs):
            lmark_p = os.path.join('/', '/'.join(p_segs[0:i]))
            matched = self._test_where(lmark_p)
            if matched:
                return matched, self.context
            i -= 1
        return None, None


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
        wildcard_descendant = None
        if parts[0] != 'where':
            prefix = os.path.expanduser(parts[0])
            parts.pop(0)
            if prefix.endswith('/*'):
                prefix = prefix[:-2]
                wildcard_descendant = 'one'
            elif prefix.endswith('/**'):
                prefix = prefix[:-3]
                wildcard_descendant = 'rec'
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
        try:
            lmark = Landmark(prefix, wildcard_descendant, where, context)
        except TooUnconstrained:
            print >>sys.stderr, "contextual: too unconstrained: %s" % line
            continue
        lmark.src = line
        landmarks.append(lmark)
    return landmarks

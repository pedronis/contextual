import pytest

from landmark import *  # noqa


@pytest.fixture(scope="module")
def home_and_where_and_here():
    HOME = os.getenv('HOME')
    where = WhereClause()
    where.push_cond(check_is_non_empty, '.bashrc')
    p = os.path.dirname(__file__)
    s = segs(p)
    return HOME, where, p, s


def test_landmark(home_and_where_and_here):
    HOME, where, p, s = home_and_where_and_here

    l = Landmark(None, None, where, 'foo')
    res = l.match(p, s)
    assert res == (HOME, 'foo')

    l = Landmark(os.path.dirname(HOME), 'one', where, 'foo')
    res = l.match(p, s)
    assert res == (HOME, 'foo')

    l = Landmark(os.path.dirname(os.path.dirname(HOME)), 'rec', where, 'foo')
    res = l.match(p, s)
    assert res == (HOME, 'foo')

    l = Landmark(HOME, None, where, 'foo')
    res = l.match(p, s)
    assert res == (HOME, 'foo')

    l = Landmark(HOME, None, None, 'foo')
    res = l.match(p, s)
    assert res == (HOME, 'foo')

    l = Landmark('/', None, None, 'foo')
    res = l.match(p, s)
    assert res == ('/', 'foo')


def test_landmark_match_shortcut(home_and_where_and_here):
    HOME, where, p, s = home_and_where_and_here

    l = Landmark(os.path.dirname(HOME), True, where, 'foo')
    res = l.match_shortcut(os.path.basename(HOME), None)
    assert res == (HOME, 'foo')

    l = Landmark(HOME, False, where, 'foo')
    res = l.match_shortcut(os.path.basename(HOME), None)
    assert res == (HOME, 'foo')


def test_parse():
    l = parse(['#test', '', 'where -s .bashrc := zzz'])[0]
    assert l.prefix_segs == []
    assert l.wildcard_descendant == 'rec'
    c = l.where.conds[0]
    assert c.check == check_is_non_empty
    assert c.relative == '.bashrc'
    assert l.context == 'zzz'
    assert l.src == 'where -s .bashrc := zzz'

    l = parse(['#test', '', '/home/* where -e .bashrc := zzz'])[0]
    assert l.prefix_segs == ['home']
    assert l.wildcard_descendant == 'one'
    c = l.where.conds[0]
    assert c.check == os.path.exists
    assert c.relative == '.bashrc'

    l = parse(['#test', '', '/home/** where -e .bashrc := zzz'])[0]
    assert l.prefix_segs == ['home']
    assert l.wildcard_descendant == 'rec'
    c = l.where.conds[0]
    assert c.check == os.path.exists
    assert c.relative == '.bashrc'

    l = parse(['#test', '', '/home/pedronis where -f .bashrc := zzz'])[0]
    assert l.prefix_segs == ['home', 'pedronis']
    assert l.wildcard_descendant is None
    c = l.where.conds[0]
    assert c.check == os.path.isfile
    assert c.relative == '.bashrc'

    l = parse(['#test', '', '/home/pedronis where -f "this one" := zzz'])[0]
    assert l.prefix_segs == ['home', 'pedronis']
    assert l.wildcard_descendant is None
    c = l.where.conds[0]
    assert c.check == os.path.isfile
    assert c.relative == 'this one'

    l = parse(['#test', '', '/home/pedronis := zzz'])[0]
    assert l.prefix_segs == ['home', 'pedronis']
    assert l.wildcard_descendant is None
    assert l.where is None

    l = parse(['#test', '', '/ := zzz'])[0]
    assert l.prefix_segs == []
    assert l.wildcard_descendant is None
    assert l.where is None

import pytest

from landmark import *  # noqa


@pytest.fixture(scope="function")
def home_and_where_and_here(request, tmpdir):
    """=> home, where clause, p under home, segs(p)"""
    request.addfinalizer(lambda: tmpdir.remove(rec=1, ignore_errors=True))
    home = tmpdir.join('home', 'user0')
    home.join('.bashrc').write_text(u'#', 'ascii', ensure=True)
    where = WhereClause()
    where.push_cond(check_is_non_empty, '.bashrc')
    p = home.join('foo', 'bar').strpath
    s = segs(p)
    return home.strpath, where, p, s


def test_landmark(home_and_where_and_here):
    home, where, p, s = home_and_where_and_here

    l = Landmark(None, None, where, 'foo')
    res = l.match(p, s)
    assert res == (home, 'foo')

    l = Landmark(os.path.dirname(home), 'one', where, 'foo')
    res = l.match(p, s)
    assert res == (home, 'foo')

    l = Landmark(os.path.dirname(os.path.dirname(home)), 'rec', where, 'foo')
    res = l.match(p, s)
    assert res == (home, 'foo')

    l = Landmark(home, None, where, 'foo')
    res = l.match(p, s)
    assert res == (home, 'foo')

    l = Landmark(home, None, None, 'foo')
    res = l.match(p, s)
    assert res == (home, 'foo')

    l = Landmark('/', None, None, 'foo')
    res = l.match(p, s)
    assert res == ('/', 'foo')


def test_landmark_match_shortcut(home_and_where_and_here):
    home, where, p, s = home_and_where_and_here

    l = Landmark(os.path.dirname(home), True, where, 'foo')
    res = l.match_shortcut(os.path.basename(home), None)
    assert res == (home, 'foo')

    l = Landmark(home, False, where, 'foo')
    res = l.match_shortcut(os.path.basename(home), None)
    assert res == (home, 'foo')


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

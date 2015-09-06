import pytest

from landmark import *  # noqa


@pytest.fixture(scope="function")
def home_and_here(request, tmpdir):
    """=> home, p under home, segs(p)"""
    request.addfinalizer(lambda: tmpdir.remove(rec=1, ignore_errors=True))
    home = tmpdir.join('home', 'user0')
    home.join('.bashrc').write_text(u'#', 'ascii', ensure=True)
    p = home.join('foo', 'bar').strpath
    s = segs(p)
    return home.strpath, p, s


@pytest.fixture(scope="function")
def non_empty_dot_bashrc():
    """Make a hopeful where clause"""
    where = WhereClause()
    where.push_cond(check_is_non_empty, '.bashrc')
    return where


def test_landmark(home_and_here, non_empty_dot_bashrc):
    home, p, s = home_and_here

    l = Landmark(None, None, non_empty_dot_bashrc, 'foo')
    res = l.match(p, s)
    assert res == (home, 'foo')

    l = Landmark(os.path.dirname(home), 'one', non_empty_dot_bashrc, 'foo')
    res = l.match(p, s)
    assert res == (home, 'foo')

    l = Landmark(os.path.dirname(os.path.dirname(home)), 'rec', non_empty_dot_bashrc, 'foo')
    res = l.match(p, s)
    assert res == (home, 'foo')

    l = Landmark(home, None, non_empty_dot_bashrc, 'foo')
    res = l.match(p, s)
    assert res == (home, 'foo')

    l = Landmark(home, None, None, 'foo')
    res = l.match(p, s)
    assert res == (home, 'foo')

    l = Landmark('/', None, None, 'foo')
    res = l.match(p, s)
    assert res == ('/', 'foo')


@pytest.fixture(scope="function")
def hopeless_where():
    where1 = WhereClause()
    where1.push_cond(check_is_executable, '.non-existent-file')
    return where1


def test_landmark_no_match(home_and_here, hopeless_where):
    home, p, s = home_and_here

    l = Landmark(home, False, None, 'foo')
    p1 = os.path.abspath(os.path.join(home, '..', 'user1'))
    res = l.match(p1, segs(p1))
    assert res == (None, None)

    l = Landmark(None, None, hopeless_where, 'foo')
    res = l.match(p, s)
    assert res == (None, None)

    l = Landmark(os.path.dirname(home), 'one', hopeless_where, 'foo')
    res = l.match(p, s)
    assert res == (None, None)

    l = Landmark(home, 'one', None, 'foo')
    res = l.match(home, segs(home))
    assert res == (None, None)


def test_landmark_match_shortcut(home_and_here, non_empty_dot_bashrc):
    home, p, s = home_and_here

    l = Landmark(os.path.dirname(home), 'one', non_empty_dot_bashrc, 'foo')
    res = l.match_shortcut(os.path.basename(home), None)
    assert res == (home, 'foo')

    l = Landmark(home, None, non_empty_dot_bashrc, 'foo')
    res = l.match_shortcut(os.path.basename(home), None)
    assert res == (home, 'foo')


def test_landmark_match_shortcut_no_match(home_and_here, hopeless_where):
    home, p, s = home_and_here

    l = Landmark(os.path.dirname(home), 'one', None, 'foo')
    res = l.match_shortcut('user1', None)
    assert res == (None, None)

    l = Landmark(home, False, None, 'foo')
    res = l.match_shortcut('user1', None)
    assert res == (None, None)

    l = Landmark(os.path.dirname(home), 'one', hopeless_where, 'foo')
    res = l.match_shortcut(os.path.basename(home), None)
    assert res == (None, None)


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
    assert isinstance(l.where, Succeed)

    l = parse(['#test', '', '/ := zzz'])[0]
    assert l.prefix_segs == []
    assert l.wildcard_descendant is None
    assert isinstance(l.where, Succeed)

    l = parse(['#test', '', '/home/** := zzz'])
    assert len(l) == 0

# contextual: providing context for shell command invocations
# Copyright 2008-2015  Samuele Pedroni
#
# This file is part of contextual.
#
# contextual is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# contextual is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with contextual.  If not, see <http://www.gnu.org/licenses/>.
#
import pytest

from landmark import *  # noqa


@pytest.fixture(scope="function")
def home_and_here(request, tmpdir):
    """=> home, p under home, segs(p)"""
    request.addfinalizer(lambda: tmpdir.remove(rec=1, ignore_errors=True))
    home = tmpdir.join('home', 'user0')
    home.join('.bashrc').write_text(u'#', 'ascii', ensure=True)
    home.join('.bashrc').chmod(0o700)
    p = home.join('foo', 'bar').strpath
    home.join('x').ensure_dir()
    home.join('y/z').ensure_dir()
    s = segs(p)
    return home.strpath, p, s


@pytest.fixture(scope="function")
def non_empty_and_executable_dot_bashrc():
    """Make a hopeful landmark clause"""
    where = LandmarkClause()
    where.push_cond(check_is_non_empty, '.bashrc')
    where.push_cond(check_is_executable, '{1}')
    return where


def test_landmark(home_and_here, non_empty_and_executable_dot_bashrc):
    home, p, s = home_and_here
    hit = os.path.join(home, '.bashrc')

    l = Landmark(None, None, non_empty_and_executable_dot_bashrc, 'ctx')
    res = l.match(p, s)
    assert res == ([home, hit, hit], 'ctx')

    l = Landmark(os.path.dirname(home), 'one', non_empty_and_executable_dot_bashrc, 'ctx')
    res = l.match(p, s)
    assert res == ([home, hit, hit], 'ctx')

    l = Landmark(os.path.dirname(os.path.dirname(home)), 'rec',
                 non_empty_and_executable_dot_bashrc, 'ctx')
    res = l.match(p, s)
    assert res == ([home, hit, hit], 'ctx')

    l = Landmark(home, None, non_empty_and_executable_dot_bashrc, 'ctx')
    res = l.match(p, s)
    assert res == ([home, hit, hit], 'ctx')

    l = Landmark(home, None, None, 'ctx')
    res = l.match(p, s)
    assert res == ([home], 'ctx')

    l = Landmark('/', None, None, 'ctx')
    res = l.match(p, s)
    assert res == (['/'], 'ctx')


def test_landmark_backtrack(home_and_here):
    home, p, s = home_and_here

    where = LandmarkClause()
    where.push_cond(os.path.isdir, '*')
    where.push_cond(os.path.isdir, '{1}/z')

    l = Landmark(home, 'rec', where, 'ctx')
    res = l.match(p, s)
    assert res == ([home, os.path.join(home, 'y'), os.path.join(home, 'y/z')], 'ctx')

    nowhere = LandmarkClause()
    nowhere.push_cond(os.path.isdir, '*')
    nowhere.push_cond(check_is_non_empty, '{1}/z')

    l = Landmark(home, 'rec', nowhere, 'ctx')
    res = l.match(p, s)
    assert res == (None, None)


@pytest.fixture(scope="function")
def hopeless_where():
    """Make a hopeless landmark clause"""
    where1 = LandmarkClause()
    where1.push_cond(lambda p: True, '.non-existent-file')
    return where1


def test_landmark_no_match(home_and_here, hopeless_where):
    home, p, s = home_and_here

    l = Landmark(home, None, None, 'ctx')
    p1 = os.path.abspath(os.path.join(home, '..', 'user1'))
    res = l.match(p1, segs(p1))
    assert res == (None, None)

    l = Landmark(None, None, hopeless_where, 'ctx')
    res = l.match(p, s)
    assert res == (None, None)

    l = Landmark(os.path.dirname(home), 'one', hopeless_where, 'ctx')
    res = l.match(p, s)
    assert res == (None, None)

    l = Landmark(home, 'one', None, 'ctx')
    res = l.match(home, segs(home))
    assert res == (None, None)


def test_landmark_match_shortcut(home_and_here, non_empty_and_executable_dot_bashrc):
    home, p, s = home_and_here
    hit = os.path.join(home, '.bashrc')

    l = Landmark(os.path.dirname(home), 'one', non_empty_and_executable_dot_bashrc, 'ctx')
    res = l.match_shortcut(os.path.basename(home), None)
    assert res == ([home, hit, hit], 'ctx')

    l = Landmark(os.path.dirname(home), 'one', None, 'ctx')
    res = l.match_shortcut(os.path.basename(home), None)
    assert res == ([home], 'ctx')

    l = Landmark(home, None, non_empty_and_executable_dot_bashrc, 'ctx')
    res = l.match_shortcut(os.path.basename(home), None)
    assert res == ([home, hit, hit], 'ctx')


def test_landmark_match_shortcut_no_match(home_and_here, hopeless_where):
    home, p, s = home_and_here

    l = Landmark(os.path.dirname(home), 'one', None, 'ctx')
    res = l.match_shortcut('user1', None)
    assert res == (None, None)

    l = Landmark(home, None, None, 'ctx')
    res = l.match_shortcut('user1', None)
    assert res == (None, None)

    l = Landmark(os.path.dirname(home), 'one', hopeless_where, 'ctx')
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


def test_placeholder_error(capsys):
    rule1 = 'where -e {2}/x := ctx'
    l = parse([rule1])[0]
    res = l.match('/', segs('/'))
    assert res == (None, None)
    assert capsys.readouterr() == (
        '',
        'contextual: [rule: {}] {!r} has unbound/unknown placeholder\n'.format(rule1, '{2}/x')
    )

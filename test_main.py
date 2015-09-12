import pytest

from _contextual import main


@pytest.fixture(scope="function")
def home_and_projs(request, tmpdir):
    """=> home, proj1/a, proj2/b, proj2/p1 -> proj1"""
    request.addfinalizer(lambda: tmpdir.remove(rec=1, ignore_errors=True))
    home = tmpdir.join('home', 'user0')
    a = home.join('proj1', 'a').ensure_dir()
    b = home.join('proj2', 'b').ensure_dir()
    p2p1 = home.join('proj2', 'p1')
    p2p1.mksymlinkto(a.dirpath())
    return home, a, b, p2p1


def test_match(home_and_projs, monkeypatch):
    home, a, b, p2p1 = home_and_projs
    conf = u"""
{} := PROJ=1
""".format(a.dirpath().strpath, b.dirpath().strpath)
    confp = home.join('ctx.conf')
    confp.write_text(conf, encoding='ascii')
    monkeypatch.chdir(a.strpath)
    monkeypatch.setenv('PWD', a.strpath)
    main(['_', confp.strpath, 'cmd'])


def test_diverged_PWD(home_and_projs, monkeypatch):
    home, a, b, p2p1 = home_and_projs
    conf = u"""
{} := PROJ=1
{} := PROJ=2
""".format(a.dirpath().strpath, b.dirpath().strpath)
    confp = home.join('ctx.conf')
    confp.write_text(conf, encoding='ascii')
    monkeypatch.chdir(p2p1.strpath)
    monkeypatch.setenv('PWD', p2p1.strpath)
    main(['_', confp.strpath, 'cmd'])

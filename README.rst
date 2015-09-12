contextual: providing context for shell command invocations
===========================================================

*contextual* is a utility that given the current working directory walks
the tree to find relevant context(s), based on path prefixes and
landmark conditions (simple ``test`` like checks), to apply before invoking
the given command. It takes a configuration file with rules and the
command and is conveniently used usually behind a short alias like
``+`` or more specific ones.

For example with a proper setup and the rule::

  ~/projs/** where -f */bin/activate := source {1}

invoking from ``~/projs/proj1/subdir`` that has a Python virtualenv
with ``~/projs/proj1/venv/bin/activate`` either::

  $ +python m.py

or::

  $ + python m.py

will actually invoke in a subshell::

  source <HOME>/projs/proj1/venv/bin/activate ; python m.py

Rules
+++++

A *contextual* configuration file contains context rules, one per
line, of the form::

  [ctx-path-prefix[wildcard-descendant]] ["where" [landmark-cond landmark-path]*] ":=" context

  wildcard-descendant =  "/*" | "/**"
  landmark-cond = "-e" | "-f" | "-d" | "-x"

*contextual* will consider in order the current working directory
first as indicated by the environment variable ``PWD`` then as result
of ``getcwd`` (which can be different in the presence of symlinks) and
find matching rules for these *start directories*.

*ctx-path-prefix* values undergo ``~`` user expansion before being
used.

A matching rule has *ctx-path-prefix* that is a prefix of the *start
directory*. Then it has, if *wildcard-descendant* is omitted in the
rule, *start directory* itself or, if *wildcard-descendant* is ``/*``,
one direct subdirectory of *ctx-path-prefix* and parent of *start
directory*, or, if *wildcard-descendant* is ``/**``, one parent of
*start directory* descendant subdirectory of *ctx-path-prefix*
(included) fulfilling all optional *landmark-cond landmark-path* pairs. The
fulfilling directory is the *context directory* and for the ``/**`` case
it is the first directory fulfilling walking up from the *start
directory* to *ctx-path-prefix* included.

In the example ``~/projs/proj1/subdir`` is the *start directory*, the
rule has ``/**`` as *wildcard-descendant* so *context directory*
candidates are in order::

  ~/projs/proj1/subdir  ~/projs/proj1  ~/projs

Fulfilling the pairs *landmark-cond landmark-path* for a candidate
*context directory* means ``test`` *landmark-cond* *landmark-path* is
true for each pair usually interpreting *landmark-path* relatively to
the candidate.  *landmark-path* can contain simple globbing (``*?``)
and they can contain placeholders ``{#}`` (``#`` is a index starting
from 0) or ``{ctx_dir}``. ``{0}`` and ``{ctx_dir}`` both evaluate to
the candidate *context directory* while ``{1}``, ``{2}``,...  evaluate
to a condition fulfilling file system entry for the corresponding
landmark condition pair, when they are numbered from 1 starting from
the left. To deal with globbing and placeholders combined,
*contextual* tries to fulfill conditions from left to right with
backtracking going through candidate file system entries for each
condition as produced by globbing.

In the example candidate ``~/projs/proj1`` fulfills ``-f
*/bin/activate`` because ``~/projs/proj1/venv/bin/activate`` exists
and is a file. Also::

  {0} = {ctx_dir} = <HOME>/projs/proj1
  {1} = <HOME>/projs/proj1/venv/bin/activate

For each *start directory* in order *contextual* will consider rules
top to bottom and will evaluate *context* of a matching rule using the
same placeholder definitions as for the conditions. In this process a
rule is ignored once it has been matching.

In the example the evaluated *context* of the matched rule becomes::

  source <HOME>/projs/proj1/venv/bin/activate

Finally *contextual* will apply the list of evaluated *context*
values from matching rules in reverse order before invoking the given
command. This means the effect (usually environment changes) of the
*context* of first-matched rules will take precedence over later
matching rule *context*.

In the example the full process gives *contextual* to invoke::

  source <HOME>/projs/proj1/venv/bin/activate ; python m.py

My Setup
++++++++

``~/bin`` in ``PATH`` and symlinks from ``~/bin`` to the ``contextual``
and ``_contextual.py`` scripts in a checkout of *contextual*.

The following aliases::

  alias +='contextual ~/.contextual'
  alias +go='+ go'
  alias +py.test='+ py.test'
  alias +python='+ python'

and ``~/.contextual`` containing::

  ~/repos/* := source ~/repos/homeconf/repocontext {ctx_dir}
  ~/go-ws/* := export GOPATH=~/go-ws
  / :=

the first rule shows that more complicated contexts can be setup by sourcing shell scripts whose behavior may depend on the *context dir*.

The last rule avoids getting ``contextual: failed to infer context:
...`` errors when using the aliases with *start directories* not
matching any rule. A matter of personal preference.

Debugging Rules
+++++++++++++++

Hacking
+++++++

License
+++++++

Copyright 2008-2015 Samuele Pedroni

*contextual* is distributed under the terms of the GNU General
Public License (GPL) version 3 or later. See COPYING.


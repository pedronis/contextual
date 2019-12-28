#!/usr/bin/python3
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
from __future__ import print_function

import os
import sys

import landmark


def infer_contexts(landmarks, locations, tracef):
    context_pairs = []
    unmatched_landmarks = landmarks[:]
    for kind, location in locations:
        tracef("start-dir[{}]: {}", kind, location)
        location_segs = landmark.segs(location)
        # use a rule only once
        unmatched_landmarks2 = []
        for lmark in unmatched_landmarks:
            matched, context = lmark.match(location, location_segs)
            if matched:
                if context:
                    tracef(" ~~ {} => {}", lmark.src, matched)
                    context_pairs.append((matched, context))
                else:
                    # void context
                    tracef(" ~~ {} => void_context", lmark.src)
                    context_pairs.append((None, None))
            else:
                unmatched_landmarks2.append(lmark)
                tracef(" ~~ {} => no", lmark.src)
        unmatched_landmarks = unmatched_landmarks2
    return context_pairs


def main(args):
    args = list(args)
    landmarks = landmark.parse(open(args[0]))
    runcmd = args[1]
    trace = False
    tracef = lambda *a: None  # noqa
    if len(args) >= 3 and args[2] == ":trace":
        args.pop(2)
        trace = True

        def tracef(fmt, *a):
            print(fmt.format(*a), file=sys.stderr)

    locations = []
    if "/" in runcmd:
        locations.append(("abscmd", os.path.dirname(os.path.abspath(runcmd))))
    PWD = os.getenv("PWD")
    if PWD:
        locations.append(("PWD", PWD))
    locations.append(("getcwd", os.getcwd()))

    context_pairs = infer_contexts(landmarks, locations, tracef)

    if not context_pairs:
        print(
            "contextual: failed to infer context: {}".format(locations), file=sys.stderr
        )
        print("exit 1", file=sys.stdout)
        sys.exit(1)

    contexts = []
    # reverse so that early rules context effects have precedence
    for matched, context in reversed(context_pairs):
        if context is None:
            continue
        try:
            contexts.append(context.format(*matched, ctx_dir=matched[0]))
        except (IndexError, KeyError):
            print(
                "contextual: {!r} has unbound/unknown placeholder".format(context),
                file=sys.stderr,
            )
    total_context = ";".join(contexts)

    if trace:
        print("CONTEXT => {}".format(total_context), file=sys.stderr)
        print("exit 0", file=sys.stdout)
        sys.exit(0)

    print(total_context, file=sys.stdout)


if __name__ == "__main__":
    main(sys.argv[1:])

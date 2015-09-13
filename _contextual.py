#!/usr/bin/python
import os
import sys

import landmark


def infer_contexts(landmarks, locations, trace):
    context_pairs = []
    unmatched_landmarks = landmarks[:]
    for location in locations:
        if trace:
            print >>sys.stderr, "start-dir: %s" % location
        location_segs = landmark.segs(location)
        # use a rule only once
        unmatched_landmarks2 = []
        for lmark in unmatched_landmarks:
            matched, context = lmark.match(location, location_segs)
            if matched:
                if trace:
                    print >>sys.stderr, "%s ~ %s => %s" % (location, lmark.src, matched)
                if context:
                    context_pairs.append((matched, context))
            else:
                unmatched_landmarks2.append(lmark)
                if trace:
                    print >>sys.stderr, "%s ~ %s => no" % (location, lmark.src)
        unmatched_landmarks = unmatched_landmarks2
    return context_pairs


def main(args):
    args = list(args)
    landmarks = landmark.parse(open(args[0]))
    runcmd = args[1]
    trace = False
    if len(args) >= 3 and args[2] == ':trace':
        args.pop(2)
        trace = True

    locations = []
    if '/' in runcmd:
        locations.append(os.path.dirname(os.path.abspath(runcmd)))
    PWD = os.getenv('PWD')
    if PWD:
        locations.append(PWD)
    locations.append(os.getcwd())

    context_pairs = infer_contexts(landmarks, locations, trace)

    if not context_pairs:
        print >>sys.stderr, "contextual: failed to infer context: %s" % locations
        print >>sys.stdout, "exit 1"
        sys.exit(1)

    contexts = []
    # reverse so that early rules context effects have precedence
    for matched, context in reversed(context_pairs):
        try:
            contexts.append(context.format(*matched, ctx_dir=matched[0]))
        except (IndexError, KeyError):
            print >>sys.stderr, 'contextual: {!r} has unbound/unknown placeholder'.format(context)
    total_context = ';'.join(contexts)

    if trace:
        print >>sys.stderr, "CONTEXT => %s" % total_context
        print >>sys.stdout, "exit 0"
        sys.exit(0)
    else:
        print >>sys.stdout, total_context


if __name__ == '__main__':
    main(sys.argv[1:])

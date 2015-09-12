#!/usr/bin/python
import sys, os, subprocess

import landmark

def infer_context(landmarks, locations, trace):
    for location in locations:
        location_segs = landmark.segs(location)
        for lmark in landmarks:
            matched, context = lmark.match(location, location_segs)
            if matched is not None:
                if trace:
                    print >>sys.stderr, "%s ~ %s => yes" % (location, lmark.src)
                return matched, context
            if trace:
                print >>sys.stderr, "%s ~ %s => no" % (location, lmark.src)

    print >>sys.stderr, "failed to infer context: %s" % locations
    print >>sys.stdout, "exit 1"
    sys.exit(1)

def main(args):
    args = list(args)
    landmarks = landmark.parse(open(args[0]))
    runcmd = args[1]
    trace = False
    if len(args) >=3 and args[2] == ':trace':
        args.pop(2)
        trace = True

    locations = []
    if '/' in runcmd:
        locations.append(os.path.dirname(os.path.abspath(runcmd)))
    PWD = os.getenv('PWD')
    if PWD:
        locations.append(PWD)
    locations.append(os.getcwd())

    matched, context = infer_context(landmarks, locations, trace)

    context = context.format(*matched, ctx_dir=matched[0])

    if trace:
        print >>sys.stderr, "CONTEXT => %s" % context
        print >>sys.stdout, "exit 0"
        sys.exit(0)
    else:
        print >>sys.stdout, context


if __name__ == '__main__':
    main(sys.argv[1:])

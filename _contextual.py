#!/usr/bin/python
import sys, os, subprocess

import landmark

def infer_context(landmarks, how, locations, hint, trace):
    match_kind = how[:1]
    match = getattr(landmark.Landmark, ('match_'+how).strip('_'))
    for location in locations:
        location_segs = landmark.segs(location)
        for lmark in landmarks:
            matched, context = match(lmark, location, location_segs)
            if matched is not None:
                if trace:
                    print >>sys.stderr, "%s ~%s~ %s => yes" % (location,
                                                               match_kind,
                                                               lmark.src)
                return lmark, matched, context
            if trace:
                print >>sys.stderr, "%s ~%s~ %s => no" % (location,
                                                          match_kind,
                                                          lmark.src)

    print >>sys.stderr, "failed to infer context: %s" % hint
    print >>sys.stdout, "exit 1"
    sys.exit(1)

def main(args):
    args = list(args)
    landmarks = landmark.parse(open(args[1]))
    runcmd = args[2]
    shortcut = None
    trace = False
    if len(args) >=4 and args[3] == ':trace':
        args.pop(3)
        trace = True
    if len(args) >=4 and args[3].startswith(':'):
        shortcut = args.pop(3)

    locations = []
    if '/' in runcmd:
        locations.append(os.path.dirname(os.path.abspath(runcmd)))
    for farg in args[3:]:
        if not (farg.startswith('-') or farg.startswith('+')):
            if os.path.exists(farg):
                locations.append(os.path.abspath(farg))
            break
    PWD = os.getenv('PWD')
    if PWD:
        locations.append(PWD)
    locations.append(os.getcwd())

    if shortcut:
        lmark, matched, context = infer_context(landmarks,
                                                'shortcut',
                                                [shortcut[1:]],
                                                shortcut,
                                                trace)
    else:
        _, matched, context = infer_context(landmarks,
                                            '',
                                            locations,
                                            locations,
                                            trace)

    context = context.format(*matched, ctx_dir=matched[0])

    if context.startswith('!'):
        p = subprocess.Popen(context[1:], shell=True, stdout=subprocess.PIPE)
        out = p.communicate()[0]
        if p.returncode != 0:
            print >>sys.stderr, "failed running: %s" % context
            print >>sys.stdout, "exit 1"
            sys.exit(1)
        context = out

    if trace:
        print >>sys.stderr, "CONTEXT => %s" % context
        print >>sys.stdout, "exit 0"
        sys.exit(0)
    else:
        print >>sys.stdout, context

    if shortcut:
        print >>sys.stdout, " ; shift 1"


if __name__ == '__main__':
    main(sys.argv)

#!/usr/bin/python
import sys, os, subprocess

import where


def infer_context(landmarks, how, locations, hint, trace):
    match_kind = how[:1]
    match = getattr(where.Landmark, ('match_'+how).strip('_'))
    for location in locations:
        location_segs = where.segs(location)
        for lmark in landmarks:
            lmark_p, context = match(lmark, location, location_segs)
            if lmark_p is not None:
                if trace:
                    print >>sys.stderr, "%s ~%s~ %s => yes" % (location,
                                                               match_kind,
                                                               lmark.src)
                return lmark, lmark_p, context
            if trace:
                print >>sys.stderr, "%s ~%s~ %s => no" % (location,
                                                          match_kind,
                                                          lmark.src)

    print >>sys.stderr, "failed to infer context: %s" % hint
    print >>sys.stdout, "exit 1"
    sys.exit(1)


def working_dir():
    return os.getenv("PWD") or os.getcwd()


def main(args):
    args = list(args)
    landmarks = where.parse(open(args[1]))
    runcmd = args[2]
    shortcut = None
    trace = False
    like = False
    if len(args) >=4 and args[3] == ':trace':
        args.pop(3)
        trace = True
    if len(args) >=4 and args[3].startswith(':'):
        shortcut = args.pop(3)
        if shortcut.startswith(':='):
            shortcut = ':' + shortcut[2:]
            like = True

    locations = []
    if '/' in runcmd:
        locations.append(os.path.dirname(os.path.abspath(runcmd)))
    for farg in args[3:]:
        if not (farg.startswith('-') or farg.startswith('+')):
            if os.path.exists(farg):
                locations.append(os.path.abspath(farg))
            break
    locations.append(working_dir())

    if shortcut:
        lmark, lmark_p, context = infer_context(landmarks,
                                         'shortcut',
                                         [shortcut[1:]],
                                         shortcut,
                                         trace)
        if like:
            _, lmark_p, context = infer_context([lmark],
                                                'unanchored',
                                                locations,
                                                locations,
                                                trace)
    else:
        _, lmark_p, context = infer_context(landmarks,
                                            '',
                                            locations,
                                            locations,
                                            trace)

    context = context % {'runcmd': runcmd, 'where': lmark_p}

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

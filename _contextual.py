#!/usr/bin/python
import sys, os, subprocess

import where

def infer_context(landmarks, match, locations, trace):
    for location in locations:
        location_segs = where.segs(location)
        for lmark in landmarks:
            lmark_p, context = match(lmark, location, location_segs)
            if lmark_p is not None:
                if trace:
                    print >>sys.stderr, "%s ~~ %s => yes" % (location, lmark.src)
                return lmark_p, context
            if trace:
                print >>sys.stderr, "%s ~~ %s => no" % (location, lmark.src)

    return None, None

def main(args):
    args = list(args)
    landmarks = where.parse(open(args[1]))
    runcmd = args[2]
    shortcut = None
    trace = False
    if len(args) >=4 and args[3] == ':trace':
        args.pop(3)
        trace = True
        
    if len(args) >=4 and args[3].startswith(':'):
        shortcut = args[3]
        locations = [shortcut[1:]]
        how = where.Landmark.match_shortcut
    else:
        locations = []
        if '/' in runcmd:
            locations.append(os.path.dirname(os.path.abspath(runcmd)))
        for farg in args[3:]:
            if not (farg.startswith('-') or farg.startswith('+')):
                if os.path.exists(farg):
                    locations.append(os.path.abspath(farg))
                break
        locations.append(os.getcwd())
        how = where.Landmark.match
        
    lmark_p, context = infer_context(landmarks, how, locations, trace)
        
    if lmark_p is None:
        print >>sys.stderr, "failed to infer context: %s" % (shortcut or locations)
        print >>sys.stdout, "exit 1"
        sys.exit(1)

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

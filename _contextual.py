#!/usr/bin/python
import sys, os

import where

def infer_context(landmarks, match, locations):
    for location in locations:
        location_segs = where.segs(location)
        for lmark in landmarks:
            lmark_p, context = match(lmark, location, location_segs)
            if lmark_p is not None:
                return lmark_p, context

    return None, None

def main():
    landmarks = where.parse(open(sys.argv[1]))
    runcmd = sys.argv[2]
    shortcut = None
    if len(sys.argv) >=4 and sys.argv[3].startswith(':'):
        shortcut = sys.argv[3]
        locations = [shortcut[1:]]
        how = lambda lmark, shortcut, _: lmark.match_shortcut(shortcut)
    else:
        locations = []
        if '/' in runcmd:
            locations.append(os.path.dirname(os.path.abspath(runcmd)))
        for farg in sys.argv[3:]:
            if not (farg.startswith('-') or farg.startswith('+')):
                if os.path.exists(farg):
                    locations.append(os.path.abspath(farg))
                break
        locations.append(os.getcwd())
        how = where.Landmark.match
        
    lmark_p, context = infer_context(landmarks, how, locations)
        
    if lmark_p is None:
        print >>sys.stderr, "failed to infer context: %s" % (shortcut or locations)
        print >>sys.stdout, "exit 1"
        sys.exit(1)

    # xxx ! context

    print >>sys.stdout, context % {'runcmd': runcmd, 'where': lmark_p}
    if shortcut:
        print >>sys.stdout, " ; shift 1" 
    

if __name__ == '__main__':
    main()

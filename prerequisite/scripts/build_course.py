"""Compatibility command for the authoritative v2 course generator."""
from paths import SITE
def outputs(course=None):
    from build_readings import render_outputs
    readings,pages=render_outputs()
    return {SITE/route:source for route,source in {**readings,**pages}.items()}
if __name__=='__main__':
    from build_readings import main
    main()

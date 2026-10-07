"""Generate v2 lab returns; legacy attachment generation is retired."""
from paths import SITE

def integrate_navigation(path,source,course=None):
    from build_readings import render_outputs
    route=path.relative_to(SITE).as_posix()
    if 'class="reading-page"' in source:return source
    return render_outputs({route:source})[1][route]

def strip_navigation(source):
    return source

def outputs():
    from build_readings import render_outputs
    return {SITE/route:source for route,source in render_outputs()[1].items() if route.startswith('labs/') and route!='labs/index.html'}

if __name__=='__main__':
    from build_readings import main
    main()

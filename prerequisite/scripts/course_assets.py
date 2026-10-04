"""Keep course entry points and their module imports on the same cache version."""
import re

ASSET_VERSION = 'outline-20261004'


def version_assets(source):
    return re.sub(r'((?:src|href)="[^"?]+(?:course-navigation\.js|course\.css|lab-shell\.js))(?:\?[^"\s]*)?"',
                  lambda match: match[1] + '?v=' + ASSET_VERSION + '"', source)

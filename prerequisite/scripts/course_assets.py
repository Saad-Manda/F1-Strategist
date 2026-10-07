"""Keep course entry points and their module imports on the same cache version."""
import re

ASSET_VERSION = 'reading-20261006-r8'


def version_assets(source):
    return re.sub(r'((?:src|href)="[^"?]+\.(?:js|css))(?:\?[^"\s]*)?"',
                  lambda match: match[1] + '?v=' + ASSET_VERSION + '"', source)

from .default_scheme import DefaultNamingScheme

try:
    from .external import EXTERNAL_SCHEMES
except ImportError:
    EXTERNAL_SCHEMES = {}

schemes = EXTERNAL_SCHEMES.copy()

schemes[DefaultNamingScheme.scheme_id] = DefaultNamingScheme

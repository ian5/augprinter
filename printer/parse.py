import yaml
from printer import bodyitems

def parse_sigil(raw : dict) -> bodyitems.Sigil:
    return bodyitems.Sigil(**raw)

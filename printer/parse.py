from PIL import Image
from printer import bodyitems
from printer.loaders import open_image_cached

# I can't think of a better place for this right now; it's an object that
# should exist but doesn't fit into the category of any of the others
class Cost:
    """Definition of a particular cost
    
    Parameters
    ----------
    icon : Image or path to image
        The cost icon
    threshold : int, optional
        The threshold at which this cost changes to compact rendering
    """
    def __init__(self, icon : str, threshold : int | None):
        self.icon = open_image_cached(icon)
        self.threshold = threshold
    
    def get_compact(self, count : int) -> bool:
        """Returns true if the given count of this cost should be compact"""
        return self.threshold is None or count <= self.threshold

def parse_sigil(raw : dict) -> bodyitems.Sigil:
    # All the work is done by the sigil initialization function
    return bodyitems.Sigil(**raw)

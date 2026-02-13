# Having this be all on its own feels weird but it resolves a circular import
# and I'm trying not to get bogged down in the details for the bodge
from printer.loaders import open_image_cached

class Cost:
    """Definition of a particular cost
    
    Parameters
    ----------
    icon : Path to image
        The cost icon
    threshold : int, optional
        The threshold at which this cost changes to compact rendering
    """
    def __init__(self, icon : str, fold : int | None = None):
        self.icon = open_image_cached(icon)
        self.fold = fold
    
    def get_compact(self, count : int) -> bool:
        """Returns true if the given count of this cost should be compact"""
        return self.fold is None or count >= self.fold
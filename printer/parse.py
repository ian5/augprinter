import collections.abc
from PIL import Image
from printer import bodyitems
from printer.loaders import open_image_cached

# I can't think of a better place for this right now; it's an object that
# should exist but doesn't fit into the category of any of the others
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
        return self.fold is None or count <= self.fold

def parse_sigil(raw : dict) -> bodyitems.Sigil:
    """Parse the dictionary form of a sigil into the Sigil class"""
    # All the work is done by the sigil initialization function
    return bodyitems.Sigil(**raw)

def parse_cost(raw : dict) -> Cost:
    """Parse the dictionary form of a cost into the Cost class"""
    return Cost(raw["icon"], raw["fold"])

# NOTE: This might be a good place to split this file later;
# I'm not quite sure if parsing the items and handling complete files should 
# be multiple files

error_sigil = bodyitems.Sigil(
    "Not Found", open_image_cached("builtin/sigil_error.png"),
    "No sigil by this name was found.")

error_cost = Cost("builtin/costerror.png", 4)

class CardContext:
    """Contextual information for the printing of cards"""
    def __init__(self):
        self.sigils = {}
        self.costs = {}
    
    def load(self, raw : dict):
        """Parse a set of sigils or costs and add them to this context"""
        # Determine what kind of entry we're loading
        # TODO: Retroactively don't repeat yourself
        match raw["type"]: 
            # If we're loading costs
            case "costs":
                # For each cost
                for raw_cost in raw["contents"]:
                    # Parse the cost's actual data
                    cost = parse_cost(raw_cost)
                    # Allow cost names to be specified alone in the format by
                    # making a single cost into a tuple of length one
                    if isinstance(raw_cost["name"], str):
                        names = (raw_cost["name"],)
                    else:
                        names = raw_cost["name"]
                    # Then for each name 
                    for name in names:
                        # Assign said cost to the name 
                        self.costs[name] = cost
            case "sigils":
                # For each sigil
                for raw_sigil in raw["contents"]:
                    # Parse the sigil's actual data
                    sigil = parse_cost(raw_sigil)
                    # Allow sigil names to be specified alone in the format by
                    # making a single cost into a tuple of length one
                    if isinstance(raw_sigil["name"], str):
                        names = (raw_sigil["name"],)
                    else:
                        names = raw_sigil["name"]
                    # Then for each name 
                    for name in names:
                        # Assign said cost to the name 
                        self.sigils[name] = sigil
    
    def get_cost(self, name : str) -> Cost:
        """Return the cost associated with that name"""
        return self.costs.get(name, error_cost)

    def get_sigil(self, name : str) -> bodyitems.Sigil:
        """Return the sigil associated with that name"""
        return self.sigils.get(name, error_sigil)
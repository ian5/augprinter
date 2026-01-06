from loguru import logger
from printer import bodyitems
from printer.loaders import open_image_cached
from collections import ChainMap
from collections.abc import Iterable, Mapping

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
        return self.fold is None or count >= self.fold

def parse_sigil(raw : Mapping) -> bodyitems.Sigil:
    """Parse the dictionary form of a sigil into the Sigil class"""
    # All the work is done by the sigil initialization function
    return bodyitems.Sigil(**raw)

def parse_cost(raw : Mapping) -> Cost:
    """Parse the dictionary form of a cost into the Cost class"""
    return Cost(raw['icon'], raw['fold'])

error_sigil = bodyitems.Sigil(
    'Not Found', open_image_cached('assets/builtin/sigil_error.png'),
    'No sigil by this name was found.')

error_cost = Cost('assets/builtin/costerror.png', 4)

class CardContext:
    """Contextual information for the printing of cards"""
    def __init__(self):
        self.sigils = {}
        self.costs = {}
    
    def load(self, raw : Mapping, defaults : Iterable = []):
        """Parse a set of data entries and add them to this context"""
        # Note any properties that apply to all objects in this list
        default_properties = raw.get('default', {})
        # For each entry...
        for entry in raw.get('contents', {}):
            # Use global values if they aren't overwritten
            # This is also where any parent groups' defaults are incorporated
            view = ChainMap(entry, default_properties, *defaults)
            IDs = view.get('id')
            
            # Each type of entry requires different parsing; unspecified types
            # are assumed to be groups for syntactic convenience
            match view.get('type', 'group'):
                case 'cost':
                    parsed = parse_cost(view)
                    target = self.costs
                case 'sigil':
                    parsed = parse_sigil(view)
                    target = self.sigils
                case 'group':
                    # Group children are called with any default values that
                    # apply to the group itself
                    self.load(view, defaults = view.maps[1:])
                    # Groups don't add any entries of their own so we're done 
                    continue
                case other:
                    # If we don't know what the user just passed us, warn them
                    # and then pretend nothing happened
                    logger.warning('Unknown data type {} in data loading. Skipping...'.format(str(other)))
                    continue

            # Collect the IDs into a set, since duplicates would be meaningless
            if IDs is None:
                # If there was no ID specified, fall back on the display name
                IDs = {view['name']}
            # Sets require different constructions from single values and
            # iterables, so we need to check the type of the input
            elif isinstance(IDs, Iterable) and not isinstance(IDs, str): 
                IDs = set(IDs) 
            else: 
                IDs = {IDs} 
            
            # Set a reference to the object we just constructed for each of its
            # specified identifiers
            for identifier in IDs:
                target[identifier] = parsed
    
    def get_cost(self, name : str) -> Cost:
        """Return the cost associated with that name"""
        return self.costs.get(name, error_cost)

    def get_sigil(self, name : str) -> bodyitems.Sigil:
        """Return the sigil associated with that name"""
        return self.sigils.get(name, error_sigil)
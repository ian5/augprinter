import re
from collections import ChainMap
from collections.abc import Iterable, Mapping, MutableMapping #import creep lol
from typing import cast
from loguru import logger
from PIL import Image
from printer import bodyitems
from printer.loaders import open_image_cached
from printer.printcore import assemble_card
from printer.datatypes import Cost

#TODO: figure out a more elegant solution for this
error_sigil = bodyitems.Sigil(
    'Not Found', open_image_cached('assets/builtin/sigil_error.png'),
    'No sigil by this name was found.')

error_cost = Cost('assets/builtin/costerror.png', 4)

class CardContext: #MARK: CardContext
    """Contextual information for the printing of cards"""
    def __init__(self):
        self.sigils = {}
        self.conditionals = {}
        self.traits = {}
        # Set priority for multiple kinds of body item with the same id
        self.body_items = ChainMap(
            self.conditionals, self.sigils, self.traits)
        self.costs = {}

    def insert(self, entry : Mapping, names : set):
        """Load a single data entry into this store. Accounts for defaults."""
        # Each type of entry requires different parsing
        #TOOD: Is this neccesary now? 
        match entry.get('type', 'Unspecified'):
            case 'cost':
                target = self.costs
            case 'sigil':
                target = self.sigils
            case 'trait':
                target = self.traits
            case 'conditional':
                target = self.conditionals
            case other:
                # If we don't know what this thing is, warn the user and then
                # pretend nothing happened
                logger.warning('Unknown data type {} in data loading. Skipping...'.format(str(other)))
                return       
        for name in names:
            # Assign the value to each name it asked to be associated with
            target[name] = entry

    def get_cost(self, name : str) -> Cost:
        """Return the cost associated with that name"""
        try:
            raw = self.costs[name]
        except KeyError:
            logger.error('Attempt to load unknown cost {}.'.format(name))
            raise
        return self.parse_cost(raw)

    def get_sigil(self, name : str) -> bodyitems.Sigil:
        """Return the sigil associated with that name"""
        try:
            raw = self.sigils[name]
        except KeyError:
            logger.error('Attempt to load unknown sigil {}.'.format(name))
            raise
        return self.parse_sigil(raw)

    @classmethod
    def parse_sigil(cls, raw : Mapping) -> bodyitems.Sigil:
        """Parse the dictionary form of a sigil into the Sigil class"""
        # All the work is done by the sigil initialization function
        return bodyitems.Sigil(**raw)

    @classmethod
    def parse_cost(cls, raw : Mapping) -> Cost:
        """Parse the dictionary form of a cost into the Cost class"""
        return Cost(**raw)
    
    @classmethod
    def parse_trait(cls, raw : Mapping) -> bodyitems.Trait:
        """Parse the dictionary form of a trait into the Trait class"""
        return bodyitems.Trait(**raw)

    # This can't be a class method because conditionals need to be able to look
    # up sigils to parse their children
    def parse_conditional(self, raw : MutableMapping) -> bodyitems.Conditional:
        """Parse a Conditional from dictionary, including contents"""
        # We need to build the contents now if they were given here
        contents = []
        if 'contents' in raw:
            for item in raw['contents']:
                contents.append(self.get_body_item(item))
        # I know the type hint looks silly here, but having part of the mapping
        # be a list scared the linter when passing to the method expecting 
        # a string argument down there
        amended : ChainMap = ChainMap({'contents': contents}, raw)
        return bodyitems.Conditional(**amended)
    
    def parse_body_item(self, raw : MutableMapping) -> bodyitems.BodyItem:
        """Parse a BodyItem, attempting to guess type if unspecified."""
        # Determine what kind of item this is
        guess = raw.get('type', None)
        if guess is None: # They didn't tell us what it was so we have to guess
            if raw.get('icon') is not None: # Only sigils have icons
                guess = 'sigil'
            elif raw.get('text') is not None: # Traits have text and no icon
                guess = 'trait'
            else: # I don't see why you'd have a bespoke conditional but eh
                guess = 'conditional'
        match guess:
            case 'sigil':
                return self.parse_sigil(raw)
            case 'trait':
                return self.parse_trait(raw)
            case 'conditional':
                return self.parse_conditional(raw)
            case err:
                logger.error('Unknown body item type {}.'.format(err))
                raise TypeError
    
    def get_body_item(self, raw : MutableMapping | str) -> bodyitems.BodyItem:
        """Parse a body item, defaulting to a parent's values if one exists."""
        # Syntactic sugar that lets you load an unchanged class faster
        if isinstance(raw, str): raw = {'parent': raw}
        # If we have any default values, we need to fetch them
        if 'parent' in raw:
            try:
                # assuming that raw['parent'] should always work
                defaults = self.body_items[raw['parent']]
            except KeyError:
                logger.error('No body item named {} found'.format(raw['parent']))
                raise
        else:
            defaults = {}
        composite = ChainMap(raw, defaults)
        return self.parse_body_item(composite)
    
class Card(): # MARK: Card
    #TODO: is there a better way to handle the generic properties than this?
    # at the very least I should do the templerarity frame things
    def __init__(self, raw : Mapping):
        self.name = str(raw.get('name', 'Unnamed Card'))
        self.rarity = str(raw.get('rarity', 'No Rarity'))
        self.temple = str(raw.get('temple', 'No Temple'))
        self.portrait = str(raw.get('portrait', 'assets/builtin/portrait_error.png'))
        self.background = str(raw.get('background', 'assets/builtin/background_error.png'))
        self.frame = str(raw.get('frame', 'assets/builtin/frame_error.png'))
        self.flavor = raw.get('flavor', None)
        self.artist = raw.get('artist', 'No Artist')
        # TODO: Validate these properly instead of just assuming they're fine
        self.raw_costs = cast(list, raw.get('costs', []))
        self.tribes = cast(list, raw.get('tribes', [])) 
        self.power = str(raw.get('power', 0))
        self.health = str(raw.get('health', 0))
        self.raw_body = cast(list, raw.get('mainbody', []))
        self.decals = cast(list, raw.get('decals', []))
        c = raw.get('accentcolor', False)
        if c:
            self.accentcolor = (c[0], c[1], c[2], 255)
        self.implications()

    # Should replace this iwth real later
    def implications(self):
        """Apply some automatic decals for certain properties"""
        # Mox band rendering
        if 'Mox' in self.tribes:
            # If we have the Prism Gem sigil
            if self.sigil_test('prismgem'):
                self.decals.append(['assets/misc/gems/moxband_prism.png', [
                    40,840]])
            elif 'Conduit' in self.tribes:
                # Get the appropriate gem
                if self.sigil_test('orangegem'):
                    self.decals.append(['assets/misc/gems/gemO.png',
                                        [530, 850]])                    
                elif self.sigil_test('greengem'):
                    self.decals.append(['assets/misc/gems/gemG.png',
                                        [530, 850]])
                elif self.sigil_test('bluegem'):
                    self.decals.append(['assets/misc/gems/gemB.png',
                                        [530, 850]])
            # Check for normal gems
            else:
                if self.sigil_test('orangegem'):
                    self.decals.append(['assets/misc/gems/gemO.png', [440, 850]])
                if self.sigil_test('greengem'):
                    self.decals.append(['assets/misc/gems/gemG.png', [610, 850]])
                if self.sigil_test('bluegem'):
                    self.decals.append(['assets/misc/gems/gemB.png', [530, 850]])
        elif 'Conduit' in self.tribes:
            self.decals.append(['assets/misc/conduit_large.png', [40, 840]])

    def sigil_test(self, name : str):
        """Check if this card has a bodyitem with a certain ID"""
        return any((n.id==name for n in self.raw_body))

    def print(self, context : CardContext):
        return assemble_card(name = self.name, rarity = self.rarity,
            temple = self.temple, portrait = self.portrait,
            background = self.background, frame = self.frame,
            tribes = self.tribes, power = self.power, health = self.health,
            costs = self.get_costs(context), accentcolor = self.accentcolor,
            mainbody = self.get_body(context), artist = self.artist,
            format = 'Card Loading Test', decals = self.decals)

    def get_costs(self, context : CardContext) -> list[Cost]:
        costs = []
        for entry in self.raw_costs:
            # Match the format used for cost entry
            match = re.match(r"(\d+) (.+)", entry)
            if match is None:
                # If we couldn't match the cost pattern, complain and exit
                logger.warning('Failed to parse cost specifier {}'.format(entry))
                continue
            count, cost = match.groups()
            # We need the count as a number, not a string
            count = int(count)
            # Look up the cost by name in the provided context
            cost = context.get_cost(cost)
            if cost is error_cost:
                # If we couldn't find the cost, complain and exit
                logger.warning('Unknown cost {}'.format(cost))
                continue
            costs.append((cost, count))
        return costs

    def get_body(self, context : CardContext) -> list[bodyitems.BodyItem]:
        """Return the bodyitems of this card, formatted based on its contents"""
        # This maybe handles more logic than it should
        sigils = []
        # Assuming conditionals will always come at the end of the sigil list,
        # other  than their own children
        conditionals = []
        traits = []
        for item in self.raw_body:
            parsed = self.resolve_body_item(item, context)
            # We need to put the item we got back in the right place
            if isinstance(parsed, bodyitems.Sigil):
                sigils.append(parsed)
            elif isinstance(parsed, bodyitems.Trait):
                traits.append(parsed)
            elif isinstance(parsed, bodyitems.Conditional):
                conditionals.append(parsed)
            elif parsed is None:
                logger.warning('Unknown BodyItem type {} in card definition {}'
                               .format(item.get('type'), self.name))
        if (sigils # If we have sigils to render...
            and (traits or self.flavor) # Something to separate them from...
            and (not conditionals)): # And nothing else that's already doing so
            # Add a seperator to the end of the sigil list
            sigils.append(bodyitems.HorizontalRule())
        # If there needs to be something seperating traits and flavor text
        if traits and self.flavor:
            # Do that
            traits.append(bodyitems.HorizontalRule())
        # Concatenate the sections of the card
        body_items = sigils + conditionals + traits 
        if self.flavor: # If we have flavor text add that to the end
            body_items.append(bodyitems.FlavorText(self.flavor))
        return body_items
    
    def resolve_body_item(self, item : MutableMapping, 
                          context : CardContext) -> bodyitems.BodyItem:
        """Get the object of a bodyitem, whether it's explicit or referenced"""
        # is this enough? feels like this should take more work; dereference if 
        # this works?
        return context.get_body_item(item)

# MARK: CardStore
class CardStore():
    def __init__(self):
        """Store for Card objects"""
        self.lookup : dict[str, Card] = dict() 
        self.cards : set[Card] =  set()
    
    def insert(self, raw, names):
        """Add a card to this object from its dictionary representation"""
        card = Card(raw)
        self.cards.add(card)
        for name in names:
            self.lookup[name] = card

    def get_card(self, card : str) -> Card:
        """Retrieve a card object by name"""
        try: 
            return self.lookup[card]
        except KeyError:
            logger.error('Card {} not found.'.format(card))
            raise

    def __iter__(self):
        return iter(self.cards)

# MARK: DataParser
class DataParser():
    def __init__(self, context : CardContext = CardContext(),
                 cards : CardStore = CardStore()):
        """Mechanism for loading data from the description format"""
        self.context = context
        self.cards = cards

    def parse(self, raw : Mapping, defaults : Iterable = []):
        """Parse a set of data entries and pass them to the managed stores"""
        # Note any properties that apply to all objects in this list
        default_properties = raw.get('default', {})
        # For each entry...
        for entry in raw.get('contents', {}):
            # Use global values if they aren't overwritten
            # This is also where any parent groups' defaults are incorporated
            view = ChainMap(entry, default_properties, *defaults)
            IDs = view.get('id')
            # Figure out what we're dealing with; assume it's a group if it's
            # empty for syntactic convenience
            kind = view.get('type', 'group')
            # If it is a group, we need to do group parsing instead of treating
            # it as an entry
            if kind == 'group':
                # Group children are called with any default values that
                # apply to the group itself
                self.parse(view, defaults = view.maps[1:])
                continue
            # Collect the IDs into a set, since duplicates would be meaningless
            # If no ID was specified, fall back on the display name
            if IDs is None:
                IDs = {view.get('name')}
            # Sets require different constructions for single values and
            # iterables, so we need to check the type of the input
            # (also, we want to treat strings as non iterable)
            elif isinstance(IDs, Iterable) and not isinstance(IDs, str): 
                IDs = {identifier for identifier in IDs}
            else: 
                IDs = {IDs} # Turn a single value into a set of one
            
            # Each type of entry requires different parsing
            match view.get('type', 'group'):
                case 'cost' | 'sigil' | 'trait' | 'conditional':
                    self.context.insert(view, IDs)
                case 'card':
                    self.cards.insert(view, IDs)
                case other:
                    # If we don't know what the user just passed us, warn them
                    # and then pretend nothing happened
                    logger.warning('Unknown data type {} fed to parser. Skipping...'.format(str(other)))
                    continue

    def print(self, name : str) -> Image.Image:
        """Prints the stored card holding this name."""
        # Find what card we're printing and print it
        card = self.cards.get_card(name)
        return card.print(self.context)
import copy
from printer import config
from printer.bodyitems import Sigil, Conditional, InfoBox, HorizontalRule, Trait, FlavorText
from printer import printcore

def spoofed_source():
    """Return a big fake dictionary to test the loaders"""
    return {
        'items': {
            'brittle': {
                'type': 'Sigil',
                'name': 'Brittle',
                'icon': 'assets/sigils/Brittle.png',
                'text': 'If this card attacked this turn, it perishes during your end step.',
            },
            'bonedigger': {
                'type': 'Sigil',
                'name': 'Bone Digger',
                'icon': 'assets/sigils/Brittle.png',
                'text': 'During your end step, gain 1 bone.',
            }
        },
        'cards': {
            'skeleton': {
                'name': 'Skeleton',
                'portrait': 'assets/art/Skeleton.png',
                'tribes': ['Skeleton'],
                'rarity': 'Side Deck',
                'power': 1, 'health': 1,
                'artist': 'pixelprofligate probably?',
                'costs': [],
                'background': 'assets/bg/bg_common_undead.png',
                'frame': 'assets/frames/frame_common_undead.png',
                'body': [
                    'Brittle',
                    'Bone Digger',
                    {
                        'type': 'FlavorText',
                        'text': 'A frail and spooky mass of bones.'
                    }
                ]
            }
        }
    }

class CardData:
    """Store for the data of a given set of cards and carditems."""
    
    def __init__(self, definition: dict) -> None:
        # We copy these so that if another format shadows them later it doesn't
        # mutate the original dict we got
        # Load items
        self.items = copy.deepcopy(definition.get('items', {}))
        # Load cards
        self.cards = copy.deepcopy(definition.get('cards', {}))
    
    def print_card(self, name):
        """Pass the data of a given card along to the printcore functions"""
        pass
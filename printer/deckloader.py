# Utilities to export cards to the Deck Loader format
import json
from typing import Iterable
from printer.parse import Card

def cards_to_json(cards : Iterable[Card], printing_nane : str='AUG') -> str:
    store = {
        'config': {
            'default_back': '[Replace with actual default back url]',
            'prefix': '[Replace with actual prefix]',
            'suffix': '[Replace with actual suffix]',
        },
        'cards': []
    }
    card_store = store['cards']
    for card in cards:
        card_store.append({
            'id': card.name,
            'name': card.name,
            'printings': {
                printing_nane: card.name,
            }
        })
    return json.dumps(store)
# Handles standard operations in a way that acts more like a user would expect
# Frontend for the backend to serve as the backend of the frontend
from itertools import chain
from typing import Iterable
import yaml
from PIL import Image
from printer import parse
from printer.config import config
from printer.deckloader import cards_to_json

documents = config['content']

def load_documents(cards : Iterable[str] = documents, 
                   parser : parse.DataParser | None = None)->parse.DataParser:
    """Parses a collection of documents into cardcontext
    
    Parameters
    ----------
    cards : Iterable[str]
        A collection of the paths of the documents to be parsed. Defaults to
        the config's "content" field
    parser : DataParser
        The parser to load items into; by default, a new empty one is created
    """
    # If we aren't updating an existing parser, we need a new one.
    if parser is None:
        parser = parse.DataParser()
    # We both need to check every physical file and load every YAML document
    # within the files
    for path in cards:
        with open(path) as f:
            for doc in yaml.load_all(f, yaml.Loader):
                parser.parse(doc)
    return parser

def print_cards(cards : Iterable[str], 
                parser : parse.DataParser) -> dict[str, Image.Image]:
    """Print a dictionary of cards by name, given a populated parser"""
    output = {}
    for card in cards:
        output[card] = parser.print(card)
    return output

def print_all_cards(parser : parse.DataParser) -> dict[str, Image.Image]:
    """Print a dictionary of all loaded cards in a parser."""
    return parser.print_all()


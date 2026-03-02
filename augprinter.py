from typing import Callable
from sys import stderr
from loguru import logger
from printer import utils, config, parse

def driver_loop(): 
    # This is a very nice state machine implementation I found on Guido van
    # Rossum's blog Neopythonic, though it's actually attributed to Ian Bicking
    func, args = home, ()
    while True:
        # god pylance was so confused about this bullshit
        func, args = func(*args) # type: ignore

# Basic state
def home() -> tuple[Callable, tuple]:
    match input("""===Augmented Printer Internal Bodge===
1) Print card by name
2) Print card by name, repeatedly
3) Print all cards in format
4) Utilities
0) Exit
>"""):
        case '1': # Single card
            return single_card, (False,)
        case '2': # Named cards
            return single_card, (True,)
        case '3':
            return dump_format, ()
        case '4':
            return utilities, ()
        case '0':
            raise SystemExit
    return home, ()

def utilities():
    match input("""===Utilities===
1) List all loaded cards
0) Return
>"""):
        case '1':
            return count_cards, ()
        case '0':
            return home, ()

def count_cards():
    format = utils.load_documents()
    for card in format.cards.cards:
        print(card.name)
    print(f'{len(format.cards.cards)} cards registered.')
    return utilities, ()

def single_card(interactive : bool, 
                card_name : str | None = None) -> tuple[Callable, tuple]:
    if card_name is None:
        # State initialization
        card_name = input('Enter card name >')
    # Load data specified in config.yaml
    format = utils.load_documents()
    # Fetch the relevant card
    card = format.cards.get_card(card_name)
    print('Card {} fetched...'.format(card.name))
    # Print it to image, with the contextual info we just loaded
    image = card.print(format.context)
    print('Printed successfully...')
    # Save the card by name
    image.save(f'output/{card.name}.png')
    print('File saved!')
    # If we're running in interactive mode
    if interactive:
        # Display the card we just printed to the user
        image.show()
        # Ask them if they want to do it again
        if input('Enter exit to exit, anything else prints again >')!='exit':
            return single_card, (True, card_name)
    return home, ()

def dump_format() -> tuple[Callable, tuple]:
    dump = input('Dump JSON? (y/n) >')=='y'
    # Load data as specified in config.yaml
    format = utils.load_documents(parser=parse.DataParser())
    # Print every card to an image
    cards = utils.print_all_cards(format)
    # Save each card to file
    for name, card in cards.items():
        card.save(f'output/{name}.png')
    print(f'{len(cards)} cards printed.')
    # If we need to produce a JSON dump
    if dump:
        # Push the JSON dump to the output directory
        json = utils.cards_to_json(format.cards)
        try: 
            with open('output/Deckloader.json', mode='x') as f:
                f.write(json)
            print('JSON dumped!')
        # If the file exists already
        except FileExistsError:
            # Ask to overwrite it first
            if input('Deckloader.json exists. Overwrite? (y/n) >')=='y':
                with open('output/Deckloader.json', mode='w') as f:
                    f.write(json)
                    print('JSON dumped!')
            else:
                print('JSON dump aborted.')
    return home, ()

if __name__ == '__main__':
    # Hide debug level messages when running as an application
    logger.remove()
    logger.add(stderr, level='INFO')
    driver_loop()
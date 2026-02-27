import yaml
from PIL import Image
from loguru import logger
from printer.printcore import assemble_card
from printer.bodyitems import Sigil, Conditional, InfoBox, HorizontalRule, Trait, FlavorText
from printer.datatypes import Cost
from printer.parse import Card, CardContext, DataParser
from printer.deckloader import cards_to_json

def build_test_cards():
    blood = Cost('assets/cost/blood.png', 5)
    energy = Cost('assets/cost/energy.png', 7)
    cells = Cost('assets/cost/overcharge.png', 7)
    cards = {}
    cards['sigiltester.png'] = (assemble_card(portrait='assets/art/Skeleton.png', background='assets/bg/bg_common_undead.png', frame='assets/frames/frame_common_undead.png',
                body=[
                    Sigil('Long Test', 'assets/sigils/Bone Digger.png', "This sigil has very long text that is being used to ensure text wrapping hasn't blown up somehow. Here's a few more words, so it's taller than the icon."),
                    Sigil('Test Sigil', 'assets/sigils/Brittle.png', 'This sigil is short.'), 
                    InfoBox([
                        Sigil('White Sigil', 'assets/sigils/Airborne.png', "This sigil is being rendered in an infobox.")
                    ])
                ],
                tribes=['Test Card'], rarity='Fake As Shit', temple='Undead', power=1, health=1, name='Sigil Tester', artist='PixelProfligate', costs=[], format='TEST')
    )
    cards['bodyitemtester.png'] = (assemble_card(portrait='assets/art/Child 13.png', background='assets/bg/bg_rare_beast.png', frame='assets/frames/frame_rare_beast.png', artist='Raytheon',
                tribes=['Hooved', 'Cryptid'], rarity='Fake As Shit', temple='Beast', power=4, health=4, name='BodyItem Tester', costs=[(blood, 1)], format='TEST',
                body = [  
                    Trait('This card is being used as a pretty inelegant test for the card printer.'),
                    Conditional('assets/misc/VALORCELL.png'),
                    HorizontalRule(),
                    FlavorText("Yes, I know sigils are also BodyItems. They're more complex than other BodyItems, and they take up a lot of space, so they got their own card.")
                ])
    )
    cards['othertester.png'] = assemble_card(portrait='assets/art/Skel-e-latcher.png', background='assets/bg/bg_common_magick.png', frame='assets/frames/frame_common_magick.png', artist='Raytheon',
                tribes=['Latcher'], rarity='Fake As Shit', temple='Tech', power='assets/variable/Mirror Power.png', health=1, name='OtherTester', costs=[(energy, 5), (cells, 2)], format='TEST',
                decals = [('assets/misc/gems/moxband_3empty.png', (40, 840)), ('assets/misc/gems/gemO.png', (440, 850))], body = [
                    FlavorText("This card is being used to test decals and variable powers, so it doesn't actually need a meaningful body. I was gonna give you a funny big infobox instead, but apparently flavortext doesn't work when rendered inside of an infobox, and given that that's not really real behavior, I've elected not to fix it, so you have to settle with funny long flavortext instead.")
                ])
    cards['tokentester.png'] = assemble_card(portrait='assets/art/Energy Bot.png', background='assets/bg/bg_common_tech.png', frame='assets/frames/frame_common_tech.png', artist='Raytheon',
                tribes=['Latcher'], rarity='Fake As Shit', temple='Tech', power='assets/variable/Mirror Power.png', health=1, name='TokenTester', costs=[(blood, 2), (cells, 2)], format='TEST',
                decals = [('assets/misc/gems/moxband_3empty.png', (40, 840)), ('assets/misc/gems/gemO.png', (440, 850))], body = [
                    Sigil('Token Test', 'assets/sigils/Frozen Away.png', "This sigil is a test for the token system; there's a token {token} in this sigil.", tokens={'token':'spoobus'}),
                ])
    cards['conditional.png'] = assemble_card(portrait='assets/art/Child 13.png', background='assets/bg/bg_rare_beast.png', frame='assets/frames/frame_rare_beast.png', artist='Raytheon',
                tribes=['Hooved', 'Cryptid'], rarity='Fake As Shit', temple='Beast', power=4, health=4, name='BodyItem Tester', costs=[(blood, 1)], format='TEST',
                body = [ 
                    Conditional('assets/misc/LATCH.png',
                                [
                        Sigil('Other Sigil', 'assets/sigils/Bone Digger.png', "This sigil is first even though it's the other sigil. It's also long enough to wrap."),
                        Sigil('Test Sigil', 'assets/sigils/Brittle.png', 'This sigil is short.'), 
                                ]),
                    FlavorText("This is the latest test by far")
                ])
    return cards

def show_card_class_test():
    context = CardContext()
    context.insert({
        'name': 'Testing Sigil',
        'body': 'Sigil test',
        'icon': 'assets/sigils/Frozen Away.png'
    }, {'Testing Sigil'})
    card = Card({
        'id': 'TestCard',
        'name': 'Loading Test',
        'portrait': 'assets/art/Horse.png',
        'frame': 'assets/frames/frame_rare_beast.png',
        'background': 'assets/bg/bg_rare_beast.png',
        'tribes': ['Hooved', 'Wizard'],
        'rarity': 'Rare', 'temple': 'Beast', 'power': 1, 'health': 6,
        'flavor': 'Test Flavor Text',
        'body': [
            'Testing Sigil'
        ]
    })
    card.print(context).show()

def save_test_cards():
    for name, card in build_test_cards().items():
        card.save('output/{}'.format(name))

def show_test_cards():  
    for name, card in build_test_cards().items():
        card.show('output/{}'.format(name))

def card_parsing_test(path : str, name : str | None = None, 
                      save : bool = False, json : bool = False):
    parser = DataParser()
    with open(path) as f:
        for doc in yaml.load_all(f, yaml.Loader):
            logger.debug(doc)
            parser.parse(doc)
    results : dict[str, Image.Image] = {}
    if name:
        results[name] = parser.print(name)
    else:
        for card in parser.cards:
            logger.info('Printing {}'.format(card))
            results[card.name] = card.print(parser.context)
    if save:
        for name, card in results.items():
            card.save('output/{}.png'.format(name))
    else:
        for card in results.values():
            card.show()
    if json:
        logger.info(cards_to_json(parser.cards))

card_parsing_test('data/test_suite_cards.yaml', save=True, json=True)

input('pause lol')

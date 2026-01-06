from printer.printcore import assemble_card
from printer.bodyitems import Sigil, Conditional, InfoBox, HorizontalRule, Trait, FlavorText
from printer.parse import Cost
from printer.config import fonts


def build_test_cards():
    blood = Cost('assets/cost/blood.png', 5)
    energy = Cost('assets/cost/energy.png', 7)
    cells = Cost('assets/cost/overcharge.png', 7)
    cards = {}
    cards['sigiltester.png'] = (assemble_card(portrait='assets/art/Skeleton.png', background='assets/bg/bg_common_undead.png', frame='assets/frames/frame_common_undead.png',
                mainbody=[
                    Sigil('Long Test', 'assets/sigils/Bone Digger.png', "This sigil has very long text that is being used to ensure text wrapping hasn't blown up somehow. Here's a few more words, so it's taller than the icon."),
                    Sigil('Test Sigil', 'assets/sigils/Brittle.png', 'This sigil is short.'), 
                    InfoBox([
                        Sigil('White Sigil', 'assets/sigils/Airborne.png', "This sigil is being rendered in an infobox.", blacked=True)
                    ])
                ],
                tribes=['Test Card'], rarity='Fake As Shit', temple='Undead', power=1, health=1, name='Sigil Tester', artist='PixelProfligate', costs=[], format='TEST')
    )
    cards['bodyitemtester.png'] = (assemble_card(portrait='assets/art/Child 13.png', background='assets/bg/bg_rare_beast.png', frame='assets/frames/frame_rare_beast.png', artist='Raytheon',
                tribes=['Hooved', 'Cryptid'], rarity='Fake As Shit', temple='Beast', power=4, health=4, name='BodyItem Tester', costs=[(blood, 1)], format='TEST',
                mainbody = [  
                    Trait('This card is being used as a pretty inelegant test for the card printer.'),
                    Conditional('assets/misc/VALORCELL.png'),
                    HorizontalRule(),
                    FlavorText("Yes, I know sigils are also BodyItems. They're more complex than other BodyItems, and they take up a lot of space, so they got their own card.")
                ])
    )
    cards['othertester.png'] = assemble_card(portrait='assets/art/Skel-e-latcher.png', background='assets/bg/bg_common_magick.png', frame='assets/frames/frame_common_magick.png', artist='Raytheon',
                tribes=['Latcher'], rarity='Fake As Shit', temple='Tech', power='assets/variable/Mirror Power.png', health=1, name='OtherTester', costs=[(energy, 5), (cells, 2)], format='TEST',
                decals = [('assets/misc/gems/moxband_3empty.png', (40, 840)), ('assets/misc/gems/gemO.png', (440, 850))], mainbody = [
                    FlavorText("This card is being used to test decals and variable powers, so it doesn't actually need a meaningful body. I was gonna give you a funny big infobox instead, but apparently flavortext doesn't work when rendered inside of an infobox, and given that that's not really real behavior, I've elected not to fix it, so you have to settle with funny long flavortext instead.")
                ])
    return cards

def save_test_cards():
    for name, card in build_test_cards().items():
        card.save('output/{}'.format(name))

def show_test_cards():  
    for name, card in build_test_cards().items():
        card.show('output/{}'.format(name))

save_test_cards()
# card_printer = reader.CardData(reader.spoofed_source())
# card_printer.print('skeleton').show()
input('pause lol')

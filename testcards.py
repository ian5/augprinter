from printer.printcore import assemble_card
from printer.bodyitems import Sigil, Conditional, InfoBox, HorizontalRule, Trait, FlavorText
from printer.config import fonts

assemble_card(portrait='assets/art/Skeleton.png', background='assets/bg/bg_common_undead.png', frame='assets/frames/frame_common_undead.png',
              mainbody=[
                Sigil('Bone Digger', 'assets/sigils/Bone Digger.png', 'During your end step, gain 1 bone.'),
                #HorizontalRule(),
                #Trait('This card cannot be sacrificed.'),
                Conditional('assets/misc/TRANSFORM.png', []),
                Sigil('Brittle', 'assets/sigils/Brittle.png', 'If this card attacked this turn, it perishes during your end step.'), 
                InfoBox([
                    Sigil('Airborne', 'assets/sigils/Airborne.png', "When this card would strike another, it instead strikes that card's space directly.", blacked=True)
                ]),
                #HorizontalRule(),
                #FlavorText('A frail and spooky mass of bones.')
              ],
              tribes=['Skeleton'], tier='Side Deck', temple='Undead', power=0, health=1, name='Skeleton', artist='Vivziepop', costs=[]).show()

assemble_card(portrait='assets/art/Child 13.png', background='assets/bg/bg_rare_beast.png', frame='assets/frames/frame_rare_beast.png', artist='Raytheon',
              tribes=['Hooved', 'Cryptid'], tier='Rare', temple='Beast', power=0, health=1, name='Child 13', costs=[('assets/cost/blood.png', 1, False)],
              mainbody = [  
                  Sigil('Many Lives', 'assets/sigils/Many Lives.png', "This card does not perish when sacrificed."),
                  Conditional('assets/misc/SACLOOP.png'),
                  Sigil('Empowered', 'assets/sigils/Empowered.png', "This card has 2 more power."),
                  Sigil('Airborne', 'assets/sigils/Airborne.png', "When this card would strike another, it instead strikes that card's space directly."),
                  HorizontalRule(),
              ]).show()

assemble_card(portrait='assets/art/Skel-e-latcher.png', background='assets/bg/bg_common_tech.png', frame='assets/frames/frame_common_tech.png', artist='Raytheon',
              tribes=['Latcher'], tier='Common', temple='Tech', power='assets/variable/Mirror Power.png', health='assets/variable/Mirror Power.png', name='Skel-e-latcher', costs=[('assets/cost/energy.png', 5, True)],
              decals = [('assets/misc/gems/moxband_3empty.png', (40, 840)), ('assets/misc/gems/gemO.png', (440, 850))], mainbody = [
                  Conditional('assets/misc/LATCH.png', contents = [
                      Sigil('Brittle', 'assets/sigils/Brittle.png', "If this card attacked this turn, it perishes during your end step.", blacked=True)
                  ]),
                  Trait("The affected card will only perish from ""Brittle"" if it had it before attacking."),
                  HorizontalRule(),
                  FlavorText('Full of neurotoxins.')
              ]).show()

input('pause lol')

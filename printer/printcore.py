import typing
from typing import Sequence
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from loguru import logger
from printer.config import format_schema, renderstep_styles
from printer.loaders import open_image_cached, open_font_cached, get_image
from printer.text import TextStyle

Font = ImageFont.ImageFont | ImageFont.FreeTypeFont

# TODO: X position handling through this whole thing is jank af

#MARK: Assemble Card
def assemble_card(power: str | int = '0', health: str | int = '0', rarity: str = 'rarityless', temple: str = 'templeless',
                  tribes: Sequence | None = None, name: str = 'Unnamed Card', artist: str = 'No Artist',
                  format: str = 'no format string lol', decals : Sequence[tuple[Image.Image|str, tuple[int, int]]] = [],
                  accentcolor : tuple[int,int,int,int] | None = None,
                  **kwargs) -> Image.Image:
    """Create and return a card image given the pieces of a card.

    Given the information of a card, return the card as an image.
    Tribes should be provided as a sequence of strings, even if there
    is only 1 tribe.

    Parameters
    ----------
    background, frame, portrait : Image or string, optional
        Image assets for the card. Accept an image object or a path.
    power, health : string
        Values to print in the card's stat boxes
    rarity, temple : string
        Values to print in the card's tribeline
    body: Sequence of BodyRenderer objects
        Sequence of things that go in the card's main body; in the
        specific context of aug this is sigils, traits, conditionals,
        and flavor text
    tribes : Sequence of strings
        Sequence of tribes the card has
    artist : str
        Creator of the portrait
    costs : Sequence of tuples, of the form (icon, number, compact)
        A Sequence containing each cost of the card; requires the icon
        the cost uses and the number, and then optionally specify to
        render them compactly

    Returns
    -------
    Image
        The constructed card's image.
    """
    # Create card image
    image = Image.new("RGBA",format_schema.get('card size', (112,156)))

    #draw_layer(image, format_schema['rendersteps']['lores'], kwargs)

#    for layer in format_schema['rendersteps'].values():
#        for renderstep in layer:
#            renderstep.draw(image, kwargs)
    for renderstep in format_schema['rendersteps']['lores']:
        renderstep.draw(image, kwargs)

    # if we weren't given one, pick the accent color with the old method
    if accentcolor is None:
        accentcolor = typing.cast(tuple[int, int, int, int], image.getpixel((66,18)))
        logger.warning('No accentcolor specified for card {}, picked color {}'.format(name, accentcolor))

    # Scale the image up then get a new draw wrapper
    scale_factor = format_schema.get('scale factor', 10)
    image = image.resize((image.width*scale_factor,image.height*scale_factor),resample=Image.Dither.NONE) #MARK: Card Upscale
    draw = ImageDraw.Draw(image)

    # Draw stats TODO: Variable power
    power, health = str(power), str(health)
    for v, x in [(power, 180), (health, 940)]: # TODO: pretend this is forwards compatibility and not laziness
        try:
            length = renderstep_styles['stats'].get_length(str(int(v)))
            renderstep_styles['stats'].print_line(str(int(v)), draw,
                (int(x - length/2), 1331), (255, 255, 255))
        except ValueError: # it was actually a variable power and not an integer
            with get_image(v) as icon:
                image.alpha_composite(icon, (int(x-icon.width/2), 1351))
    #shadow_text(draw,968,1331,str(int(health)),statFont,anchor="ra")

    # sigils
    for renderstep in format_schema['rendersteps']['hires']:
        renderstep.draw(image, kwargs)

    # Tribeline (includes rarity and temple)
    tribe_string = '{} {}'.format(rarity, temple) if tribes == None else '{} {} - {}'.format(rarity, temple, ' '.join(tribes))
    renderstep_styles['tribeline'].print_line(tribe_string, draw, (151,1295), 
                                              accentcolor[:3])
    # Draw name
    renderstep_styles['name'].print_line(name, draw, (136, 136), (255,255,255))
    # Art credit
    renderstep_styles['artist'].print_line('Illus. {}'.format(artist),
                                           draw, (560, 1375), (255, 255, 255),
                                           anchor='ma')
    # Oh yeah and the version too
    renderstep_styles['format'].print_line(format, draw, (560,1483), 
                                           accentcolor[:3], anchor='ma')
    # draw the decals
    for icon, pos in decals:
        with get_image(icon) as i:
            image.alpha_composite(i, pos)

    return image

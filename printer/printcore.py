import typing
from typing import Sequence
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from loguru import logger
from printer.config import format_schema
from printer.loaders import open_image_cached, open_font_cached, get_image

Font = ImageFont.ImageFont | ImageFont.FreeTypeFont

# TODO: X position handling through this whole thing is jank af

# TODO: data driven
nameFont = ImageFont.truetype('assets/fonts/Poly-Regular.ttf', 63)
statFont = ImageFont.truetype('assets/fonts/Cambria.otf', 109)
textFont = ImageFont.truetype('assets/fonts/Cambria.otf', 33)
boldFont = ImageFont.truetype('assets/fonts/Cambria-Bold.ttf', 33)
italFont = ImageFont.truetype('assets/fonts/Cambria-Italic.ttf', 33)
artsFont = ImageFont.truetype('assets/fonts/Poly-Regular.ttf', 42)
formatFont = ImageFont.truetype('assets/fonts/Cambria.otf', 20)

def shadow_text(image : ImageDraw.ImageDraw, x : int, y : int, text : str, font : Font, anchor : str ="la") -> None: # TODO make this not so inflexible-
    image.text((x+5,y+5), text, fill=(0,0,0), font=font, anchor=anchor)
    image.text((x,y), text, fill=(255,255,255), font=font, anchor=anchor)

def draw_layer(image: Image.Image, items: Sequence[dict], params: dict) -> None: #MARK: Draw Layer
    pass

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
            length = statFont.getlength(str(int(v)))
            shadow_text(draw,int(x - length/2),1331,str(int(v)),statFont)
        except ValueError: # it was actually a variable power and not an integer
            with get_image(v) as icon:
                image.alpha_composite(icon, (int(x-icon.width/2), 1351))
    #shadow_text(draw,968,1331,str(int(health)),statFont,anchor="ra")

    # sigils
    for renderstep in format_schema['rendersteps']['hires']:
        renderstep.draw(image, kwargs)

    # Tribeline (includes rarity and temple)
    tribe_string = '{} {}'.format(rarity, temple) if tribes == None else '{} {} - {}'.format(rarity, temple, ' '.join(tribes))
    draw.text((151,1295), tribe_string, fill=accentcolor, font=textFont, anchor="la")

    # Draw name
    shadow_text(draw,136,136,name,nameFont)

    # Art credit
    shadow_text(draw,560,1375,"Illus. {}".format(artist),artsFont,anchor="ma")

    # Oh yeah and the version too
    draw.text((560,1483),format,fill=accentcolor,font=formatFont,anchor="ma")

    # draw the decals
    for icon, pos in decals:
        with get_image(icon) as i:
            image.alpha_composite(i, pos)

    return image

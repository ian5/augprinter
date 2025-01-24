import functools
import typing
from typing import Sequence
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from loguru import logger

Font = ImageFont.ImageFont | ImageFont.FreeTypeFont

# TODO: X position handling through this whole thing is jank af

# fonts TODO: data driven
nameFont = ImageFont.truetype('assets/fonts/Poly-Regular.ttf', 63)
statFont = ImageFont.truetype('assets/fonts/Cambria.otf', 109)
textFont = ImageFont.truetype('assets/fonts/Cambria.otf', 33)
boldFont = ImageFont.truetype('assets/fonts/Cambria-Bold.ttf', 33)
italFont = ImageFont.truetype('assets/fonts/Cambria-Italic.ttf', 33)
artsFont = ImageFont.truetype('assets/fonts/Poly-Regular.ttf', 42)
formatFont = ImageFont.truetype('assets/fonts/Cambria.otf', 20)

#costnumbers = {c:Image.open('assets/builtin/{}.png'.format(c)) for c in ['0','1','2','3','4','5','6','7','8','9','x']}
#before i decided to have cost images cached, i manually loaded the numbers in advance, instead of letting them ride along with the cache
@functools.cache
def open_image_cached(path: str):
    """Open an image and keep it loaded."""
    img = Image.open(path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    return img

def wrap_text(text: str, w: int, font: ImageFont.ImageFont | ImageFont.FreeTypeFont | None = None, first_line_offset: int = 0) -> list[str]:
        """Split a string into a list of strings that each fit within a given horizontal space.
        
        Parameters
        ----------
        text : str
            The string to be split
        w : int
            The width of available space in pixels. If no font is provided, instead the width in characters
        font : ImageFont
            The font to use; if unspecified, this function works in characters instead of pixels
        first_line_offset : int
            An offset to apply to the first line; negative values can be used to account for a hanging indentation
        """
        if font is None:
            logger.debug('monospaced wrapping string "{}"'.format(text))            
        else:
            logger.debug('wrapping string "{}" with font {}'.format(text, font))
        x = first_line_offset
        lines = []
        current_line = []
        for word in (n+' ' for n in text.split()): # Add a space to each word, to account for the one we ate in the split
            if font is None:
                length = 1
            else:
                length = font.getlength(word)
            if x + length > w:
                x = 0
                lines.append(''.join(current_line))
                current_line = []
            x += length
            current_line.append(word)
        lines.append(''.join(current_line)) # We know there will always be at least one word on a line that isn't wrapped, because for a wrap to happen such a word must exist
        return lines

class get_image:
    def __init__(self, image : Image.Image | str, default : Image.Image | str | None = None):
        """If passed an image, pass it through the context manager and leave it alone. If passed a path, load that path and close the file when you're done.
               
        Raises
        ------
        FileNotFoundError
            No default was provided, and the file requested does not exist.
        """
        self.image = image
        self.default = default
        self.close = False
        pass

    def __enter__(self) -> Image.Image: # This is perhaps unnecessarily forgiving to the caller, because I don't know how everything works out yet
        """Locate based on a resource, or pass through an image as a context manager."""
        extensions = ['.png', '.jpg', '.jpeg', '.bmp']
        try: # What if they just pass a path outright
            self.image = typing.cast(str, self.image) # assume that image is a string
            self.managed = Image.open(self.image)
            self.close = True
            logger.debug('get_image loaded {}'.format(self.image))
        except AttributeError: # This is actually already an image and not a path
            self.image = typing.cast(Image.Image, self.image) # sike it was actually an image
            self.managed = self.image
            self.close = False
            logger.debug('get_image passed image through')
        except FileNotFoundError: # Test if they skipped a file extension
            for extension in extensions:
                try:
                    self.image = typing.cast(str, self.image)
                    self.managed = Image.open(self.image+extension)
                    self.close = True
                    logger.debug('get_image loaded {} with extension {}'.format(self.image, extension))
                    break
                except FileNotFoundError:
                    self.close = True
            if self.close: # reusing the close variable to see if we found one
                if self.default is None:
                    raise(FileNotFoundError('get_image did not find image {}'.format(self.image)))
                else:
                    try:
                        self.default = typing.cast(str, self.default)
                        self.managed = Image.open(self.default)
                        self.close = True
                        logger.warning('get_image did not find image {}, loading default at {}'.format(self.image, self.default))
                    except AttributeError: # default is an image and not a path, don't close it
                        self.default = typing.cast(Image.Image, self.default)
                        self.managed = self.default
                        self.close = False
                        logger.warning('get_image did not find image {}, using default'.format(self.image, self.default))
        if self.managed.mode != 'RGBA':
            self.managed = self.managed.convert('RGBA')
        return self.managed
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Close the image resource, if you were the one who opened it."""
        if self.close:
            self.managed.close() # is this enough? i guess i'll find out in production :P

class BodyItem: #MARK: Body Items
    def __init__(self) -> None:
        pass

    def draw(self, image, x, y) -> int:
        return 0
    
    def get_height(self, y) -> int:
        return 0

class Sigil(BodyItem):
    """A sigil to be drawn onto a card. Also supports the reminder sigil background.
    
    Parameters
    ----------
    icon : image or path to image
        The icon of the sigil
    text : string
        The body text of the sigil
    render_color : tuple[float,float,float]
        The color to render the text and if the blacked parameter is true the icon with
    blacked : bool
        If true, render the sigil in forced monocolor; used for infobox rendering
    outlineicon : image or path to image
        A special icon, used when the sigil needs to be rendered in a reminder box; ignores render_color if provided"""
    def __init__(self, name: str, icon: str | Image.Image, text: str, blacked : bool = False, outlineicon: str | Image.Image | None = None) -> None:
        self.name = name
        self.icon = icon
        self.blacked = blacked
        self.titlewidth = int(boldFont.getlength(self.name + ': '))
        self.text = wrap_text(text, w = 750, font=textFont, first_line_offset=self.titlewidth) # split into lines now, since we don't need the raw description later
        self.outlineicon = outlineicon
    
    def draw(self, image: Image.Image, x: int, y: int, blacked: bool = False) -> int:
        draw = ImageDraw.Draw(image)
        if self.blacked: # Are we being drawn in an infobox?
            if self.outlineicon is not None: # If we have a special case sigil, just use that
                with get_image(self.outlineicon, default = open_image_cached('assets/builtin/sigil_error.png')) as icon:
                    image.alpha_composite(icon, (x, y))
            else: # If we don't, make the sigil render as a single color (white, for aug purposes)
                with get_image(self.icon, default = open_image_cached('assets/builtin/sigil_error.png')) as icon:
                    blacked_icon = Image.new('RGBA', icon.size, 'white')
                    blacked_icon.putalpha(icon.getchannel('A'))
                    image.alpha_composite(blacked_icon, (x, y))
        else: # If we're not, just render the icon normally
            with get_image(self.icon, default = open_image_cached('assets/builtin/sigil_error.png')) as icon:
                image.alpha_composite(icon, (x, y))
        text_color = 'white' if self.blacked else 'black' # lol 
        # Render the sigil text
        if len(self.text) == 1: # vertically center single line text
            draw.text((x+80, y+15), self.name+": ", fill=text_color, font=boldFont, anchor="la") # name
            draw.text((x+80+self.titlewidth, y+15), self.text[0], fill=text_color, font=textFont, anchor="la") # text
        else:
            draw.text((x+80, y-5), self.name+": ", fill=text_color, font=boldFont, anchor="la") # name
            for i, line in enumerate(self.text):
                draw.text((x+80+self.titlewidth if i==0 else x+80, y-5+40*i), line, fill=text_color, font=textFont, anchor="la") # text
        return self.get_height(y)

    def get_height(self, y : int) -> int:
        return 40*max(2, len(self.text)) # 40px per line of text, sigils are a minimum of 2 lines tall


class PixelAligned(BodyItem):
    def __init__(self, image : Image.Image | str) -> None: # TODO take another look at this whole thing, it's kinda a clusterfuck
        """Draws an image aligned to the lores pixel grid, snapping downwards."""
        self.image = image
        with get_image(self.image) as img:
            self.image_height = img.height

    def pixel_align(self, y : int) -> int:
        return 10*(y//10) #TODO: this needs to support different resolutions

    def draw(self, image: Image.Image, x: int, y: int) -> int:
        with get_image(self.image) as img:
            image.alpha_composite(img, (0, self.pixel_align(y)))
        return self.get_height(y)
    
    def get_height(self, y) -> int:
        return self.pixel_align(y) - y + self.image_height
    
class HorizontalRule(PixelAligned):
    def __init__(self):
        """Convenience function; just a PixelAligned which is always the seperator bar."""
        return super().__init__(open_image_cached('assets/builtin/separator_large.png'))

class InfoBox(PixelAligned):
    def __init__(self, children : Sequence[BodyItem]):
        self.children = list(children)
        self.contents = Image.new('RGBA', (1120,1560)) # magic number; the second number here is arbirary, pretty much
        self.content_height = 0
        for o in self.children:
            self.content_height += o.draw(self.contents, 0, self.content_height)

    def draw(self, image: Image.Image, x : int, y : int) -> int:
        box = open_image_cached('assets/builtin/darkbox.png')
        py = self.pixel_align(y)
        image.alpha_composite(box.crop((0,0,box.width,self.content_height+30)), dest=(0, py))
        image.alpha_composite(open_image_cached('assets/builtin/darkbox_end.png'), dest=(0, self.pixel_align(self.content_height+py+10)))

        image.alpha_composite(self.contents,(x,py+20))
        return self.get_height(y)

    def get_height(self, y) -> int:
        return self.pixel_align(self.content_height+y) - y + 30

class Conditional(PixelAligned):
    def __init__(self, conditional: Image.Image | str, contents: Sequence[BodyItem] = []): # TODO: make these render actual text maybe?
        self.image = conditional
        with get_image(self.image) as img:
            self.image_height = img.height
        self.contents = list(contents)
        self.box = InfoBox(self.contents)

    def draw(self, image: Image.Image, x : int, y : int) -> int:
        with get_image(self.image) as img:
            image.alpha_composite(img, (0, self.pixel_align(y)))
        offset = self.image_height + 10
        if self.contents:
            offset += self.box.draw(image, x, self.pixel_align(y+offset))
        return offset

class Trait(BodyItem):
    def __init__(self, text: str) -> None: 
        self.text = wrap_text(text, w = 830, font=textFont)
        
    def draw(self, image: Image.Image, x: int, y: int) -> int:
        draw = ImageDraw.Draw(image)
        for i, line in enumerate(self.text):
            draw.text((x, y+35*i), line, fill=(0,0,0), font=textFont, anchor="la") # text
        return self.get_height(y)
    
    def get_height(self, y) -> int:
        return 40*len(self.text)
    
class FlavorText(BodyItem):
    def __init__(self, text) -> None:
        self.text = wrap_text(text, 830, italFont)

    def draw(self, image: Image.Image, x: int, y: int) -> int:
        draw = ImageDraw.Draw(image)
        draw.text((561,y), '\n'.join(self.text), fill=(0,0,0), font=italFont, anchor="ma", align='center')  #TODO magic number reduction 
        return self.get_height(y)# Technically not needed for aug cards but feels prudent
    
    def get_height(self, y) -> int:
        return 40*len(self.text)

def shadow_text(image : ImageDraw.ImageDraw, x : int, y : int, text : str, font : Font, anchor : str ="la") -> None: # TODO make this not so inflexible-
    image.text((x+5,y+5), text, fill=(0,0,0), font=font, anchor=anchor)
    image.text((x,y), text, fill=(255,255,255), font=font, anchor=anchor)

#MARK: Assemble Card
def assemble_card(background: str | Image.Image = open_image_cached('assets/builtin/background_error.png'), 
                  portrait: str | Image.Image = open_image_cached('assets/builtin/portrait_error.png'),
                  frame: str | Image.Image = open_image_cached('assets/builtin/frame_error.png'), 
                  power: Image.Image | str | int = '0', health: Image.Image | str | int = '0', tier: str = 'tierless', temple: str = 'templeless',
                  tribes: Sequence | None = None, name: str = 'Unnamed Card', artist: str = 'No Artist', costs: Sequence[tuple[Image.Image | str, int, bool]] = [],
                  format: str = 'no format string lol', decals : Sequence[tuple[Image.Image|str, tuple[int, int]]] = [], 
                  accentcolor : tuple[int,int,int,int] | None = None,
                  body: Sequence = []) -> Image.Image:
    """Create and return a card image given the pieces of a card.

    Given the information of a card, return the card that the represented as an image.
    Tribes should be provided as a sequence of strings, even if there is only 1 tribe.

    Parameters
    ----------
    background, frame, portrait : Image or string, optional
        Image assets for the card. Accept an image object or a path.
    power, health : string
        Values to print in the card's stat boxes
    tier, temple : string
        Values to print in the card's tribeline
    body: Sequence of BodyRenderer objects
        Sequence of things that go in the card's main body; in the specific context of aug this is sigils, traits, conditionals, and flavor text
    tribes : Sequence of strings
        Sequence of tribes the card has
    artist : str
        Creator of the portrait (we don't give credit to those people who made *assets*)
    costs : Sequence of tuples, of the form (icon, number, compact)
        A Sequence containing each cost of the card; requires the icon the cost uses and the number, and then optionally specify to render them compactly

    Returns
    -------
    Image
        The constructed card's image.
    """
    # TODO Make these data driven (probably a refactor more than a tweak)
    # Create card image
    image = Image.new("RGBA",(112,156))

    # Draw background
    with get_image(background, default = open_image_cached('assets/builtin/background_error.png')) as bgimage: 
        image.paste(bgimage,(13,27))

    # Draw portrait
    with get_image(portrait, default = open_image_cached('assets/builtin/portrait_error.png')) as artimage: 
        image.alpha_composite(artimage,(13,27))

    # Draw frame
    with get_image(frame, default = open_image_cached('assets/builtin/frame_error.png')) as frameimage: 
        image.alpha_composite(frameimage,(0,0))

    # if we weren't given one, pick the accent color with the old method
    if accentcolor is None:
        accentcolor = typing.cast(tuple[int, int, int, int], image.getpixel((66,18)))
        logger.warning('No accentcolor specified for card {}, picked color {}'.format(name, accentcolor))

    # Create a drawing interface
    draw = ImageDraw.Draw(image)

    # Draw costs
    costx = 99 # TODO demagic number this whole section
    costy = 14
    
    for cost in costs:
        path, count, compact = cost
        with get_image(path, default=open_image_cached('assets/builtin/costerror.png')) as icon:
            if compact:
                image.alpha_composite(icon, ((costx-(icon.width-1)),costy-(icon.height//2-4)))
                costx -= icon.width+5
                for c in reversed('{}x'.format(count)):
                    char = open_image_cached('assets/builtin/{}.png'.format(c))
                    image.alpha_composite(char, (costx,costy))
                    costx -= 6
            else:
                # verbose rendering
                for i in range(count):
                    image.alpha_composite(icon, ((costx-(icon.width-1)),costy-(icon.height//2-4)))
                    costx -= icon.width-1
        costx -= 2

    # Scale the image up then get a new draw wrapper
    # TODO configurable output resoltion (now that I think about it, should also add configurable input resolution)
    image = image.resize((1120,1560),resample=Image.Dither.NONE) #MARK: Card Upscale
    draw = ImageDraw.Draw(image)

    # Draw stats TODO: Variable power
    power = typing.cast(int, power)
    health = typing.cast(int, health)
    for v, x in [(power, 180), (health, 940)]: # TODO: pretend this is forwards compatibility and not laziness
        try:
            length = statFont.getlength(str(int(v)))
            shadow_text(draw,int(x - length/2),1331,str(int(v)),statFont)
        except ValueError: # it was actually a variable power and not an integer
            v = typing.cast(str | Image.Image, v)
            with get_image(v) as icon:
                image.alpha_composite(icon, (int(x-icon.width/2), 1351))
    #shadow_text(draw,968,1331,str(int(health)),statFont,anchor="ra")

    # Sigils TODO: magic number removal service
    sigilx = 150
    sigily = 920

    for o in body:
        sigily += o.draw(image, sigilx, sigily)

    # Tribeline (includes tier and temple)
    tribe_string = '{} {}'.format(tier, temple) if tribes == None else '{} {} - {}'.format(tier, temple, ' '.join(tribes))
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

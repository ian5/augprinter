from typing import Sequence
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from loguru import logger
import text
from loaders import open_image_cached
from loaders import get_image

DEFAULT_FONTS = {
    'Sigil': {
        'body': None,
        'title': None
    },
    'Trait': {
        'body': None,
    },
    'FlavorText': {
        'body': None
    }
}

class BodyItem: 
    def __init__(self) -> None:
        pass

    def font(self, overwrite: text.TextStyle|None, bodyitem: str, font: str) -> text.TextStyle:
        """Use a set default font for this body item, unless explicitly overruled"""
        default = DEFAULT_FONTS[bodyitem][font]
        if overwrite is not None:
            return overwrite
        elif default is not None:
            return default
        else:
            raise(ValueError('No provided or default font {}.{}'.format(bodyitem, font)))


    def draw(self, image, box) -> int:
        return 0
    
    def get_height(self, y) -> int:
        return 0

class Sigil(BodyItem): #MARK: Sigil
    """A sigil to draw on a card.
    
    Parameters
    ----------
    icon : image or path to image
        The icon of the sigil
    text : string
        The body text of the sigil
    render_color : tuple[float,float,float]
        The color to render the text and possibly icon with
    blacked : bool
        If true, render the sigil in forced monocolor.
        Used for infobox rendering
    outlineicon : image or path to image
        A special icon, used when the sigil needs to be rendered in a
        reminder box; ignores render_color if provided
    """

    def __init__(self, name: str, icon: str | Image.Image, text: str, titlefont: text.TextStyle|None = None, bodyfont: text.TextStyle|None = None,  blacked : bool = False, outlineicon: str | Image.Image | None = None) -> None:
        self.name = name
        self.icon = icon
        self.blacked = blacked
        self.titlefont = self.font(titlefont, 'Sigil', 'title')
        self.bodyfont = self.font(bodyfont, 'Sigil', 'body')
        self.titlewidth = self.titlefont.get_length(self.name + ': ')
        self.text = text 
        self.outlineicon = outlineicon
    
    def draw(self, image: Image.Image, box: tuple[int, int, int ,int], blacked: bool = False) -> int:
        draw = ImageDraw.Draw(image)
        x, y, w, h = box
        if self.blacked: # Are we being drawn in an infobox?
            if self.outlineicon is not None: # If we have a special case sigil, just use that
                with get_image(self.outlineicon, default = open_image_cached('assets/builtin/sigil_error.png')) as icon:
                    image.alpha_composite(icon, (x, y))
            else: # If we don't, make the sigil render as a single color (white, for aug purposes)
                with get_image(self.icon, default = open_image_cached('assets/builtin/sigil_error.png')) as icon:
                    blacked_icon = Image.new('RGBA', icon.size, (255,255,255))
                    blacked_icon.putalpha(icon.getchannel('A'))
                    image.alpha_composite(blacked_icon, (x, y))
        else: # If we're not, just render the icon normally
            with get_image(self.icon, default = open_image_cached('assets/builtin/sigil_error.png')) as icon:
                image.alpha_composite(icon, (x, y))
        text_color = (255,255,255) if self.blacked else (0,0,0) # lol 

        sigil_name = self.name + ': '
        titlewidth = self.titlefont.get_length(sigil_name)
        self.bodyfont.wrap(self.text, w = 750, first_line_offset=titlewidth)

        # Render the sigil text
        if len(self.text) == 1: # vertically center single line text
            self.titlefont.print_line(self.name+": ", draw, (x+80, y+15), fill=text_color, anchor="la")
            self.bodyfont.print_line(self.text[0], draw, (x+80+self.titlewidth, y+15), fill=text_color, anchor="la") # text
        else:
            self.titlefont.print_line(self.name+": ", draw, (x+80, y-5),  fill=text_color, anchor="la") # name
            for i, line in enumerate(self.text):
                self.bodyfont.print_line(line, draw, (x+80+self.titlewidth if i==0 else x+80, y-5+40*i),  fill=text_color, anchor="la") # text
        return self.get_height(y)

    def get_height(self, y : int) -> int:
        return 40*max(2, len(self.text)) # 40px per line of text, sigils are a minimum of 2 lines tall


class PixelAligned(BodyItem): #MARK: PixelAligned
    """Draws an image aligned to the lores pixel grid, snapping downwards.
    
    Parameters
    ----------
    image: Image or str
        The image to be drawn
    """

    def __init__(self, image : Image.Image | str) -> None: # TODO take another look at this whole thing, it's kinda a clusterfuck
       
        self.image = image
        with get_image(self.image) as img:
            self.image_height = img.height

    def pixel_align(self, y : int) -> int:
        return 10*(y//10) #TODO: this needs to support different resolutions

    def draw(self, image: Image.Image, box: tuple[int, int, int ,int]) -> int:
        x, y, w, h = box
        with get_image(self.image) as img:
            image.alpha_composite(img, (0, self.pixel_align(y)))
        return self.get_height(y)
    
    def get_height(self, y) -> int:
        return self.pixel_align(y) - y + self.image_height
    
class HorizontalRule(PixelAligned): #MARK: HorizontalRule
        """Convenience function; just a PixelAligned which is always the seperator bar."""
        def __init__(self):
            return super().__init__(open_image_cached('assets/builtin/separator_large.png'))

class InfoBox(PixelAligned): #MARK: InfoBox
    """Draws a stretchy box that holds other BodyItems. No clipping.
    
    Parameters
    ----------
    children : Sequence[BodyItem]
        The BodyItems to put within the container; height is automatically
        detected. 
    """

    def __init__(self, children : Sequence[BodyItem]):
        self.children = list(children)
        self.contents = Image.new('RGBA', (1120,1560)) # magic number; the second number here is arbirary, pretty much
        self.content_height = 0
        for o in self.children:
            self.content_height += o.draw(self.contents, (0, self.content_height, 750, 1560))

    def draw(self, image: Image.Image, box: tuple[int, int, int ,int]) -> int:
        x, y, w, h = box
        container = open_image_cached('assets/builtin/darkbox.png')
        py = self.pixel_align(y)
        image.alpha_composite(container.crop((0,0,container.width,self.content_height+30)), dest=(0, py))
        image.alpha_composite(open_image_cached('assets/builtin/darkbox_end.png'), dest=(0, self.pixel_align(self.content_height+py+10)))

        image.alpha_composite(self.contents,(x,py+20))
        return self.get_height(y)

    def get_height(self, y) -> int:
        return self.pixel_align(self.content_height+y) - y + 30

class Conditional(PixelAligned): #MARK: Conditional
    """Draws a conditional. Can have children in an Infobox
    
    Parameters
    ----------
    conditional : Image or str
        The conditional image
    contents : Sequence[BodyItem]
        The things to put in the conditionals infobox; renders if non empty.
    """

    def __init__(self, conditional: Image.Image | str, contents: Sequence[BodyItem] = []): # TODO: make these render actual text maybe?
        self.image = conditional
        with get_image(self.image) as img:
            self.image_height = img.height
        self.contents = list(contents)
        self.box = InfoBox(self.contents)

    def draw(self, image: Image.Image, box: tuple[int, int, int ,int]) -> int:
        x, y, w, h = box
        with get_image(self.image) as img:
            image.alpha_composite(img, (0, self.pixel_align(y)))
        offset = self.image_height + 10
        if self.contents:
            offset += self.box.draw(image, (x, self.pixel_align(y+offset), 750, 1156))
        return offset

class Trait(BodyItem): #MARK: Trait
    """Draws a piece of text.
    
    Parameters
    ----------
    text : str
        The text to be drawn
    """

    def __init__(self, text: str, bodyfont: text.TextStyle|None = None) -> None: 
        self.bodyfont = self.font(bodyfont, 'Trait', 'body')
        self.text = self.bodyfont.wrap(text, w = 830) #TODO More magic numbers
        
    def draw(self, image: Image.Image, box: tuple[int, int, int ,int]) -> int:
        x, y, w, h = box
        draw = ImageDraw.Draw(image)
        for i, line in enumerate(self.text):
            self.bodyfont.print_line(line, draw, (x, y+35*i), fill=(0,0,0), anchor="la") # text
        return self.get_height(y)
    
    def get_height(self, y) -> int:
        return 40*len(self.text)
    
class FlavorText(BodyItem): #MARK: FlavorText
    """Draws a piece of text, centered and italic.
    
    Parameters
    ----------
    text : str
        The text to be drawn
    """

    def __init__(self, text, bodyfont: text.TextStyle|None = None) -> None:
        self.bodyfont = self.font(bodyfont, 'FlavorText', 'body')
        self.text = self.bodyfont.wrap(text, 830)

    def draw(self, image: Image.Image, box: tuple[int, int, int ,int]) -> int:
        x, y, w, h = box
        draw = ImageDraw.Draw(image)
        self.bodyfont.print_line('\n'.join(self.text), draw, (560,y),  fill=(0,0,0), anchor="ma", align='center')  #TODO magic number reduction 
        return self.get_height(y)# Technically not needed for aug cards but feels prudent
    
    def get_height(self, y) -> int:
        return 40*len(self.text)
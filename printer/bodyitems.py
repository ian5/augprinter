from typing import Sequence
from PIL import Image
from PIL import ImageDraw
from loguru import logger
from printer import text
from printer.loaders import open_image_cached, get_image

class BodyItem:
    # Expose a method to set class default fonts, so that the config module
    # doesn't have to play with the attributes directly
    @classmethod
    def set_default_font(cls, name : str, font : text.TextStyle) -> None:
        cls.fonts[name] = font

    # Each subclass needs its own set of default fonts
    def __init_subclass__(cls):
        # So we make a new dictionary for each subclass
        cls.fonts = {}

    # You can also change a specific instance's font, if you'd like
    def set_font(self, font: text.TextStyle | None, name : str) -> None:
        # This is a convenience function for constructors, so only do anything
        # if actually called with an argument
        if font is not None:
            self.fonts[name] = font

    # Assume that there was no height if an item doesn't specifically say so
    def draw(self, image: Image.Image, box: tuple[int, int, int ,int]) -> int:
        # The get height method needs to know our position, so pass that along
        return self.get_height(box)

    # Bodyitems only have height if told to
    def get_height(self, box: tuple[int, int, int ,int]) -> int:
        return 0

class Sigil(BodyItem): #MARK: Sigil
    """A sigil to draw on a card.

    Parameters
    ----------
    icon : image or path to image
        The icon of the sigil
    text : string
        The body text of the sigil
    titlefont, bodyfont : TextStyle
        Use the specified font to render the text stated
    invertedicon : image or path to image
        A special icon, used when the sigil needs to be rendered in inverted
        colors; ignores render_color if provided
    """

    error = open_image_cached('assets/builtin/sigil_error.png')

    def __init__(self, name: str, icon: str | Image.Image, text: str,
                 titlefont: text.TextStyle|None = None,
                 bodyfont: text.TextStyle|None = None,
                 invertedicon: str | Image.Image | None = None,
                 **kwargs) -> None:
        self.name = name
        self.icon = icon
        # Apply python formatting to the string directly; this is kinda lazy
        # but it's close to a perfect solution
        self.text = text.format(**kwargs) 
        # Helper function that only sets the font if we were provided one
        self.set_font(titlefont, 'title')
        self.set_font(bodyfont, 'body')
        self.invertedicon = invertedicon

    def draw(self, image: Image.Image, box: tuple[int, int, int ,int],
             blacked: bool = False) -> int:
        # Unpack the bounding box to make it more convenient to use
        x, y, w, h = box
        # We need an ImageDraw object to render the sigil text
        draw = ImageDraw.Draw(image)
        if blacked: # Are we being drawn in an infobox?
            # If so, and there's a special icon for infoboxes, just use it
            if self.invertedicon is not None:
                # We cache the sigil error, since we'll only ever have the one
                with get_image(self.invertedicon, self.error) as icon:
                    # Then overlay the sigil icon in the right place
                    image.alpha_composite(icon, (x, y))
            # If we don't have one, make the sigil render in a single color
            else:
                with get_image(self.icon, self.error) as icon:
                    # Make a flat color image of the same size as the sigil
                    blacked_icon = Image.new('RGBA', icon.size, (255,255,255))
                    # Copy the sigil's alpha channel to it
                    blacked_icon.putalpha(icon.getchannel('A'))
                    # Then put it in the right place instead of the sigil icon
                    image.alpha_composite(blacked_icon, (x, y))
        else: # If we're not, just render the icon normally
            # Cache the error then draw the icon in the right place
            with get_image(self.icon, self.error) as icon:
                image.alpha_composite(icon, (x, y))
        # If we're in an infobox make the text show up on a black background
        text_color = (255,255,255) if blacked else (0,0,0) # lol

        lines = self.get_wrapped_lines()
        titlewidth = self.get_title_width()

        # If the sigil text is one line long, it needs centered vertically
        if len(lines) == 1:
            # TODO: kill magic number
            self.fonts['title'].print_line(self.name+": ", draw, (x+80, y+15),
                                           fill=text_color, anchor="la")# name
            self.fonts['body'].print_line(lines[0], draw,
                                          (x+80+titlewidth, y+15),
                                          fill=text_color, anchor="la") # text
        # Otherwise draw each line in a stack
        else:
            # Okay this is a *ton* of magic numbers; i'm not even going to
            # bother commenting this until I come back to strip those
            self.fonts['title'].print_line(self.name+": ", draw, (x+80, y-5),
                                           fill=text_color, anchor="la") # name
            for i, line in enumerate(lines):
                self.fonts['body'].print_line(line, draw,
                                              (x+80+titlewidth if i==0
                                               else x+80, y-5+40*i),
                                              fill=text_color, anchor="la") # text
        # Return how tall this thing is, so that other code can stack them
        return self.get_height(box)

    def get_height(self, box: tuple[int, int, int ,int]) -> int:
        # 40px per line of text, sigils are a minimum of 2 lines tall even
        # if they only have one line of text
        return 40*max(2, len(self.get_wrapped_lines()))
    
    def get_wrapped_lines(self) -> list[str]:
        # TODO: Magic number
        return self.fonts['body'].wrap(self.text, w = 750,
            first_line_offset=self.get_title_width())

    def get_title_width(self) -> int:
        """Returns the width, in pixels, of the title in the current font"""
        return self.fonts['title'].get_length(self.name + ': ')
class PixelAligned(BodyItem): #MARK: PixelAligned

    """Draws an image aligned to the lores pixel grid, snapping downwards.

    Parameters
    ----------
    image: Image or str
        The image to be drawn
    """
    # TODO: take another look at this whole thing, it's kinda a clusterfuck
    def __init__(self, image : Image.Image | str) -> None:
        self.image = image
        # The height function needs the height of the image set aside
        with get_image(self.image) as img:
            self.image_height = img.height

    @staticmethod
    def pixel_align(y : int) -> int:
        """Given a number, snap that position to the next multiple of 10"""
        return y - y%10 #TODO: magic number

    def draw(self, image: Image.Image, box: tuple[int, int, int ,int]) -> int:
        # Unpack the bounding box to make it more convenient to use
        x, y, w, h = box
        with get_image(self.image) as img:
            # Draw our image at the next lores pixel it can snap to
            image.alpha_composite(img, (0, self.pixel_align(y)))
        # Return how tall this thing is, so that other code can stack them
        return self.get_height(box)

    def get_height(self, box: tuple[int, int, int ,int]) -> int:
        x, y, w, h = box
        # Height of the image, plus extra room to round to a pixel
        return self.pixel_align(y) - y + self.image_height

class HorizontalRule(PixelAligned): #MARK: HorizontalRule
        """A PixelAligned which is always the seperator bar."""
        def __init__(self):
            return super().__init__(open_image_cached(
                'assets/builtin/separator_large.png'))

class InfoBox(PixelAligned): #MARK: InfoBox
    """Draws a stretchy box that holds other BodyItems. No clipping.

    Parameters
    ----------
    children : Sequence[BodyItem]
        The BodyItems to put within the container; height is automatically
        detected.
    """
#TODO: make this play nice with more bodyitems it fucks up flavortext apparently
    def __init__(self, children : Sequence[BodyItem]):
        self.children = list(children)
        # TODO: kill an magic number

        # We're drawing this boxes contents now, rather than at render time
        self.contents = Image.new('RGBA', (1120,1560))
        self.content_height = 0

        # We need to know how tall the actual image content is
        for o in self.children:
            self.content_height += o.draw(self.contents,
                                          (0, self.content_height, 750, 1560))

    def draw(self, image: Image.Image, box: tuple[int, int, int ,int]) -> int:
        # Unpack the bounding box to make it more convenient to use
        x, y, w, h = box
        # Since every infobox uses the darkbox, we cache it
        container = open_image_cached('assets/builtin/darkbox.png')
        # Find a pixel aligned position, so we can render to the lores grid
        py = self.pixel_align(y)
        # Crop the container background down to fit our content
        container_section = container.crop((0,0,container.width,
                                            self.content_height+30))
        # And paste it
        image.alpha_composite(container_section, (0, py))
        # Then paste the bottom edge of the container at the bottom
        image.alpha_composite(open_image_cached(
            'assets/builtin/darkbox_end.png'),
            (0, self.pixel_align(self.content_height+py+10)))
        # And paste the contents we rendered earlier on top
        image.alpha_composite(self.contents,(x,py+20))
        # Return how tall this thing is, so that other code can stack them
        return self.get_height(box)

    def get_height(self, box: tuple[int, int, int ,int]) -> int:
        x, y, w, h = box
        # Height of the content aligned to the pixel grid, with some extra room
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

    def __init__(self, conditional: Image.Image | str, 
                 contents: Sequence[BodyItem] = []): 
        # TODO: make these render actual text maybe?
        self.image = conditional
        # We need to know the image height to find the total height of the item
        with get_image(self.image) as img:
            self.image_height = img.height
        self.contents = list(contents)
        self.box = InfoBox(self.contents)

    def draw(self, image: Image.Image, box: tuple[int, int, int ,int]) -> int:
        # Unpack the bounding box to make it more convenient to use
        x, y, w, h = box
        # Paste the image, aligned to the next lores pixel
        with get_image(self.image) as img:
            image.alpha_composite(img, (0, self.pixel_align(y)))
        # We'll draw the contents infobox one pixel down
        offset = self.image_height + 10
        # If this conditional has contents...
        if self.contents:
            # ...then render the contents box, and keep track of how far down
            # we've rendered things 
            offset += self.box.draw(image, (x, self.pixel_align(y+offset),
                                            750, 1156))
        # Return the total height of the conditional and any contents
        return offset# TODO: move to a get_height method

class Trait(BodyItem): #MARK: Trait
    """Draws a piece of text.

    Parameters
    ----------
    text : str
        The text to be drawn
    """

    def __init__(self, text: str, bodyfont: text.TextStyle|None = None) -> None:
        # Helper function that only sets the font if we were provided one
        self.set_font(bodyfont, 'body')
        # Wrap the text in advance
        self.text = self.fonts['body'].wrap(text, w = 830) #TODO More magic numbers

    def draw(self, image: Image.Image, box: tuple[int, int, int ,int]) -> int:
        # Unpack the bounding box to make it more convenient to use
        x, y, w, h = box
        # We need an ImageDraw to render the text
        draw = ImageDraw.Draw(image)
        # Draw each line in order
        for i, line in enumerate(self.text):
            self.fonts['body'].print_line(line, draw, (x, y+35*i), 
                                          fill=(0,0,0), anchor="la")
        # Return the height so that other code can stack these
        return self.get_height(box)

    def get_height(self, box: tuple[int, int, int ,int]) -> int:
        # Each line of text is 40px tall
        return 40*len(self.text)

class FlavorText(BodyItem): #MARK: FlavorText
    """Draws a piece of text, centered and italic.

    Parameters
    ----------
    text : str
        The text to be drawn
    """

    def __init__(self, text, bodyfont: text.TextStyle|None = None) -> None:
        # Helper function that only sets the font if we were provided one
        self.set_font(bodyfont, 'body')
        # Wrap the text in advance
        self.text = self.fonts['body'].wrap(text, 830)

    def draw(self, image: Image.Image, box: tuple[int, int, int ,int]) -> int:
        # Unpack the bounding box to make it more convenient to use
        x, y, w, h = box
        # We need an ImageDraw to render the text
        draw = ImageDraw.Draw(image)
        # Draw each line in order, centered.
        self.fonts['body'].print_line('\n'.join(self.text), draw, (560,y),
                                      fill=(0,0,0), anchor="ma",align='center')
        #TODO magic number reduction
        # Return the height so that other code can stack these
        return self.get_height(box)# Technically not needed for aug cards but feels prudent

    def get_height(self, box: tuple[int, int, int ,int]) -> int:
        # Each line of text is 40px tall
        return 40*len(self.text)

# A dictionary with every available body item has turned out to be worth having
# in a few places, so we do that here instead of in several different places.
body_items = {i.__name__: i for i in BodyItem.__subclasses__()}
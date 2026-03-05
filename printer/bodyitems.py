from typing import Sequence, Type
from PIL import Image
from PIL import ImageDraw
from loguru import logger
from printer import text
from printer.loaders import open_image_cached, get_image

BoundingBox = tuple[int, int, int, int]

class BodyItem: # MARK: BodyItem
    # Expose a method to set class default fonts, so that the config module
    # doesn't have to play with the attributes directly
    @classmethod
    def set_default_font(cls, name : str, font : text.TextStyle) -> None:
        cls.fonts[name] = font

    # Each subclass needs its own set of default fonts
    def __init_subclass__(cls):
        # So we make a new dictionary for each subclass
        cls.fonts : dict[str, text.TextStyle] = {}

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

    def __init__(self, name: str, icon: str | Image.Image, body: str,
                 titlefont: text.TextStyle|None = None,
                 bodyfont: text.TextStyle|None = None,
                 invertedicon: str | Image.Image | None = None,
                 **kwargs) -> None:
        self.name = name
        self.icon = icon
        self.body = body
        # Helper function that only sets the font if we were provided one
        self.set_font(titlefont, 'title')
        self.set_font(bodyfont, 'body')
        self.invertedicon = invertedicon
        self.args = kwargs # Used for token requiring bodies.

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

        lines = self.get_wrapped_lines(box)
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
        return 40*max(2, len(self.get_wrapped_lines(box)))
    
    def get_wrapped_lines(self, box: BoundingBox) -> list[str]:
        text = self.get_body_text()
        return self.fonts['body'].wrap(text, w=self.get_body_width(box),
            first_line_offset=self.get_title_width())

    @classmethod
    def get_body_width(cls, box: BoundingBox) -> int:
        """Returns the width for body text given the bounding box"""
        x, y, w, h = box
        return w-70 # pretend this is more complicated and taking into account
        # extra customization options

    def get_body_text(self) -> str:
        """Get the raw body text"""
        return self.body.format(**self.args)
    
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
        for child in self.children:
            # Prepare the arguments in a dictionary so that we can modify them
            # for special case rendering
            arguments = {"image": self.contents,
                         "box": (0, self.content_height, 750, 1560)}
            # If the contents are a sigil then they should be rendered inverted
            if isinstance(child, Sigil):
                arguments["blacked"] = True
            self.content_height += child.draw(**arguments)

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
    #TODO: Move child rendering to runtime
    """Draws a conditional. Can have children in an Infobox

    Parameters
    ----------
    image : Image or str
        The conditional image
    contents : Sequence[BodyItem]
        The things to put in the conditionals infobox; renders if non empty.
    """

    def __init__(self, image: Image.Image | str, 
                 contents: Sequence[BodyItem] = [], **kwargs): 
        # TODO: make these render actual text maybe?
        self.image = image
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

class Text(BodyItem): #MARK: Text
    """Draws a piece of text.
    
    Parameters
    ----------
    body : str
        The text to be drawn.
    bodyfont : text.TextStyle = None
        The TextStyle to draw the text with
    **kwargs
        Additional arguments are passed to the PIL print calls"""
    def __init__(self, body: str, bodyfont: text.TextStyle|None = None, 
                 **kwargs):
        # Helper function that only sets the font if we were provided one
        self.set_font(bodyfont, 'body')
        self.text = body
        self.args = kwargs
    
    def get_wrapped_lines(self, box : BoundingBox):
        """Return the lines of the body text, wrapped within a bounding box"""
        return self.fonts['body'].wrap(self.text, box[2])
    
    def get_height(self, box : BoundingBox):
        return len(self.get_wrapped_lines(box))*35+5

    def get_line_position(self, line : int, 
                          box : BoundingBox) -> tuple[int, int]:
        x, y, w, h = box
        return (x, y + 35*line)

    def draw(self, image: Image.Image, box : BoundingBox):
        # Unpack the bounding box 
        x, y, w, h = box
        # Make a drawing object for the image we got
        draw = ImageDraw.Draw(image)
        # For each wrapped line
        for i, line in enumerate(self.get_wrapped_lines(box)):
            # Print the line in its position, plus any extra arguments
            self.fonts['body'].print_line(line, draw, 
                self.get_line_position(i, box), (0,0,0), **self.args)
        return self.get_height(box)

class Trait(Text): #MARK: Trait
    def __init__(self, body: str, bodyfont: text.TextStyle|None = None,
                **kwargs):
        super().__init__(body, bodyfont, **{'anchor': 'la'} | kwargs)

class FlavorText(Text): #MARK: FLavorText
    def __init__(self, body: str, bodyfont: text.TextStyle|None = None,
                **kwargs):
        self.set_font(bodyfont, 'body')
        self.text = body
        self.args = {'anchor': 'ma', 'align': 'center'} | kwargs
    
    def get_line_position(self, line: int, 
                          box: tuple[int, int, int, int]) -> tuple[int, int]:
        x, y, w, h = box
        # The print position is horizontally centered
        return (x + w//2, y + 35*line)

def all_subclasses(cls):
    return {cls}.union(s for c in cls.__subclasses__() 
                       for s in all_subclasses(c))

body_items = {i.__name__: i for i in all_subclasses(BodyItem)}
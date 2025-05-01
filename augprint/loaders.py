import functools
import typing
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from loguru import logger

@functools.lru_cache
def open_image_cached(path: str):
    """Open an image and keep it loaded."""
    img = Image.open(path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    return img

@functools.lru_cache(maxsize=16)
def open_font_cached(path: str, size: int):
    """Open a font and keep it loaded."""
    return ImageFont.truetype(path, size)

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
        except FileNotFoundError: # Test if they skipped a file extension #TODO: Gut this; it's pointless with the planned implications
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
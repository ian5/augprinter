import functools
import typing
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from loguru import logger

@functools.lru_cache
def open_image_cached(path: str):
    """Open an image and keep it loaded."""
    return Image.open(path)

@functools.lru_cache(maxsize=16)
def open_font_cached(path: str, size: int):
    """Open a font and keep it loaded."""
    return ImageFont.truetype(path, size)

class get_image:
    def __init__(self, image : Image.Image | str, default : Image.Image | str | None = None):
        """Handle image loading safely, but let preloaded images through

        Parameters
        ----------
        image : Image | str
            Either an image or path to image; if it's a path, the image will be
            loaded and unloaded by the context manager
        default : Image | str
            The image or path to use if image is not found
        Raises
        ------
        FileNotFoundError
            No default was provided, and the file requested does not exist.
        """
        self.image = image
        self.default = default

    def __enter__(self) -> Image.Image:
        """Locate or pass through an image as a context manager."""
        try: # What if they just pass a path outright
            # Assume that image is a string
            self.image = typing.cast(str, self.image)
            self.managed = Image.open(self.image)
            self.close = True
            logger.debug('get_image loaded {}'.format(self.image))
        except AttributeError: # This is actually already an image not a path
            # sike dumb linter it was actually an image
            self.image = typing.cast(Image.Image, self.image)
            # The image we're keeping track of is already loaded
            self.managed = self.image
            # So it's also not our job to close it
            self.close = False
            logger.debug('get_image passed image through')
        except FileNotFoundError: # We failed to find the image
            # If there's no default, we have no image to return
            if self.default is None:
                # Raise an exception; it's the user's problem now
                raise(FileNotFoundError('get_image did not find image {}'.format(self.image)))
            # If there is, we need to use it
            else:
                try:
                    # Assume the default is a path
                    self.default = typing.cast(str, self.default)
                    # Open the default image and hold onto it
                    self.managed = Image.open(self.default)
                    # Since we opened it, it's our job to close it
                    self.close = True
                    logger.warning('get_image did not find image {}, loading default at {}'.format(self.image, self.default))
                # The default wasn't a path
                except AttributeError:
                    # So we assume it's an image
                    self.default = typing.cast(Image.Image, self.default)
                    # Hold onto the image
                    self.managed = self.default
                    # And don't close it when we're done
                    self.close = False
                    logger.warning('get_image did not find image {}, using default'.format(self.image, self.default))
                except FileNotFoundError:
                    # Well shit
                    raise(FileNotFoundError('get_image did not find image {} or default {}'.format(self.image, self.default)))
        # If the image isn't in RGBA mode
        if self.managed.mode != 'RGBA':
            # Hold onto the original so that we can close it correctly
            self.old = self.managed
            # Make a copy that is in RGBA mode
            self.managed = self.old.convert('RGBA')
            # Unless we're supposed to leave the original image alone,
            # close it now
            if self.close:
                self.old.close()
        return self.managed

    def __exit__(self, exc_type, exc_value, traceback):
        """Close the image resource, if you were the one who opened it."""
        # If it's our job to close the image we're managing...
        if self.close:
            # Do that
            self.managed.close()
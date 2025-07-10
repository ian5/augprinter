import pytest
from PIL import Image

# stolen from https://github.com/python-pillow/Pillow/blob/main/Tests/helper.py
# but with some github actions support i neither understand nor need removed
def assert_image_equal(a: Image.Image, b: Image.Image, msg: str | None = None) -> None:
    assert a.mode == b.mode, msg or f"got mode {repr(a.mode)}, expected {repr(b.mode)}"
    assert a.size == b.size, msg or f"got size {repr(a.size)}, expected {repr(b.size)}"
    if a.tobytes() != b.tobytes():
        pytest.fail(msg or "got different content")

# ditto but this time i removed some kind of smart path handling
# god these tests are scuffed.
def assert_image_equal_tofile(
    a: Image.Image,
    filename: str ,
    msg: str | None = None,
    mode: str | None = None,
) -> None:
    with Image.open(filename) as img:
        if mode:
            img = img.convert(mode)
        assert_image_equal(a, img, msg)

from io import BytesIO
from tempfile import NamedTemporaryFile

from PIL import Image


class ImageConverter:
    """convert images to TamTam format"""

    @classmethod
    def convert_to_tt_format(self, img_bytes: bytes) -> bytes:
        """
        convert image to png and resize to 512x512
        with save proportions
        """

        img = Image.open(BytesIO(img_bytes))

        # fill to 512x512
        x, y = img.size
        size = max(x, y)
        new_im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        new_im.paste(img, (int((size - x) / 2), int((size - y) / 2)))

        # convert to png
        tmp_f = NamedTemporaryFile()
        new_im.convert("RGB")
        new_im.thumbnail((512, 512), Image.ANTIALIAS)
        new_im.save(tmp_f.name, "png")
        with open(tmp_f.name, "rb") as fb:
            return fb.read()

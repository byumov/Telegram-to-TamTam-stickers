from io import BytesIO
from tempfile import NamedTemporaryFile

from PIL import Image

TAMTAM_STICKER_SIZE = (512, 512)

class ImageConverter:
    """convert images to TamTam format"""

    @classmethod
    def convert_to_tt_format(cls, img_bytes: bytes) -> bytes:
        """
        convert image to png and resize to 512x512
        with save proportions
        """

        img = Image.open(BytesIO(img_bytes))

        # fill to TAMTAM_STICKER_SIZE
        x, y = img.size
        size = max(x, y)
        new_im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        new_im.paste(img, (int((size - x) / 2), int((size - y) / 2)))

        # convert to png
        with NamedTemporaryFile() as tmp_f:
            new_im.convert("RGB")
            new_im.thumbnail(TAMTAM_STICKER_SIZE, Image.ANTIALIAS)
            new_im.save(tmp_f.name, "png")
            with open(tmp_f.name, "rb") as fb:
                return fb.read()

import atexit
import logging
import pathlib

from PIL import Image, ImageDraw

import epd2in13_V4

logging.basicConfig(level=logging.INFO)


class SealScreen:
    def __init__(self):
        self.epd = epd2in13_V4.EPD()
        self.epd.init()
        self.epd.clear()
        self._render_template()

    def _render_template(self):
        self.base_image = Image.new("1", (self.epd.height, self.epd.width), 255)

        self.draw = ImageDraw.Draw(self.base_image)
        self.draw.text((110, 60), "SEAL", fill=0)

        fdir = pathlib.Path(__file__).parent
        logo = Image.open(fdir / "soroban.png")
        logo.thumbnail((100, 100))
        self.base_image.paste(logo, (5, 10))

        self.epd.display_part_base_image(self.epd.get_buffer(self.base_image))
        self.epd.sleep()  # deep?

    def update_screen(self, seal_onchain, seal_offchain, ice_extent, delta):
        self.epd.init()

        # blank fill update area
        self.draw.rectangle(((150, 0), (250, 122)), fill=255)

        self.draw.text((150, 30), f"Ice Extent: {ice_extent}", fill=0)
        self.draw.text((150, 45), f"Delta: {delta} km^2", fill=0)

        self.draw.text((150, 70), "Supply", fill=0)
        self.draw.text((150, 85), f"- On-chain:  {seal_onchain}", fill=0)
        self.draw.text((150, 100), f"- Off-chain:   {seal_offchain}", fill=0)

        # screen refresh
        self.epd.display_partial(self.epd.get_buffer(self.base_image))
        self.epd.sleep()

    @staticmethod
    @atexit.register
    def shutdown():
        _epd = epd2in13_V4.EPD()
        _epd.init()
        _epd.clear()
        _epd.sleep()

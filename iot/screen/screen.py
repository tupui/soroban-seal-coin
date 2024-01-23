import logging

from PIL import Image, ImageDraw

import epd2in13_V4

logging.basicConfig(level=logging.INFO)

epd = epd2in13_V4.EPD()

try:
    epd.init()
    epd.clear()

    image = Image.new("1", (epd.height, epd.width), 255)

    draw = ImageDraw.Draw(image)
    draw.text((100, 60), "SEAL", fill=0)

    logo = Image.open("soroban.png")
    logo.thumbnail((100, 100))
    image.paste(logo, (5, 10))

    epd.display_part_base_image(epd.get_buffer(image))

    epd.sleep()
    epd.init()
    draw.rectangle((120, 80, 220, 105), fill=255)
    draw.text((120, 80), f"An update", fill=0)
    epd.display_partial(epd.get_buffer(image))
    epd.sleep()

except KeyboardInterrupt:
    epd.init()
    epd.clear()
    epd.sleep(cleanup=True)
    epd2in13_V4.epdconfig.module_exit(cleanup=True)

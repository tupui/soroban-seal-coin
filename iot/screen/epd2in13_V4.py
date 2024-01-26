"""E-paper controller for Waveshare's epd2in13_V4.

Based on epd2in13_V4.py from Waveshare team.

Original copyright notice:

*****************************************************************************
* | File        :	  epd2in13_V4.py
* | Author      :   Waveshare team
* | Function    :   Electronic paper driver
* | Info        :
*----------------
* | This version:   V1.0
* | Date        :   2023-06-25
# | Info        :   python demo
-----------------------------------------------------------------------------
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documnetation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to  whom the Software is
furished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
import sys

if sys.platform == "darwin":
    raise SystemExit("SPI not supported on macOS")

import logging
import time

import gpiozero
import spidev


logger = logging.getLogger(__name__)


class RaspberryPi:
    # Pin definition
    RST_PIN = 17
    DC_PIN = 25
    CS_PIN = 8
    BUSY_PIN = 18
    PWR_PIN = 22

    def __init__(self):
        self.SPI = spidev.SpiDev()
        self.GPIO_RST_PIN = gpiozero.LED(self.RST_PIN)
        self.GPIO_DC_PIN = gpiozero.LED(self.DC_PIN)
        # self.GPIO_CS_PIN     = gpiozero.LED(self.CS_PIN)
        self.GPIO_PWR_PIN = gpiozero.LED(self.PWR_PIN)
        self.GPIO_BUSY_PIN = gpiozero.Button(self.BUSY_PIN, pull_up=False)

    def digital_write(self, pin, value):
        if pin == self.RST_PIN:
            if value:
                self.GPIO_RST_PIN.on()
            else:
                self.GPIO_RST_PIN.off()
        elif pin == self.DC_PIN:
            if value:
                self.GPIO_DC_PIN.on()
            else:
                self.GPIO_DC_PIN.off()
        # elif pin == self.CS_PIN:
        #     if value:
        #         self.GPIO_CS_PIN.on()
        #     else:
        #         self.GPIO_CS_PIN.off()
        elif pin == self.PWR_PIN:
            if value:
                self.GPIO_PWR_PIN.on()
            else:
                self.GPIO_PWR_PIN.off()

    def digital_read(self, pin):
        if pin == self.BUSY_PIN:
            return self.GPIO_BUSY_PIN.value
        elif pin == self.RST_PIN:
            return self.GPIO_RST_PIN.value
        elif pin == self.DC_PIN:
            return self.GPIO_DC_PIN.value
        # elif pin == self.CS_PIN:
        #     return self.CS_PIN.value
        elif pin == self.PWR_PIN:
            return self.GPIO_PWR_PIN.value

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.SPI.writebytes(data)

    def spi_writebyte2(self, data):
        self.SPI.writebytes2(data)

    def module_init(self):
        self.GPIO_PWR_PIN.on()

        # SPI device, bus = 0, device = 0
        self.SPI.open(0, 0)
        self.SPI.max_speed_hz = 4000000
        self.SPI.mode = 0b00
        return 0

    def module_exit(self, cleanup=False):
        logger.debug("spi end")
        self.SPI.close()

        self.GPIO_RST_PIN.off()
        self.GPIO_DC_PIN.off()
        self.GPIO_PWR_PIN.off()
        logger.debug("close 5V, Module enters 0 power consumption ...")

        if cleanup:
            self.GPIO_RST_PIN.close()
            self.GPIO_DC_PIN.close()
            # self.GPIO_CS_PIN.close()
            self.GPIO_PWR_PIN.close()
            self.GPIO_BUSY_PIN.close()


class EPD:
    def __init__(self):
        self.epdconfig = RaspberryPi()

        self.reset_pin = self.epdconfig.RST_PIN
        self.dc_pin = self.epdconfig.DC_PIN
        self.busy_pin = self.epdconfig.BUSY_PIN
        self.cs_pin = self.epdconfig.CS_PIN
        self.width = 122
        self.height = 250

        # some magic as not working
        # self.init()
        # self.clear()

    def init(self):
        """Initialize the e-Paper register."""
        # EPD hardware init start
        self._reset()

        self._read_busy()
        self._send_command(0x12)  # SWRESET
        self._read_busy()

        self._send_command(0x01)  # Driver output control
        self._send_data(0xF9)
        self._send_data(0x00)
        self._send_data(0x00)

        self._send_command(0x11)  # data entry mode
        self._send_data(0x03)

        self._set_window(0, 0, self.width-1, self.height-1)
        self._set_cursor(0, 0)

        self._send_command(0x3C)
        self._send_data(0x05)

        self._send_command(0x21)  # Display update control
        self._send_data(0x00)
        self._send_data(0x80)

        self._send_command(0x18)
        self._send_data(0x80)

        self._read_busy()

    def init_fast(self):
        """Initialize the e-Paper fast register."""
        # EPD hardware init start
        self._reset()

        self._send_command(0x12)  # SWRESET
        self._read_busy()

        self._send_command(0x18)  # Read built-in temperature sensor
        self._send_command(0x80)

        self._send_command(0x11)  # data entry mode
        self._send_data(0x03)

        self._set_window(0, 0, self.width-1, self.height-1)
        self._set_cursor(0, 0)

        self._send_command(0x22)  # Load temperature value
        self._send_data(0xB1)
        self._send_command(0x20)
        self._read_busy()

        self._send_command(0x1A)  # Write to temperature register
        self._send_data(0x64)
        self._send_data(0x00)

        self._send_command(0x22)  # Load temperature value
        self._send_data(0x91)
        self._send_command(0x20)
        self._read_busy()

        return 0

    def get_buffer(self, image):
        """Display images."""
        img = image
        imwidth, imheight = img.size
        if imwidth == self.width and imheight == self.height:
            img = img.convert("1")
        elif imwidth == self.height and imheight == self.width:
            # image has correct dimensions, but needs to be rotated
            img = img.rotate(90, expand=True).convert("1")
        else:
            logger.warning(
                "Wrong image dimensions: must be "
                + str(self.width)
                + "x"
                + str(self.height)
            )
            # return a blank buffer
            return [0x00] * (int(self.width / 8) * self.height)

        buf = bytearray(img.tobytes("raw"))
        return buf

    def display(self, image):
        """Sends the image buffer in RAM to e-Paper and displays."""
        self._send_command(0x24)
        self._send_data2(image)
        self._turn_on_display()

    def display_partial(self, image):
        """Sends the image buffer in RAM to e-Paper and partial refresh."""
        self.epdconfig.digital_write(self.reset_pin, 0)
        self.epdconfig.delay_ms(1)
        self.epdconfig.digital_write(self.reset_pin, 1)

        self._send_command(0x3C)  # BorderWavefrom
        self._send_data(0x80)

        self._send_command(0x01)  # Driver output control
        self._send_data(0xF9)
        self._send_data(0x00)
        self._send_data(0x00)

        self._send_command(0x11)  # data entry mode
        self._send_data(0x03)

        self._set_window(0, 0, self.width-1, self.height-1)
        self._set_cursor(0, 0)

        self._send_command(0x24)  # WRITE_RAM
        self._send_data2(image)
        self._turn_on_display_part()

    def display_part_base_image(self, image):
        """Refresh a base image."""
        self._send_command(0x24)
        self._send_data2(image)

        self._send_command(0x26)
        self._send_data2(image)
        self._turn_on_display()

    def clear(self, color=0xFF):
        """Clear screen."""
        if self.width % 8 == 0:
            linewidth = int(self.width / 8)
        else:
            linewidth = int(self.width / 8) + 1
        # logger.debug(linewidth)

        self._send_command(0x24)
        self._send_data2([color] * int(self.height * linewidth))
        self._turn_on_display()

    def sleep(self, deep=False):
        """Enter sleep mode."""
        self._send_command(0x10)  # enter deep sleep
        self._send_data(0x01)

        self.epdconfig.delay_ms(2000)
        self.epdconfig.module_exit(cleanup=deep)

    # Private API

    def _reset(self):
        """Hardware reset."""
        self.epdconfig.digital_write(self.reset_pin, 1)
        self.epdconfig.delay_ms(20)
        self.epdconfig.digital_write(self.reset_pin, 0)
        self.epdconfig.delay_ms(2)
        self.epdconfig.digital_write(self.reset_pin, 1)
        self.epdconfig.delay_ms(20)

    def _send_command(self, command):
        self.epdconfig.digital_write(self.dc_pin, 0)
        self.epdconfig.digital_write(self.cs_pin, 0)
        self.epdconfig.spi_writebyte([command])
        self.epdconfig.digital_write(self.cs_pin, 1)

    def _send_data(self, data):
        self.epdconfig.digital_write(self.dc_pin, 1)
        self.epdconfig.digital_write(self.cs_pin, 0)
        self.epdconfig.spi_writebyte([data])
        self.epdconfig.digital_write(self.cs_pin, 1)

    def _send_data2(self, data):
        """Send more data"""
        self.epdconfig.digital_write(self.dc_pin, 1)
        self.epdconfig.digital_write(self.cs_pin, 0)
        self.epdconfig.spi_writebyte2(data)
        self.epdconfig.digital_write(self.cs_pin, 1)

    def _read_busy(self):
        """Wait until the busy_pin goes LOW."""
        logger.debug("e-Paper busy")
        while self.epdconfig.digital_read(self.busy_pin) == 1:  # 0: idle, 1: busy
            self.epdconfig.delay_ms(10)
        logger.debug("e-Paper busy release")

    def _turn_on_display(self):
        self._send_command(0x22)  # Display Update Control
        self._send_data(0xF7)
        self._send_command(0x20)  # Activate Display Update Sequence
        self._read_busy()

    def _turn_on_display_fast(self):
        self._send_command(0x22)  # Display Update Control
        self._send_data(0xC7)  # fast:0x0c, quality:0x0f, 0xcf
        self._send_command(0x20)  # Activate Display Update Sequence
        self._read_busy()

    def _turn_on_display_part(self):
        self._send_command(0x22)  # Display Update Control
        self._send_data(0xFF)  # fast:0x0c, quality:0x0f, 0xcf
        self._send_command(0x20)  # Activate Display Update Sequence
        self._read_busy()

    def _set_window(self, x_start, y_start, x_end, y_end):
        """Setting the display window.
        parameter:
            xstart : X-axis starting position
            ystart : Y-axis starting position
            xend : End position of X-axis
            yend : End position of Y-axis
        """
        self._send_command(0x44)  # SET_RAM_X_ADDRESS_START_END_POSITION
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self._send_data((x_start >> 3) & 0xFF)
        self._send_data((x_end >> 3) & 0xFF)

        self._send_command(0x45)  # SET_RAM_Y_ADDRESS_START_END_POSITION
        self._send_data(y_start & 0xFF)
        self._send_data((y_start >> 8) & 0xFF)
        self._send_data(y_end & 0xFF)
        self._send_data((y_end >> 8) & 0xFF)

    def _set_cursor(self, x, y):
        """Set Cursor.
        parameter:
            x : X-axis starting position
            y : Y-axis starting position
        """
        self._send_command(0x4E)  # SET_RAM_X_ADDRESS_COUNTER
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self._send_data(x & 0xFF)

        self._send_command(0x4F)  # SET_RAM_Y_ADDRESS_COUNTER
        self._send_data(y & 0xFF)
        self._send_data((y >> 8) & 0xFF)

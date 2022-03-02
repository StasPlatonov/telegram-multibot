from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import math
import logging

logger = logging.getLogger(__name__)


class AsciiProcessor(object):
    def __init__(self):
        self.tmp = 0

    def get_some_char(self, h):
        chars = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "[::-1]
        char_arr = list(chars)
        l = len(char_arr)
        mul = l/256
        return char_arr[math.floor(h*mul)]

    def convert_to_ascii(self, in_file_name, out_file_name, text):
        try:
            logger.info('Converting file ' + in_file_name)
            image = Image.open(in_file_name)
            scaleFac = 0.1
            charWidth = 8
            charHeight = 16
            w, h = image.size
            image = image.resize((int(scaleFac*w), int(scaleFac*h*(charWidth/charHeight))),Image.NEAREST)
            w, h = image.size
            pixels = image.load()

            font = ImageFont.truetype('lucon.ttf', 15)
            output_image = Image.new('RGB', (charWidth*w, charHeight*h), color=(0, 0, 0))
            draw = ImageDraw.Draw(output_image)
            img_wid = charWidth*w
            img_hei = charHeight*h

            for i in range(h):
                for j in range(w):
                    r, g, b = pixels[j, i]
                    grey = int((r/3+g/3+b/3))
                    pixels[j, i] = (grey, grey, grey)
                    draw.text((j*charWidth, i*charHeight), self.get_some_char(grey), font=font, fill=(r, g, b))

            # Add text
            if text is not None:
                text_font = ImageFont.truetype("comic.ttf", 70)
                text_width, text_height = draw.textsize(text, font=text_font)
                draw.text((img_wid / 2 - text_width / 2, text_height), text, (200, 200, 200), font=text_font)

            # Adjust brightness
            enhancer = ImageEnhance.Brightness(output_image)

            factor = 1.5
            output_image_enhanced = enhancer.enhance(factor)

            output_image_enhanced.save(out_file_name)


            #output_image.save(out_file_name)
        except OSError as e:
            logger.error(f'Failed to add text: {e}')
        except Exception as e:
            logger.error('Failed to convert photo: ' + str(e))

import sqlite3
from PIL import Image, ImageMode


start_time = 1

bitmap_width, bitmap_height = 1000, 1000;
Matrix = [[(255,255,255) for x in range(bitmap_width)] for y in range(bitmap_height)]

gif_frames = []

DELTA_FRAME_TIME = 60 * 20 #five minutes.

FRAME_DURATION = 1/10

colors = [
    0xffffff,
    0xe4e4e4,
    0x888888,
    0x222222,
    0xffa7d1,
    0xe50000,
    0xe59500,
    0xa06a42,
    0xe5d900,
    0x94e044,
    0x02be01,
    0x00d3dd,
    0x0083c7,
    0x0000ea,
    0xcf6ee4,
    0x820080
]

colors_tuple = [
    (255,255,255),
    (228,228,228),
    (136,136,136),
    (34, 34, 34),
    (255,167,209),
    (229, 0, 0),
    (229, 149, 0),
    (160, 106, 66),
    (229, 217, 0),
    (148, 224, 68),
    (2, 190, 1),
    (0, 211, 221),
    (0, 131, 199),
    (0, 0, 234),
    (207, 110, 228),
    (130, 0, 128)
]

def bitmap_to_matrix(bitmap):
    header_size = 3

    for i, byte in enumerate(bitmap[(header_size + 1):]):
        x1 = (i * 2) % bitmap_width
        y1 = min((i * 2) // bitmap_width, bitmap_height - 1)
        x2 = (x1 + 1) % bitmap_width
        y2 = y1 + 1 if (x1 + 1) > (bitmap_width - 1) else y1

        # The upper nibble represents the first pixel, and the lower nibble
        # represents the second pixel
        color1 = colors_tuple[byte >> 4]
        color2 = colors_tuple[byte & 0x0F]

        Matrix[x1][y1] = color1
        Matrix[x2][y2] = color2
#        img.putpixel((x1, y1), color1)
#        img.putpixel((x2, y2), color2)

#    img.save(png_name)

def main():

    #Connect to db
    conn = sqlite3.connect("place.sqlite")
    c = conn.cursor()

    image = Image.new("RGB", (1000, 1000), (255,255,255))

    gif = Image.new("RGB", (1000, 1000), (255,255,255))

    next_frame = DELTA_FRAME_TIME + 1490990923

    for row in c.execute('SELECT * FROM starting_bitmaps ORDER BY recieved_on ASC LIMIT 1'):
        bitmap_to_matrix(row[1])

    for row in c.execute('SELECT * FROM placements WHERE recieved_on >= 1490990923 ORDER BY recieved_on'):
        if(row[1] <= 999 and row[2] <= 999):
            Matrix[row[1]][row[2]] = colors_tuple[row[3]]
        if(row[0] > next_frame):
            print("Generating frame " + str(len(gif_frames) + 1) + "...")
            image = Image.new("RGB", (1000, 1000), (255, 255, 255))
            pixels = image.load()
            for y in range(0, len(Matrix)):
                for x in range(0, len(Matrix[y])):
                    pixels[x, y] = Matrix[x][y]
            gif_frames.append(image) #Append the image to the list of images.
            next_frame = next_frame + DELTA_FRAME_TIME
            print("Done\n")
    #        image.putpixel((x,y), (255,255,255))#colors_tuple[Matrix[x][y]])

    gif_file = open("out.gif", "wb")

    gif.save(gif_file, save_all=True, append_images=gif_frames, duration=FRAME_DURATION)

            #   image.show()
#    gif.save('out.gif')


if __name__ == '__main__':
    main()
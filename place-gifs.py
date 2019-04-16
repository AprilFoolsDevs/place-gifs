import sqlite3
from PIL import Image, ImageMode
from enum import Enum
import numpy
import colorsys

#####################
# Heatmap Variables #
#####################

HEATMAP_MAX = 3

HEATMAP_LOW_COLOR = (0, 0, 0)

HEATMAP_HI_COLOR = (255, 0, 0)

class Mode(Enum):
    NORMAL = 0
    HEATMAP = 1

start_time = 1

bitmap_width, bitmap_height = 1000, 1000;

matrix = [[HEATMAP_LOW_COLOR for x in range(bitmap_width)] for y in range(bitmap_height)]

golden_frames = []

gif_frames = []

GIF_LENGTH_SECONDS = 30

MINUTES_PER_FRAME = 5  # The number of real-time minutes per frame

GOLDEN_FRAME_INTERVAL = 30 # Minutes of delta data used until a golden frame is inserted.

FRAMES_PER_SECOND = 10

SECONDS_PER_MINUTE = 60

DELTA_FRAME_TIME = SECONDS_PER_MINUTE * MINUTES_PER_FRAME  # How long is each frame in real time.

FRAME_DURATION = 1 / FRAMES_PER_SECOND  

GOLDEN_FRAME_DELTA = SECONDS_PER_MINUTE * GOLDEN_FRAME_INTERVAL

current_mode = Mode.HEATMAP

colors_tuple = [
    (255, 255, 255),
    (228, 228, 228),
    (136, 136, 136),
    (34, 34, 34),
    (255, 167, 209),
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

    local_matrix = [[(255, 255, 255) for x in range(bitmap_width)] for y in range(bitmap_height)]

    for i, byte in enumerate(bitmap[(header_size + 1):]):
        x1 = (i * 2) % bitmap_width
        y1 = min((i * 2) // bitmap_width, bitmap_height - 1)
        x2 = (x1 + 1) % bitmap_width
        y2 = y1 + 1 if (x1 + 1) > (bitmap_width - 1) else y1

        # The upper nibble represents the first pixel, and the lower nibble
        # represents the second pixel
        color1 = colors_tuple[byte >> 4]
        color2 = colors_tuple[byte & 0x0F]

        local_matrix[x1][y1] = color1
        local_matrix[x2][y2] = color2

    return local_matrix

def matrix_to_image(local_matrix):
    image = Image.new("RGB", (len(local_matrix[0]), len(local_matrix)), (255, 255, 255))
    pixels = image.load()
    for y in range(0, len(local_matrix)):
        for x in range(0, len(local_matrix[y])):
            pixels[x, y] = local_matrix[x][y]
    gif_frames.append(image)  # Append the image to the list of images.

    return image

def setMatrixColor(x, y, code):

    if(current_mode == Mode.NORMAL):
        matrix[x][y] = colors_tuple[code]
    elif(current_mode == Mode.HEATMAP):

        
        maximum_value = map(max, matrix) 

        if maximum_value == 0:
            maximum_value = 1

        heatmap_diff = tuple(numpy.subtract( HEATMAP_HI_COLOR, HEATMAP_LOW_COLOR))
        heatmap_div = tuple(numpy.divide(heatmap_diff, HEATMAP_MAX))
        heatmap_values = tuple(numpy.add(heatmap_div, matrix[x][y]))
        heatmap_final = (int(heatmap_values[0]), int(heatmap_values[1]), int(heatmap_values[2]))
        matrix[x][y] = heatmap_final

def clearMatrix():
    global  matrix
    matrix = [[HEATMAP_LOW_COLOR for x in range(bitmap_width)] for y in range(bitmap_height)]

def main():
    # Connect to db
    conn = sqlite3.connect("place.sqlite")
    placement_cursor = conn.cursor()
    bitmaps_cursor = conn.cursor()

    global matrix

    # This is the timecode of the next variable. Primed to -1.
    next_frame = -1
    next_golden_frame = -1

    earliest_frame = -1

    # Start with just the first bitmap we have. Will add "golden frames" later.
    for row in bitmaps_cursor.execute('SELECT * FROM starting_bitmaps ORDER BY recieved_on'):
        if earliest_frame == -1:
            earliest_frame = row[0]
            if current_mode != Mode.HEATMAP:
                matrix = bitmap_to_matrix(row[1])
        else:
            golden_frames.append(row[0])



    for row in placement_cursor.execute('SELECT * FROM placements WHERE recieved_on >= {time} ORDER BY recieved_on'.format(time = earliest_frame) ):

        # Ensure the current placement is within our boarder, then place it.
        if (row[1] <= 999 and row[2] <= 999):
            setMatrixColor(row[1], row[2], row[3])
#            matrix[row[1]][row[2]] = colors_tuple[row[3]]

        # If the next frame time isn't initialized, initialize it.
        if (next_frame == -1):
            next_frame = row[0] + DELTA_FRAME_TIME
            next_golden_frame = row[0] + GOLDEN_FRAME_DELTA

        # Check if we are at the next golden frame
        if(current_mode != Mode.HEATMAP and len(golden_frames) > 0 and golden_frames[0] <= row[0]):
            if(row[0] >= next_golden_frame):
                print("Inserting Golden Frame...")
                bitmaps_cursor.execute('SELECT * FROM starting_bitmaps WHERE recieved_on = {time}'.format(time = golden_frames[0]))
                data = bitmaps_cursor.fetchone()
                matrix = bitmap_to_matrix(data[1])
                next_golden_frame += GOLDEN_FRAME_DELTA
            golden_frames.remove(golden_frames[0])


        # If the current timecode is passed our next frame time, make a new frame.
        if (row[0] > next_frame):
            print("Generating frame " + str(len(gif_frames) + 1) + "...")
            image = Image.new("RGB", (1000, 1000), (255, 255, 255))
            pixels = image.load()
            for y in range(0, len(matrix)):
                for x in range(0, len(matrix[y])):
                    pixels[x, y] = matrix[x][y]
            gif_frames.append(image)  # Append the image to the list of images.
            clearMatrix()
            next_frame = next_frame + DELTA_FRAME_TIME

        if GIF_LENGTH_SECONDS < len(gif_frames) * FRAME_DURATION:
            break

    gif = gif_frames[0] # Initialize gif variable with the first frame

    gif_frames.remove(gif_frames[0])

    gif_file = open("out.gif", "wb")

    gif.save(gif_file, save_all=True, append_images=gif_frames, duration=FRAME_DURATION, loop=0xffff)


if __name__ == '__main__':
    main()

import matplotlib.colors as mcolors
import random

class Color:
    def __init__(self, list_color):
        self.list_color = list_color

    @staticmethod
    def generate_hex_color(colors):
        # Convert the existing colors to RGB format
        rgb_colors = [mcolors.to_rgb(color) for color in colors]

        # Generate a new color that is not present in the list
        while True:
            new_color = '#{:06x}'.format(random.randint(0, 0xFFFFFF))
            rgb_color = mcolors.to_rgb(new_color)

            # Calculate the minimum distance to existing colors
            min_distance = min(Color.color_distance(rgb_color, rgb) for rgb in rgb_colors)

            # If the distance is greater than a threshold, return the new color
            threshold = 0.5
            if min_distance > threshold:
                return new_color

    @staticmethod
    def color_distance(rgb1, rgb2):
        r1, g1, b1 = rgb1
        r2, g2, b2 = rgb2
        return abs(r1 - r2) + abs(g1 - g2) + abs(b1 - b2)

    def get_new_color(self):
        return self.generate_hex_color(self.list_color)

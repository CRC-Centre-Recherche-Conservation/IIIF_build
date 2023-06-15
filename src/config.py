import os
import json

from src.opt.tools import Color
from path import CONFIG_PATH, INDEX_FILE


class IndexConfig:
    list_colors = {}
    status = False

    def __init__(self, **kwargs):
        self.verbose = kwargs.get('verbose', False)
        for file in os.listdir(CONFIG_PATH):
            if file.lower() == INDEX_FILE:
                if self.verbose:
                    print("Parsing config file colors 'manuscript.json'.")
                with open("config/Manuscript.json") as f:
                    json_file = json.load(f)
                    self.ents = json_file['taxonomy']['descriptors']
                    for ent in self.ents:
                        self.list_colors[ent['targetName']] = ent['targetColor']
                    del json
                    self.status = True
            # If the script don't find 'manuscript.json file in config folder
            else:
                print("We cannot find config file 'manuscript.json' in the config folder")

    def get_idx_microscopy(self) -> list:
        """
        Function to return all analysis in 'image' group
        :return: list of name of analysis
        """
        return [ent['targetName'] for ent in self.ents if ent['targetType'].lower() == 'image']

    def get_color(self, idx_type: str):
        """
        Function to get colors in 'manuscript.json' in config file. If status file is False, the script get new color
        :return: Hexadecimal colors
        """
        if not self.status:
            # if add new type of analysis not in the scheme, but it's better to respect the scheme -> update in config
            if idx_type not in list(self.list_colors):
                print(f"We don't find the type '{idx_type}' in the config file 'manuscript.json'")
                return Color(list(self.list_colors.values())).get_new_color()
            else:
                return self.list_colors[idx_type]
        else:
            print("Generation of color index")
            return Color(list(self.list_colors.values())).get_new_color()

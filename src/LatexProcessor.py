import os
import json
import subprocess
import chardet

from .TikzFinder import TikzFinder
from .ColoredLogger import ColoredLogger

class LatexProcessor:
    def __init__(self, app):
        self.logger = ColoredLogger().logger

        self.app = app
        self.fit_file = self.app.fit_file # 后续可以添加不同的keyword
        self.capable_ids = self.get_capable_ids()
        self.jsonl_file = self.app.jsonl_file
        self.ids_path = self.get_main_file_dict()
        self.logger.debug(self.app.subject_path)
        self.extract_and_save_tikz(self.app.subject_path)

    def get_capable_ids(self):
        if os.path.isfile(self.fit_file):
            with open(self.fit_file, 'r') as file:
                capable_ids = json.load(file)
            return capable_ids
        return []


    def get_main_file_dict(self):
        file_paths_dict = {}
        for id in self.capable_ids:
            file_path = os.path.join(self.app.subject_path, id)
            command = "grep -rl --include='*.tex' --exclude='*_merged.tex' 'documentclass' " + file_path
            try:
                result = subprocess.check_output(command, shell=True)
                file_paths = result.decode('utf-8').strip().split('\n')
                main_file_path = file_paths[0] if file_paths else None
                file_paths_dict[id] = main_file_path
            except subprocess.CalledProcessError:
                file_paths_dict[id] = None
        self.logger.info(f"file_paths_dict:{file_paths_dict}")
        return file_paths_dict




    def extract_and_save_tikz(self, output_directory):
        system_content = "AutomaTikZ: Text-Guided Synthesis of Scientific Vector Graphics with TikZ"
        with open(self.jsonl_file, 'w', encoding='utf-8') as f:
            for id, path in self.ids_path.items():
                try:
                    tikz_finder = TikzFinder(path)
                    tikz_figures = list(tikz_finder.find())

                    for fig in tikz_figures:

                        item = {
                            "messages": [
                                {"role": "system", "content": system_content},
                                {"role": "user", "content": f"iArxiv-{id}:" + fig.caption},
                                {"role": "assistant", "content": fig.code}
                            ]
                        }
                        f.write(json.dumps(item) + '\n')
                    print(f"Separated and saved {len(tikz_figures)} TikZ code:\n--> {path} from {id} to {self.jsonl_file}")
                except Exception as e:
                    self.logger.error(f"Error processing file {path}: {e}")













import os
import tarfile
import shutil
import requests
import json
import concurrent.futures
import chardet
import subprocess

DEBUG = False

class ArxivCollector:
    def __init__(self, app):
        self.app = app
        self.keyword = self.app.keyword
        self.collector_path = self.app.subject_path
        self.json_file = self.app.json_file
        self.fit_file = self.app.fit_file
        self.subject_ids = self.get_subject_ids()
        self.get_fit_list()

    def get_subject_ids(self):
        if os.path.isfile(self.json_file):
            print(f"{self.json_file} is found")
            with open(self.json_file, "r") as file:
                subject_ids = json.load(file)
                print(f"Found {len(subject_ids)} accessible ids:{self.app.subject}")
            return subject_ids
        return []

    def get_fit_list(self):
        fit_ids = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for id in self.subject_ids:
                if executor.submit(
                    self.download_source, self.collector_path, id
                ).result():
                    if executor.submit(
                        self.tar_source, self.collector_path, id
                    ).result():
                        if executor.submit(
                            self.keyword_check,
                            os.path.join(self.collector_path, id),
                            self.keyword,
                        ).result():
                            fit_ids.append(id)
                        else:
                            self._cleanup(id)

        with open(self.fit_file, "w") as file:
            json.dump(fit_ids, file)

    def _cleanup(self, id):
        if os.path.isdir(os.path.join(self.collector_path, f"{id}")):
            shutil.rmtree(os.path.join(self.collector_path, f"{id}"))
        if os.path.isfile(os.path.join(self.collector_path, f"{id}.tar.gz")) and not DEBUG:
            os.remove(os.path.join(self.collector_path, f"{id}.tar.gz"))

    @staticmethod
    def download_source(path, id):
        url = f"https://arxiv.org/e-print/{id}"
        tar_file = os.path.join(path, f"{id}.tar.gz")
        response = requests.get(url)

        if response.status_code == 200:
            with open(tar_file, "wb") as file:
                file.write(response.content)
            return True
        else:
            print(f"Failed download {id}:{os.path.basename(tar_file)}")
            return False

    @staticmethod
    def download_source(path, id):
        url = f"https://arxiv.org/e-print/{id}"
        tar_file = os.path.join(path, f"{id}.tar.gz")

        # If tar_file exists, skip the download 
        if os.path.exists(tar_file):
            print(f"{tar_file} already exists.")
            return True

        response = requests.get(url)

        if response.status_code == 200:
            with open(tar_file, "wb") as file:
                file.write(response.content)
            return True
        else:
            print(f"Failed to download {id}: {os.path.basename(tar_file)}")
            return False



    @staticmethod
    def tar_source(path, id):
        tar_file = os.path.join(path, f'{id}.tar.gz')
        untar_file = os.path.join(path, f'{id}')

        try:
            with tarfile.open(tar_file) as tar:
                tar.extractall(path=untar_file)
            return True
        except Exception as e:
            print(f"Failed unzip {id}:{os.path.basename(tar_file)}")
            if os.path.isfile(tar_file) and not DEBUG:  # Add a condition check here
                os.remove(tar_file)
            return False




    @staticmethod
    def keyword_check(path, keyword):
        command = f'grep -rl --include="*.tex" --exclude="*%*" "{keyword}" {path}'
        try:
            result = subprocess.check_output(command, shell=True)
            if result:  # 如果找到了关键字，grep 命令会返回文件的路径
                print(f"Found {keyword} in a .tex file:{os.path.basename(path)}")
                return True
            else:
                return False
        except subprocess.CalledProcessError:
            return False

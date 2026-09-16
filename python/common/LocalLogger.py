import shutil
import sys
import logging
import os
from datetime import datetime

from common.Logger import Logger
from common.constants import *

LOG_GROUP = "asp-traffic"
ERROR_STREAM = "errors"


class LocalLogger(Logger):
    def __init__(self, experiment, args):
        self.experimentSession = args.experimentSession
        self.printToShell = False
        self.experiment = experiment
        self.timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f") + delim + args.run_name if self.experimentSession else "current"
        if not self.experimentSession:
            current_dir = os.path.join(self.experiment, "current")
            for dir in os.listdir(current_dir):
                shutil.rmtree(os.path.join(current_dir, dir))

        self.logger = logging.getLogger(LOG_GROUP)
        # self.logger.setLevel(logging.INFO)
        self.logger.setLevel(logging.DEBUG)
        self.logger.disabled = args.loggerDisabled

        # Remove existing handlers if they exist (to avoid duplicates)
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # Create log directory
        log_dir = os.path.join(self.experiment, self.timestamp, "logs")
        print(f"Logging to {log_dir}")
        os.makedirs(log_dir, exist_ok=True)

        # Define log file path
        log_file_path = os.path.join(log_dir, "log.txt")

        with open(log_file_path, "w") as log_file:
            log_file.write(datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f") + "\n")
            log_file.write("New experiment\n")

        # File handler (write both INFO and ERROR levels here)
        file_handler = logging.FileHandler(log_file_path)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

    def log(self, message, level=logging.DEBUG):
        if self.printToShell: print(f"[{logging._levelToName[level]}]: {message}")
        self.logger.log(level, message)

    def error(self, error):
        self.logger.error(error)

    def __createStream(self, name):
        pass

    def uploadFile(self, filename: str, content: str):
        directory = os.path.join(self.experiment, self.timestamp, os.path.dirname(filename))
        os.makedirs(directory, exist_ok=True)

        file_path = os.path.join(directory, os.path.basename(filename))
        with open(file_path, "w") as file:
            file.write(content)
        self.logger.info(f"File {file_path} saved locally.")

    def deleteFile(self, filename: str):
        file_path = os.path.join(self.experiment, self.timestamp, os.path.dirname(filename))
        if os.path.exists(file_path):
            os.remove(file_path)
            self.logger.info(f"File {file_path} deleted locally.")
        else:
            self.logger.warning(f"File {file_path} does not exist and cannot be deleted.")
    
    def cleanDirectory(self, directory: str, deleteDir = True):
        dir_path = os.path.join(self.experiment, self.timestamp, directory)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            for root, dirs, files in os.walk(dir_path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            if(deleteDir): os.rmdir(dir_path)
            self.logger.info(f"Directory {dir_path} cleaned locally.")
        else:
            self.logger.warning(f"Directory {dir_path} does not exist and cannot be deleted.")

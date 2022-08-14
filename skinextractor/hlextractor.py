import logging
import struct
import subprocess
from logging import getLogger
from pathlib import Path
from typing import Union, List


class HLExtractor:
    def __init__(self, executable=None, output_dir=None):
        if executable:
            self._executable = executable
        else:
            if struct.calcsize("P") == 8:
                arch = "x64"
            else:
                arch = "x86"
            self._executable = f"third-party/HLExtract/{arch}/HLExtract.exe"

        self._output = output_dir or Path(".")

        logging.debug(f"Initialized HLExtractor with executable {self._executable}, output dir {self._output}")

    def extract(self, archive: Path, path: List[str]):
        assert archive.exists() is True

        cmd = [self._executable, "-p", archive]
        cmd.extend(["-d", self._output])

        for arg in path:
            cmd.extend(["-e", arg])

        logging.debug(f"HLExtractor cmd: {cmd}")
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL)

        return [self._output / entry.split("/")[-1] for entry in path]

    def extract_single(self, archive: Path, path: str):
        return self.extract(archive, [path])[0]

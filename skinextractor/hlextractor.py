import struct
import subprocess
from logging import getLogger
from pathlib import Path
from typing import Union, List

logger = getLogger(__name__)


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

        self._output = output_dir

        logger.debug(f"Initialized HLExtractor with executable {self._executable}, output dir {self._output}")

    def extract(self, archive: Path, path: Union[str, List[str]]):
        assert archive.exists() is True

        cmd = [self._executable, "-p", archive]

        if self._output:
            cmd.extend(["-d", self._output])

        if isinstance(path, str):
            path = [path]

        for arg in path:
            cmd.extend(["-e", arg])

        logger.debug(f"HLExtractor cmd: {cmd}")
        subprocess.check_call(cmd)

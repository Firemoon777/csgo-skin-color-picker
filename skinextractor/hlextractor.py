import struct
import subprocess
from pathlib import Path


class HLExtractor:
    _executable: str
    _vpk: str

    def __init__(self, vpk: Path, executable=None):
        if executable:
            self._executable = executable
        else:
            if struct.calcsize("P") == 8:
                arch = "x64"
            else:
                arch = "x86"
            self._executable = f"third-party/HLExtract/{arch}/HLExtract.exe"

        assert vpk.exists() is True, f"{vpk} doesn't exists!"
        self._vpk = str(vpk)

    def extract(self, vpk_path: str, output: str) -> None:
        cmd = [self._executable, "-p", self._vpk]
        cmd.extend(["-d", output])

        cmd.extend(["-e", vpk_path])

        subprocess.check_call(cmd, stdout=subprocess.DEVNULL)

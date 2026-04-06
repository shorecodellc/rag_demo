#kevin fink
#kevin@shorecode.org
#Mon Apr  6 09:49:55 AM +07 2026
#.py

import os
import sys
import platform
import pathlib
from dataclasses import dataclass, field

@dataclass
class Files:
    current_platform: str = field(init=False)
    filepaths: list = field(default_factory=lambda: ['logging/1.log'])
    win_filepaths: list = field(default_factory=list)

    def __post_init__(self):
        self.current_platform = platform.system()      
        if self.current_platform == 'Windows':
            for f in self.filepaths:
                f = f.replace('/', '\\')
                if getattr(sys, 'frozen', False):
                    f = os.path.join(os.path.dirname(sys.executable), f)
                    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = os.path.dirname(sys.executable)
                else:
                    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), f)
                self.win_filepaths.append(f)
            self.win_filepaths[0] = os.path.join(os.path.dirname(sys.executable), 'logging', '1.log')
        else:
            for idx, f in enumerate(self.filepaths):
                if getattr(sys, 'frozen', False):
                    f = os.path.join(os.path.dirname(sys.executable), f)
                    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = os.path.dirname(sys.executable)
                else:
                    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), f)
                self.filepaths[idx] = f

    def get_files_list(self) -> list:
        if self.current_platform == 'Windows':
            return self.win_filepaths
        else:
            return self.filepaths
        
    def get_file_by_index(self, idx: int) -> str:
        if self.current_platform == 'Windows':
            return self.win_filepaths[idx]
        else:
            return self.filepaths[idx]

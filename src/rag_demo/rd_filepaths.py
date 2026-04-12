from dataclasses import dataclass, field
from pathlib import Path
import os
import sys


@dataclass
class Files:
    filepaths: list[str] = field(default_factory=lambda: [
        "logging/1.log",
        "data",
        "data/c-46.pdf"
    ])

    def __post_init__(self):
        base_dir = self._get_base_dir()

        resolved_paths = []
        for rel_path in self.filepaths:
            full_path = base_dir / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            resolved_paths.append(full_path)

        self.filepaths = resolved_paths

    def _get_base_dir(self) -> Path:
        # 1. Explicit override (BEST)
        env_dir = os.getenv("APP_BASE_DIR")
        if env_dir:
            return Path(env_dir).resolve()

        # 2. Frozen binary
        if getattr(sys, "frozen", False):
            base = Path(sys.executable).parent
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(base)
            return base

        # 3. Fallback: working directory
        return Path.cwd().resolve()

    def get_files_list(self) -> list[str]:
        return [str(p) for p in self.filepaths]

    def get_file_by_index(self, idx: int) -> str:
        return str(self.filepaths[idx])
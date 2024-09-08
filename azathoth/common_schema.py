from pathlib import Path
from typing import Optional

from autom.engine import AutomSchema


RelPathContentMap = dict[Path, str]
"""The map of relative path to content"""


class AutomFrontendFileMap(AutomSchema):
    """Output Schema for AutomSchemaAttacher
    
    The file map key is ALWAYS the relative path
    """
    autom_frontend_root_path: Path
    autom_frontend_file_content_map: RelPathContentMap

    def dump_to_disk(self, autom_frontend_root_path: Optional[Path] = None):
        if autom_frontend_root_path is None:
            autom_frontend_root_path = self.autom_frontend_root_path
        for path, content in self.autom_frontend_file_content_map.items():
            if not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
            with open(autom_frontend_root_path / path, 'w') as f:
                f.write(content)

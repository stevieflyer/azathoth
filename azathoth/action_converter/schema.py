from pathlib import Path

from autom.engine import AutomSchema


class FileActionConvertParams(AutomSchema):
    autom_frontend_root_path: Path
    api_src_fullpath: Path
    action_dst_fullpath: Path


class AutomProjectActionConvertParams(AutomSchema):
    autom_frontend_root_path: Path


ProjectActionConvertPlannerInput = AutomProjectActionConvertParams


class ProjectActionConvertPlan(AutomSchema):
    autom_frontend_root_path: Path
    src_dst_filepaths_pair: list[tuple[Path, Path]]

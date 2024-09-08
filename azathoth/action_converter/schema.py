from pathlib import Path

from autom.engine import AutomSchema


class FileActionConverterInput(AutomSchema):
    autom_frontend_root_path: Path
    api_src_fullpath: Path
    action_dst_fullpath: Path


class FileActionConverterOutput(FileActionConverterInput):
    action_dst_content: str


class AutomProjectActionConverterInput(AutomSchema):
    autom_frontend_root_path: Path


ProjectActionConvertPlannerInput = AutomProjectActionConverterInput


class ProjectActionConvertPlan(AutomSchema):
    autom_frontend_root_path: Path
    src_dst_filepaths_pair: list[tuple[Path, Path]]


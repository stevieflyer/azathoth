from pathlib import Path

from autom.engine import AutomSchema


class AutomProjectAPIConvertParams(AutomSchema):
    autom_backend_root_path: Path
    autom_frontend_root_path: Path


FileEnumeratorInput = AutomProjectAPIConvertParams


class EnumeratedFiles(AutomSchema):
    autom_backend_root_path: Path
    autom_frontend_root_path: Path
    src_file_fullpaths: list[Path]


class FileAPIConverterInput(AutomSchema):
    src_file_fullpath: Path
    autom_backend_root_path: Path
    autom_frontend_root_path: Path


FileAPIConvertPlannerInput = FileAPIConverterInput


class FileAPIConvertPlan(AutomSchema):
    src_file_fullpath: Path
    autom_backend_root_path: Path
    autom_frontend_root_path: Path
    function_name_source_dict: dict[str, str]


class FunctionAPIConverterInput(AutomSchema):
    api_function_source: str
    src_file_fullpath: Path
    dst_file_fullpath: Path
    autom_backend_root_path: Path
    autom_frontend_root_path: Path

from pathlib import Path

from autom import AutomSchema, AutomField, autom_registry


class FileActionConvertParams(AutomSchema):
    autom_frontend_root_path: Path
    api_src_fullpath: Path
    action_dst_fullpath: Path


@autom_registry(is_internal=False)
class AutomProjectActionConvertParams(AutomSchema):
    autom_frontend_root_path: Path = AutomField(
        ...,
        description="The root path of the Autom Frontend Project",
    )


ProjectActionConvertPlannerInput = AutomProjectActionConvertParams


class ProjectActionConvertPlan(AutomSchema):
    autom_frontend_root_path: Path = AutomField(
        ...,
        description="The root path of the Autom Frontend Project",
    )
    src_dst_filepaths_pair: list[tuple[Path, Path]]

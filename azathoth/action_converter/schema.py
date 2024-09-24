from pathlib import Path

from autom import AutomSchema, AutomField, autom_registry, WebUnsupportedFilepath


class FileActionConvertParams(AutomSchema):
    autom_frontend_root_path: WebUnsupportedFilepath
    api_src_fullpath: WebUnsupportedFilepath
    action_dst_fullpath: WebUnsupportedFilepath


@autom_registry(is_internal=False)
class AutomProjectActionConvertParams(AutomSchema):
    autom_frontend_root_path: WebUnsupportedFilepath = AutomField(
        ...,
        description="The root path of the Autom Frontend Project",
    )


ProjectActionConvertPlannerInput = AutomProjectActionConvertParams


class ProjectActionConvertPlan(AutomSchema):
    autom_frontend_root_path: WebUnsupportedFilepath = AutomField(
        ...,
        description="The root path of the Autom Frontend Project",
    )
    src_dst_filepaths_pair: list[tuple[WebUnsupportedFilepath, WebUnsupportedFilepath]]

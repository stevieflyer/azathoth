from pathlib import Path

from autom.engine import AutomSchema, AutomField
from pydantic import model_validator, PositiveInt

from azathoth.common import RepoEnum


class SrcDstFilePairInfo(AutomSchema):
    src_repo_enum: RepoEnum
    src_root_path: Path
    src_filepath: Path
    dst_repo_enum: RepoEnum
    dst_root_path: Path
    dst_filepath: Path

    @model_validator(mode='after')
    def ensure_src_dst_repo_enum_are_different(self):
        if self.src_repo_enum == self.dst_repo_enum:
            raise ValueError(f'src_repo_enum and dst_repo_enum must be different, but got src_repo_enum={self.src_repo_enum}, dst_repo_enum={self.dst_repo_enum}')
        return self


class SegmentSchemaConvertParams(SrcDstFilePairInfo):
    """Input Params for SegmentSchemaConverter

    Contains:
        - metadata about the src/dst repository and file paths
        - the code segment to be converted(actually, it's part of the file content of the src file)
    """
    segment: str

    @model_validator(mode='after')
    def validate_repo_pair(self):
        if self.src_repo_enum == RepoEnum.AUTOM and self.dst_repo_enum != RepoEnum.FRONTEND:
            raise ValueError(f'Only support <autom, frontend> conversion, but got src_repo_enum={self.src_repo_enum}, dst_repo_enum={self.dst_repo_enum}')
        return self


class ConvertedSchemaSegment(AutomSchema):
    """Output of SegmentSchemaConverter"""
    converted_schema: str = AutomField(..., description="String contains the typescript type definitions, which are converted from backend python pydantic models")


class SchemaConvertPlan(AutomSchema):
    src_repo_enum: RepoEnum
    src_root_path: Path
    dst_repo_enum: RepoEnum
    dst_root_path: Path
    max_lines_per_segment: PositiveInt = AutomField(512, description="Max lines per segment, higher value can reduce the overhead prompt cost, lower value can speed up the conversion process")
    src_dst_filepath_pairs: list[tuple[Path, Path]] = AutomField(
        default_factory=list, 
        description="List of (src_filepath, dst_filepath) pairs, all are full file paths"
    )


class AutomProjectSchemaConvertParams(AutomSchema):
    autom_engine_root_path: Path
    autom_backend_root_path: Path
    autom_frontend_root_path: Path
    max_lines_per_segment: PositiveInt = AutomField(512, description="Max lines per segment, higher value can reduce the overhead prompt cost, lower value can speed up the conversion process")


__all__ = [
    'SrcDstFilePairInfo',
    'SegmentSchemaConvertParams',
    'ConvertedSchemaSegment',
    'SchemaConvertPlan',
    'AutomProjectSchemaConvertParams',
]

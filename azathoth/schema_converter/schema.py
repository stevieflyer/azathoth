from enum import StrEnum
from pathlib import Path

from autom.engine import AutomSchema, AutomField
from pydantic import model_validator, PositiveInt


class ProgrammingLanguage(StrEnum):
    python = 'python'
    typescript = 'typescript'


class RepoEnum(StrEnum):
    AUTOM = 'autom'
    BACKEND = 'backend'
    FRONTEND = 'frontend'

    @property
    def repo_language(self) -> ProgrammingLanguage:
        if self == RepoEnum.AUTOM or self == RepoEnum.BACKEND:
            return ProgrammingLanguage.python
        else:
            return ProgrammingLanguage.typescript


class SrcDstFilePairInfo(AutomSchema):
    src_repo_enum: RepoEnum
    src_repo_root: Path
    src_file_relpath: Path
    dst_repo_enum: RepoEnum
    dst_repo_root: Path
    dst_file_relpath: Path
    
    @property
    def src_file_fullpath(self) -> Path:
        return self.src_repo_root / self.src_file_relpath
    
    @property
    def dst_file_fullpath(self) -> Path:
        return self.dst_repo_root / self.dst_file_relpath

    @model_validator(mode='after')
    def ensure_src_dst_repo_enum_are_different(self):
        if self.src_repo_enum == self.dst_repo_enum:
            raise ValueError(f'src_repo_enum and dst_repo_enum must be different, but got src_repo_enum={self.src_repo_enum}, dst_repo_enum={self.dst_repo_enum}')
        return self


class AutomProjectSchemaConverterInput(AutomSchema):
    """
    autom --> autom_frontend
    autom_backend --> autom_frontend
    """
    autom_engine_root_path: Path
    autom_backend_root_path: Path
    autom_frontend_root_path: Path
    max_lines_per_segment: PositiveInt = AutomField(512, description="Max lines per segment, higher value can reduce the overhead prompt cost, lower value can speed up the conversion process")


class SchemaConvertPlan(AutomSchema):
    src_repo_enum: RepoEnum
    src_repo_root: Path
    dst_repo_enum: RepoEnum
    dst_repo_root: Path
    max_lines_per_segment: PositiveInt = AutomField(512, description="Max lines per segment, higher value can reduce the overhead prompt cost, lower value can speed up the conversion process")
    src_dst_relpath_pairs: list[tuple[Path, Path]] = AutomField(default_factory=list, description="List of (src_file_relpath, dst_file_relpath) pairs, all are relative paths")


class FileSchemaConverterInput(SrcDstFilePairInfo):
    max_lines_per_segment: PositiveInt = AutomField(512, description="Max lines per segment, higher value can reduce the overhead prompt cost, lower value can speed up the conversion process")


class FileSchemaConverterOutput(SrcDstFilePairInfo):
    src_file_content: str
    dst_file_content: str


class FileSegmenterInput(FileSchemaConverterInput):
    pass


class FileSegmenterOutput(FileSegmenterInput):
    n_segment: int
    segments: list[str]


class SegmentSchemaConverterInput(SrcDstFilePairInfo):
    segment: str

    @model_validator(mode='after')
    def validate_repo_pair(self):
        if self.src_repo_enum == RepoEnum.AUTOM and self.dst_repo_enum != RepoEnum.FRONTEND:
            raise ValueError(f'Only support <autom, frontend> conversion, but got src_repo_enum={self.src_repo_enum}, dst_repo_enum={self.dst_repo_enum}')
        return self


class SegmentSchemaConverterOutput(SrcDstFilePairInfo):
    converted_segment: str

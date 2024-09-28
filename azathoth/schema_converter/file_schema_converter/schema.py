from pathlib import Path

from pydantic import PositiveInt
from autom.engine import AutomSchema, AutomField

from ..schema import SrcDstFilePairInfo


class FileSchemaConvertParams(SrcDstFilePairInfo):
    max_lines_per_segment: PositiveInt = AutomField(512, description="Max lines per segment, higher value can reduce the overhead prompt cost, lower value can speed up the conversion process")


class SchemaImportConvertParams(AutomSchema):
    src_filepath: Path
    src_root_path: Path
    dst_filepath: Path
    dst_root_path: Path
    imports_content: str


class ConvertedImportsContent(AutomSchema):
    converted_imports_content: str


__all__ = [
    'FileSchemaConvertParams',
    'SchemaImportConvertParams',
    'ConvertedImportsContent',
]

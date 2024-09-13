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

    @classmethod
    def define_examples(cls) -> list[dict]:
        return [
            {
                "src_filepath": "/home/steve/workspace/autom-backend/app/schemas/entities.py",
                "src_root_path": "/home/steve/workspace/autom-backend/",
                "dst_filepath": "/home/steve/workspace/autom-frontend/types/entites.ts",
                "dst_root_path": "/home/steve/workspace/autom-frontend/",
                "imports_content": "from datetime import datetime\nfrom typing import Optional, Annotated\n\nfrom pydantic import EmailStr, Field, StringConstraints, model_validator\nfrom autom.engine.integration_auth import name_regexp, qualifier_regexp, IntegrationAuthSecretMeta\nfrom autom.engine.project import qualifier_regexp, ProjectPublicity, ProjectRunnableStatus, ProjectGitStatus\n\nfrom .base import MyBaseModel\nfrom .enum import RegistryPublicity, IntegrationAuthStatusLiteral, SecretStatusLiteral, WorkerIntegrationAuthorizationLiteral\n"
            },
        ]


class ConvertedImportsContent(AutomSchema):
    converted_imports_content: str


__all__ = [
    'FileSchemaConvertParams',
    'SchemaImportConvertParams',
    'ConvertedImportsContent',
]

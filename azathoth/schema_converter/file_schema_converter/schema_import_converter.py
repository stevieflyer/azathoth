from pathlib import Path

from autom.engine import Request, Response, AgentWorker, Socket, AutomSchema, AggregatorWorker

from azathoth.ast_utils import extract_imports_info
from .schema import SchemaImportConvertParams, ConvertedImportsContent


autom_qualifiers = set([
    'OAuthProviderEnum',
    'SecretRetrievalBy',
    'ProjectPublicity',
    'ProjectRunnableStatus',
    'ProjectGitStatus',
    'IntegrationAuthSecretMeta',
    'IntegrationAuthMeta',
])
excluded_qualifiers = set([
    'MyBaseModel',
])


class SchemaImportConvertParamsAggregator(AggregatorWorker):
    @classmethod
    def define_output_schema(cls) -> AutomSchema | None:
        return SchemaImportConvertParams

    @classmethod
    def define_socket_list(cls) -> list[Socket]:
        return [
            Socket(
                name='set_src_filepath',
                input_type=Path,
                socket_handler=cls._set_src_filepath,
            ),
            Socket(
                name='set_src_root_path',
                input_type=Path,
                socket_handler=cls._set_src_root_path,
            ),
            Socket(
                name='set_dst_filepath',
                input_type=Path,
                socket_handler=cls._set_dst_filepath,
            ),
            Socket(
                name='set_dst_root_path',
                input_type=Path,
                socket_handler=cls._set_dst_root_path,
            ),
            Socket(
                name='set_imports_content',
                input_type=str,
                socket_handler=cls._set_imports_content,
            ),
        ]

    def _set_src_filepath(self, data: Path):
        self._output_as_dict['src_filepath'] = data

    def _set_src_root_path(self, data: Path):
        self._output_as_dict['src_root_path'] = data

    def _set_dst_filepath(self, data: Path):
        self._output_as_dict['dst_filepath'] = data

    def _set_dst_root_path(self, data: Path):
        self._output_as_dict['dst_root_path'] = data

    def _set_imports_content(self, data: str):
        self._output_as_dict['imports_content'] = data


class SchemaImportConverter(AgentWorker):
    """Schema Import Converter for Autom Project
    
    我们要把 Autom Backend 中的 Python pydantic schema 转换为 Autom Frontend 中的 TypeScript Type。
    
    对于 imports, 我们需要

    - 把 src_root_path / 'app/schemas' 中的项目内 imports 全部转换为 dst_root_path / 'types' 中的项目内 imports。
    - 把 autom 中 import 到的特定项目从 dst_root_path / 'types/autom_schemas' 的相对引入
    """
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return SchemaImportConvertParams

    @classmethod
    def define_output_schema(cls) -> AutomSchema | None:
        return ConvertedImportsContent

    def invoke(self, req: Request) -> Response:
        req_body: SchemaImportConvertParams = req.body

        import_froms: dict[str, list[str]] = extract_imports_info(req_body.imports_content).import_froms
        filtered_import_froms: dict[str, list[str]] = {}

        dst_types_dir = req_body.dst_root_path / 'types'
        dst_filepath_depth = len(req_body.dst_filepath.relative_to(dst_types_dir).parts)

        if dst_filepath_depth <= 0:
            raise ValueError("dst_filepath should be in dst_root_path / 'types'")
        elif dst_filepath_depth == 1:
            autom_schemas_module = './autom_schemas'
        else:
            autom_schemas_module = ''.join(['../' for _ in range(dst_filepath_depth - 1)]) + 'autom_schemas'

        for module_name, qualifiers in import_froms.items():
            if module_name.startswith('.'):
                # For relative imports, we need to import all qualifier that is capitalized(because they are classes)
                remained_qualifiers = [qualifier for qualifier in qualifiers if qualifier[0].isupper() and qualifier not in excluded_qualifiers]
                if len(remained_qualifiers) > 0:
                    if '..' in module_name:
                        typescript_module_name = module_name.replace('..', '../')
                    else:
                        typescript_module_name = module_name.replace('.', './')
                    
                    if typescript_module_name not in filtered_import_froms:
                        filtered_import_froms[typescript_module_name] = []
                    filtered_import_froms[typescript_module_name].extend(remained_qualifiers)
            else:
                # For non-relative imports, we only consider `autom` imports
                if module_name.startswith("autom"):
                    remained_qualifiers = [q for q in qualifiers if q in autom_qualifiers]
                    if len(remained_qualifiers) > 0:
                        typescript_module_name = autom_schemas_module
                        if autom_schemas_module not in filtered_import_froms:
                            filtered_import_froms[typescript_module_name] = []
                        filtered_import_froms[typescript_module_name].extend(remained_qualifiers)

        converted_import_lines = [
            f'import {{ {", ".join(qualifiers)} }} from "{module}";'
            for module, qualifiers in filtered_import_froms.items()
        ]
        converted_import_lines.sort(key=lambda x: len(x))
        converted_imports_content = '\n'.join(converted_import_lines)
        return Response[ConvertedImportsContent].from_worker(self).success(
            body=ConvertedImportsContent(
                converted_imports_content=converted_imports_content
            )
        )


__all__ = [
    'SchemaImportConvertParamsAggregator',
    'SchemaImportConverter',
]

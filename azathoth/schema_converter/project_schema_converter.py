from pathlib import Path

from autom.engine import (
    autom_registry,
    DispatchBridgeWorker, AutomSchema, AutomGraph, Node, Link, GraphAgentWorker,
    Request, Response, AgentWorker, PluggerWorker, SocketRequestBody, SocketCall,
)
from autom.official import HolderAgentWorker, IdentityBridgeWorker, NullPlugger

from azathoth.common import (
    RepoEnum, TSExportHelperInputAggregator, FilesDumper,
    TSExportHerlper, FilesContentAggregator, FilesContentFilesContentPlugger, FileContentFilesContentCollectPlugger,
)
from .schema import AutomProjectSchemaConvertParams, SchemaConvertPlan
from .file_schema_converter import FileSchemaConverter, FileSchemaConvertParams


class InnerSchemaConverter(GraphAgentWorker):
    @classmethod
    def define_graph(cls) -> AutomGraph:
        graph = AutomGraph()

        entry_node = Node.from_worker(HolderAgentWorker().with_schema(AutomProjectSchemaConvertParams))
        entry_planner_bridge = Link.from_worker(IdentityBridgeWorker())
        planner = Node.from_worker(BackendSchemaConvertPlanner())
        planner_file_converter_dispatch_bridge = Link.from_worker(PlannerFileConverterDispatchBridge())
        file_converter = Node.from_worker(FileSchemaConverter())
        converter_exit_collect_plugger = Link.from_worker(FileContentFilesContentCollectPlugger())
        exit_aggregator = Node.from_worker(FilesContentAggregator())

        graph.add_node(entry_node)
        graph.add_node(planner)
        graph.add_node(file_converter)
        graph.add_node(exit_aggregator)

        graph.bridge(entry_node, planner, entry_planner_bridge)
        graph.bridge(planner, file_converter, planner_file_converter_dispatch_bridge)
        graph.plug(file_converter, exit_aggregator, converter_exit_collect_plugger)

        graph.set_entry_node(entry_node)
        graph.set_exit_node(exit_aggregator)

        return graph


@autom_registry(is_internal=False)
class BackendSchemaConverter(GraphAgentWorker):
    @classmethod
    def define_graph(cls) -> AutomGraph:
        graph = AutomGraph()

        entry_node = Node.from_worker(HolderAgentWorker().with_schema(AutomProjectSchemaConvertParams))
        entry_inner_schema_converter_bridge = Link.from_worker(IdentityBridgeWorker())
        inner_schema_converter = Node.from_worker(InnerSchemaConverter())
        inner_schema_converter_schema_files_dumper_bridge = Link.from_worker(IdentityBridgeWorker())
        schema_files_dumper = Node.from_worker(FilesDumper())
        schema_files_dumper_ts_export_aggregator_plugger = Link.from_worker(NullPlugger())
        schema_files_dumper_exit_plugger = Link.from_worker(FilesContentFilesContentPlugger())

        entry_ts_export_aggregator_plugger = Link.from_worker(SchemaConverterParamsTSExportHelperPlugger())
        ts_export_aggregator = Node.from_worker(TSExportHelperInputAggregator())
        ts_export_aggregator_ts_export_helper_bridge = Link.from_worker(IdentityBridgeWorker())
        ts_export_helper = Node.from_worker(TSExportHerlper())
        ts_export_helper_index_files_dumper_bridge = Link.from_worker(IdentityBridgeWorker())
        index_files_dumper = Node.from_worker(FilesDumper())
        index_files_dumper_exit_plugger = Link.from_worker(FilesContentFilesContentPlugger())
        exit_aggregator = Node.from_worker(FilesContentAggregator())

        graph.add_node(entry_node)
        graph.add_node(inner_schema_converter)
        graph.add_node(schema_files_dumper)
        graph.add_node(ts_export_aggregator)
        graph.add_node(ts_export_helper)
        graph.add_node(index_files_dumper)
        graph.add_node(exit_aggregator)

        graph.bridge(entry_node, inner_schema_converter, entry_inner_schema_converter_bridge)
        graph.bridge(inner_schema_converter, schema_files_dumper, inner_schema_converter_schema_files_dumper_bridge)
        graph.plug(schema_files_dumper, exit_aggregator, schema_files_dumper_exit_plugger)
        graph.plug(schema_files_dumper, ts_export_aggregator, schema_files_dumper_ts_export_aggregator_plugger)
        graph.plug(entry_node, ts_export_aggregator, entry_ts_export_aggregator_plugger)
        graph.bridge(ts_export_aggregator, ts_export_helper, ts_export_aggregator_ts_export_helper_bridge)
        graph.bridge(ts_export_helper, index_files_dumper, ts_export_helper_index_files_dumper_bridge)
        graph.plug(index_files_dumper, exit_aggregator, index_files_dumper_exit_plugger)

        graph.set_entry_node(entry_node)
        graph.set_exit_node(exit_aggregator)

        return graph


class PlannerFileConverterDispatchBridge(DispatchBridgeWorker):
    @classmethod
    def define_src_schema(cls):
        return SchemaConvertPlan

    @classmethod
    def define_dst_schema(cls):
        return FileSchemaConvertParams

    def dispatch(self, req: Request) -> dict[int, Response]:
        req_body: SchemaConvertPlan = req.body
        responses: dict[int, Response[FileSchemaConvertParams]] = {}

        # Iterate through the src_dst_filepath_pairs and create FileSchemaConverterInput for each
        for idx, (src_filepath, dst_filepath) in enumerate(req_body.src_dst_filepath_pairs):
            # Create a FileSchemaConverterInput for each pair
            converter_input = FileSchemaConvertParams(
                src_repo_enum=req_body.src_repo_enum,
                src_root_path=req_body.src_root_path,
                src_filepath=src_filepath,
                dst_repo_enum=req_body.dst_repo_enum,
                dst_root_path=req_body.dst_root_path,
                dst_filepath=dst_filepath,
                max_lines_per_segment=req_body.max_lines_per_segment,
            )

            # Wrap in a Response and store it in the responses dict
            responses[idx] = Response[FileSchemaConvertParams].from_worker(self).success(body=converter_input)

        return responses


class SchemaConverterParamsTSExportHelperPlugger(PluggerWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return AutomProjectSchemaConvertParams

    def invoke(self, req: Request) -> Response:
        req_body: AutomProjectSchemaConvertParams = req.body
        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(
                calls=[
                    SocketCall(
                        socket_name="set_project_root_path",
                        data=req_body.autom_frontend_root_path,
                    ),
                    SocketCall(
                        socket_name="set_module_to_exports",
                        data=[
                            req_body.autom_frontend_root_path / 'types',
                        ],
                    )
                ]
            )
        )


class BackendSchemaConvertPlanner(AgentWorker):
    @classmethod
    def define_input_schema(cls):
        return AutomProjectSchemaConvertParams

    @classmethod
    def define_output_schema(cls):
        return SchemaConvertPlan

    def invoke(self, req: Request) -> Response:
        req_body: AutomProjectSchemaConvertParams = req.body

        # backend /app/schemas directory --> frontend /types directory
        backend_repo_root = req_body.autom_backend_root_path
        frontend_repo_root = req_body.autom_frontend_root_path
        backend_schemas_dir = backend_repo_root / 'app/schemas'
        frontend_types_dir = frontend_repo_root / 'types'
        excluded_files = ['__init__.py']

        src_dst_filepath_pairs: list[tuple[Path, Path]] = []
        # iterate through the backend schemas directory
        for src_filepath in backend_schemas_dir.rglob('*.py'):  # Find all Python files recursively
            # Skip excluded files
            if src_filepath.name in excluded_files:
                continue

            # Construct the corresponding destination path in the frontend types dir
            dst_filepath = frontend_types_dir / src_filepath.relative_to(backend_schemas_dir).with_suffix('.ts')  # Change .py to .ts

            # Add the source and destination file paths as a tuple, use relative paths
            src_dst_filepath_pairs.append((src_filepath, dst_filepath))

        # Create the response
        return Response[SchemaConvertPlan].from_worker(self).success(body=SchemaConvertPlan(
            src_repo_enum=RepoEnum.BACKEND,
            src_root_path=backend_repo_root,
            dst_repo_enum=RepoEnum.FRONTEND,
            dst_root_path=frontend_repo_root,
            max_lines_per_segment=req_body.max_lines_per_segment,
            src_dst_filepath_pairs=src_dst_filepath_pairs
        ))

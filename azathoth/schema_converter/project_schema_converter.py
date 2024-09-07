from typing import Dict
from autom.engine import (
    Request, Response, AgentWorker, PluggerWorker, AggregatorWorker,
    DispatchBridgeWorker, CollectPluggerWorker,AutomSchema, BatchRequestSchema,
    AutomGraph, Node, Link, GraphAgentWorker, Socket, SocketCall, SocketRequestBody,
)
from autom.official import HolderAgentWorker, IdentityBridgeWorker

from .schema import *
from .file_schema_converter import FileSchemaConverter


# Project Schema Converter
class FrontendFileMapFronednFileMapPluggerWorker(PluggerWorker):
    @classmethod
    def define_input_schema(cls):
        return AutomFrontendFileMap

    def invoke(self, req: Request) -> Response:
        pass


class AutomProjectSchemaConverter(GraphAgentWorker):
    @classmethod
    def define_graph(cls) -> AutomGraph:
        graph = AutomGraph()

        entry_node = Node.from_worker(HolderAgentWorker().with_schema(AutomProjectSchemaConverterInput))
        entry_engine_bridge = Link.from_worker(IdentityBridgeWorker())
        entry_backend_bridge = Link.from_worker(IdentityBridgeWorker())
        engine_schema_converter = Node.from_worker(EngineSchemaConverter())
        backend_schema_converter = Node.from_worker(BackendSchemaConverter())
        engine_exit_plugger = Link.from_worker(FrontendFileMapFronednFileMapPluggerWorker())
        backend_exit_plugger = Link.from_worker(FrontendFileMapFronednFileMapPluggerWorker())
        exit_aggregator = Node.from_worker(AutomFrontendFileMapAggregator())

        graph.add_node(entry_node)
        graph.bridge(entry_node, engine_schema_converter, entry_engine_bridge)
        graph.bridge(entry_node, backend_schema_converter, entry_backend_bridge)
        graph.plug(engine_schema_converter, exit_aggregator, engine_exit_plugger)
        graph.plug(backend_schema_converter, exit_aggregator, backend_exit_plugger)
        graph.add_node(exit_aggregator)

        graph.set_entry_node(entry_node)
        graph.set_exit_node(exit_aggregator)

        return graph


# Repo Schema Converter: BackendSchemaConverter, EngineSchemaConverter
class AutomFrontendFileMapAggregator(AggregatorWorker):
    @classmethod
    def define_output_schema(cls):
        return AutomFrontendFileMap

    @classmethod
    def define_socket_list(cls) -> list[Socket]:
        return [
            Socket(
                name='set_autom_frontend_root_path',
                input_type=Path,
                socket_handler=cls._set_autom_frontend_root_path,
            ),
            Socket(
                name='update_file_map',
                input_type=dict,
                socket_handler=cls._update_file_map,
            )
        ]
    
    def _set_autom_frontend_root_path(self, data: Path):
        self._output_as_dict['autom_frontend_root_path'] = data

    def _update_file_map(self, data: dict):
        for key, value in data.items():
            if not isinstance(key, Path) or not isinstance(value, str):
                raise TypeError(f"Expected dict[Path, str], got {type(key)}[{type(value)}]")

        if 'autom_frontend_file_content_map' not in self._output_as_dict:
            self._output_as_dict['autom_frontend_file_content_map'] = {}
        self._output_as_dict['autom_frontend_file_content_map'].update(data)


class ConverterInputFrontendFileMapPlugger(PluggerWorker):
    @classmethod
    def define_input_schema(cls):
        return AutomProjectSchemaConverterInput

    def invoke(self, req: Request) -> Response:
        req_body: AutomProjectSchemaConverterInput = req.body
        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(
                calls=[
                    SocketCall(
                        socket_name='set_autom_frontend_root_path',
                        data=req_body.autom_frontend_root_path,
                    )
                ]
            )
        )


class PlannerFileConverterDispatchBridgeWorker(DispatchBridgeWorker):
    @classmethod
    def define_src_schema(cls):
        return SchemaConvertPlan
    
    @classmethod
    def define_dst_schema(cls):
        return FileSchemaConverterInput

    def dispatch(self, req: Request) -> Dict[int, Response]:
        req_body: SchemaConvertPlan = req.body
        responses: dict[int, Response[FileSchemaConverterInput]] = {}

        # Iterate through the src_dst_relpath_pairs and create FileSchemaConverterInput for each
        for idx, (src_relpath, dst_relpath) in enumerate(req_body.src_dst_relpath_pairs):
            # Create a FileSchemaConverterInput for each pair
            converter_input = FileSchemaConverterInput(
                src_repo_enum=req_body.src_repo_enum,
                src_repo_root=req_body.src_repo_root,
                src_file_relpath=src_relpath,
                dst_repo_enum=req_body.dst_repo_enum,
                dst_repo_root=req_body.dst_repo_root,
                dst_file_relpath=dst_relpath,
                max_lines_per_segment=req_body.max_lines_per_segment,
            )

            # Wrap in a Response and store it in the responses dict
            responses[idx] = Response[FileSchemaConverterInput].from_worker(self).success(body=converter_input)

        return responses


class FileSchemaConverterOutputFrontendFileMapCollectPlugger(CollectPluggerWorker):
    @classmethod
    def define_src_schema(cls) -> AutomSchema:
        return FileSchemaConverterOutput
    
    def invoke(self, req: Request[BatchRequestSchema]) -> Response:
        req_body: BatchRequestSchema[FileSchemaConverterOutput] = req.body
        calls = []

        for i, req_item in req_body.batch_requests.items():
            req_item_body: FileSchemaConverterOutput = req_item.body
            calls.append(SocketCall(
                socket_name='update_file_map',
                data={req_item_body.dst_file_fullpath : req_item_body.dst_file_content}
            ))

        return Response[SocketRequestBody].from_worker(self).success(
            SocketRequestBody(calls=calls)
        )


class BackendSchemaConverter(GraphAgentWorker):
    @classmethod
    def define_graph(cls) -> AutomGraph:
        graph = AutomGraph()
        
        entry_node = Node.from_worker(HolderAgentWorker().with_schema(AutomProjectSchemaConverterInput))
        entry_exit_plugger = Link.from_worker(ConverterInputFrontendFileMapPlugger())
        entry_planner_bridge = Link.from_worker(IdentityBridgeWorker())
        planner = Node.from_worker(BackendSchemaConvertPlanner())
        planner_fileConverter_dispatch_bridge = Link.from_worker(PlannerFileConverterDispatchBridgeWorker())
        file_converter = Node.from_worker(FileSchemaConverter())
        converter_exit_collect_plugger = Link.from_worker(FileSchemaConverterOutputFrontendFileMapCollectPlugger())
        exit_aggregator = Node.from_worker(AutomFrontendFileMapAggregator())

        graph.add_node(entry_node)
        graph.add_node(planner)
        graph.add_node(file_converter)
        graph.add_node(exit_aggregator)

        graph.plug(entry_node, exit_aggregator, entry_exit_plugger)
        graph.bridge(entry_node, planner, entry_planner_bridge)
        graph.bridge(planner, file_converter, planner_fileConverter_dispatch_bridge)
        graph.plug(file_converter, exit_aggregator, converter_exit_collect_plugger)

        graph.set_entry_node(entry_node)
        graph.set_exit_node(exit_aggregator)

        return graph


class EngineSchemaConverter(GraphAgentWorker):
    @classmethod
    def define_graph(cls) -> AutomGraph:
        graph = AutomGraph()
        
        entry_node = Node.from_worker(HolderAgentWorker().with_schema(AutomProjectSchemaConverterInput))
        entry_exit_plugger = Link.from_worker(ConverterInputFrontendFileMapPlugger())
        entry_planner_bridge = Link.from_worker(IdentityBridgeWorker())
        planner = Node.from_worker(EngineSchemaConvertPlanner())
        planner_fileConverter_dispatch_bridge = Link.from_worker(PlannerFileConverterDispatchBridgeWorker())
        file_converter = Node.from_worker(FileSchemaConverter())
        converter_exit_collect_plugger = Link.from_worker(FileSchemaConverterOutputFrontendFileMapCollectPlugger())
        exit_aggregator = Node.from_worker(AutomFrontendFileMapAggregator())

        graph.add_node(entry_node)
        graph.add_node(planner)
        graph.add_node(file_converter)
        graph.add_node(exit_aggregator)

        graph.plug(entry_node, exit_aggregator, entry_exit_plugger)
        graph.bridge(entry_node, planner, entry_planner_bridge)
        graph.bridge(planner, file_converter, planner_fileConverter_dispatch_bridge)
        graph.plug(file_converter, exit_aggregator, converter_exit_collect_plugger)

        graph.set_entry_node(entry_node)
        graph.set_exit_node(exit_aggregator)

        return graph


## BackendSchemaConvertPlanner
class BackendSchemaConvertPlanner(AgentWorker):
    @classmethod
    def define_input_schema(cls):
        return AutomProjectSchemaConverterInput

    @classmethod
    def define_output_schema(cls):
        return SchemaConvertPlan

    def invoke(self, req: Request) -> Response:
        req_body: AutomProjectSchemaConverterInput = req.body

        # backend /app/schemas directory --> frontend /types directory
        backend_repo_root = req_body.autom_backend_root_path
        frontend_repo_root = req_body.autom_frontend_root_path
        backend_schemas_dir = backend_repo_root / 'app/schemas'
        frontend_types_dir = frontend_repo_root / 'types'
        excluded_files = ['__init__.py']

        src_dst_relpath_pairs: list[tuple[Path, Path]] = []
        # iterate through the backend schemas directory
        for src_file in backend_schemas_dir.rglob('*.py'):  # Find all Python files recursively
            # Skip excluded files
            if src_file.name in excluded_files:
                continue

            # Construct the corresponding destination path in the frontend types dir
            dst_file = frontend_types_dir / src_file.relative_to(backend_schemas_dir).with_suffix('.ts')  # Change .py to .ts

            # Calculate the relative path to each project root
            src_file_relpath = src_file.relative_to(backend_repo_root)
            dst_file_relpath = dst_file.relative_to(frontend_repo_root)

            # Add the source and destination file paths as a tuple, use relative paths
            src_dst_relpath_pairs.append((src_file_relpath, dst_file_relpath))

        # Create the response
        return Response[SchemaConvertPlan].from_worker(self).success(body=SchemaConvertPlan(
            src_repo_enum=RepoEnum.BACKEND,
            src_repo_root=backend_repo_root,
            dst_repo_enum=RepoEnum.FRONTEND,
            dst_repo_root=frontend_repo_root,
            max_lines_per_segment=req_body.max_lines_per_segment,
            src_dst_relpath_pairs=src_dst_relpath_pairs
        ))


## EngineSchemaConvertPlanner
class EngineSchemaConvertPlanner(AgentWorker):
    @classmethod
    def define_input_schema(cls):
        return AutomProjectSchemaConverterInput

    @classmethod
    def define_output_schema(cls):
        return SchemaConvertPlan

    def invoke(self, req: Request) -> Response:
        pass

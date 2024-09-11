from autom.engine import (
    AutomSchema, Request, Response,
    AgentWorker, DispatchBridgeWorker, GraphAgentWorker, AutomGraph, Node, Link, 
)
from autom.official import HolderAgentWorker, IdentityBridgeWorker

from azathoth.common import FilesContentAggregator, FileContentFilesContentCollectPlugger
from ..ast_utils import extract_python_parts
from .schema import *
from .function_api_converter import FunctionAPIConverter


class FileAPIConvertPlanner(AgentWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return FileAPIConvertPlannerInput

    @classmethod
    def define_output_schema(cls) -> AutomSchema | None:
        return FileAPIConvertPlan
    
    def invoke(self, req: Request) -> Response:
        req_body: FileAPIConverterInput = req.body
        python_parts = extract_python_parts(file_path=req_body.src_file_fullpath, project_root=req_body.autom_backend_root_path)
        return Response[FileAPIConvertPlan].from_worker(self).success(
            body=FileAPIConvertPlan(
                src_file_fullpath=req_body.src_file_fullpath,
                autom_backend_root_path=req_body.autom_backend_root_path,
                autom_frontend_root_path=req_body.autom_frontend_root_path,
                function_name_source_dict=python_parts.get_function_name_source_dict(with_dependencies=False)
            )
        )


class FileAPIConverter(GraphAgentWorker):
    @classmethod
    def define_graph(cls) -> AutomGraph:
        graph = AutomGraph()

        entry_node = Node.from_worker(HolderAgentWorker().with_schema(FileAPIConverterInput))
        entry_planner_bridge = Link.from_worker(IdentityBridgeWorker())
        planner = Node.from_worker(FileAPIConvertPlanner())
        planner_function_api_converter_dispatch_bridge = Link.from_worker(PlannerFunctionAPIConverterDispatchBridgeWorker())
        function_api_converter = Node.from_worker(FunctionAPIConverter())
        function_api_converter_exit_collect_plugger = Link.from_worker(FileContentFilesContentCollectPlugger())
        exit_aggregator = Node.from_worker(FilesContentAggregator())

        graph.add_node(entry_node)
        graph.add_node(planner)
        graph.add_node(function_api_converter)
        graph.add_node(exit_aggregator)

        graph.bridge(entry_node, planner, entry_planner_bridge)
        graph.bridge(planner, function_api_converter, planner_function_api_converter_dispatch_bridge)
        graph.plug(function_api_converter, exit_aggregator, function_api_converter_exit_collect_plugger)

        graph.set_entry_node(entry_node)
        graph.set_exit_node(exit_aggregator)

        return graph


class PlannerFunctionAPIConverterDispatchBridgeWorker(DispatchBridgeWorker):
    @classmethod
    def define_src_schema(cls) -> AutomSchema:
        return FileAPIConvertPlan

    @classmethod
    def define_dst_schema(cls) -> AutomSchema:
        return FunctionAPIConverterInput

    def dispatch(self, req: Request) -> dict[int, Response]:
        req_body: FileAPIConvertPlan = req.body
        batch_responses: dict[int, Response[FunctionAPIConverterInput]] = {}
        
        router_name = req_body.src_file_fullpath.stem

        for function_name, function_source in req_body.function_name_source_dict.items():
            batch_responses[len(batch_responses)] = Response[FunctionAPIConverterInput].from_worker(self).success(
                body=FunctionAPIConverterInput(
                    api_function_source=function_source,
                    src_file_fullpath=req_body.src_file_fullpath,
                    dst_file_fullpath=req_body.autom_frontend_root_path / f"lib/backend-api/{router_name}/{function_name}.ts",
                    autom_backend_root_path=req_body.autom_backend_root_path,
                    autom_frontend_root_path=req_body.autom_frontend_root_path,
                )
            )

        return batch_responses

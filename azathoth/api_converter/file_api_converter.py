from autom.engine import (
    AutomSchema, Request, Response, BatchRequestSchema,
    GraphAgentWorker, AutomGraph, Node, Link, SocketCall, SocketRequestBody,
    AgentWorker, PluggerWorker, DispatchBridgeWorker, CollectPluggerWorker,
)
from autom.official import HolderAgentWorker, IdentityBridgeWorker

from ..common_agent import *
from ..common_schema import *
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
        entry_exit_plugger = Link.from_worker(FileAPIConverterEntryExitPlugger()) 
        planner = Node.from_worker(FileAPIConvertPlanner())
        planner_function_api_converter_dispatch_bridge = Link.from_worker(PlannerFunctionAPIConverterDispatchBridgeWorker())
        function_api_converter = Node.from_worker(FunctionAPIConverter())
        function_api_converter_exit_collect_plugger = Link.from_worker(FunctionAPIConverterExitCollectPlugger())
        exit_aggregator = Node.from_worker(AutomFrontendFileMapAggregator())

        graph.add_node(entry_node)
        graph.add_node(planner)
        graph.add_node(function_api_converter)
        graph.add_node(exit_aggregator)

        graph.plug(entry_node, exit_aggregator, entry_exit_plugger)
        graph.bridge(entry_node, planner, entry_planner_bridge)
        graph.bridge(planner, function_api_converter, planner_function_api_converter_dispatch_bridge)
        graph.plug(function_api_converter, exit_aggregator, function_api_converter_exit_collect_plugger)

        graph.set_entry_node(entry_node)
        graph.set_exit_node(exit_aggregator)

        return graph


class FileAPIConverterEntryExitPlugger(PluggerWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return FileAPIConverterInput

    def invoke(self, req: Request) -> Response:
        req_body: FileAPIConverterInput = req.body
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
                    dst_file_fullpath=req_body.autom_frontend_root_path / f"lib/backend_api/{router_name}/{function_name}.ts",
                    autom_backend_root_path=req_body.autom_backend_root_path,
                    autom_frontend_root_path=req_body.autom_frontend_root_path,
                )
            )

        return batch_responses


class FunctionAPIConverterExitCollectPlugger(CollectPluggerWorker):
    @classmethod
    def define_src_schema(cls) -> AutomSchema:
        return FunctionAPIConverterOutput

    def invoke(self, req: Request[BatchRequestSchema]) -> Response:
        req_body: BatchRequestSchema[FunctionAPIConverterOutput] = req.body
        
        calls = []
        for i, req_item in req_body.batch_requests.items():
            req_item_body: FunctionAPIConverterOutput = req_item.body
            calls.append(SocketCall(
                socket_name='update_file_map',
                data={req_item_body.dst_file_fullpath: req_item_body.frontend_api_source},
            ))
        
        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(calls=calls)
        )

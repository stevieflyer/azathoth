from typing import Type
from autom.engine import (
    AutomSchema, Request, Response,
    AgentWorker, PluggerWorker, DispatchBridgeWorker,
    GraphAgentWorker, AutomGraph, Node, Link, SocketCall, SocketRequestBody,
)
from autom.engine.graph.base import BatchRequestSchema
from autom.official import HolderAgentWorker, IdentityBridgeWorker

from ..common_agent import *
from ..common_schema import *
from .schema import *
from .file_action_converter import FileActionConverter


class AutomProjectActionConverter(GraphAgentWorker):
    @classmethod
    def define_graph(cls) -> AutomGraph:
        graph = AutomGraph()

        entry_node = Node.from_worker(HolderAgentWorker().with_schema(AutomProjectActionConverterInput))
        entry_exit_plugger = Link.from_worker(AutomProjectActionConverterEntryExitPlugger())
        entry_planner_bridge = Link.from_worker(IdentityBridgeWorker())
        project_action_convert_planner = Node.from_worker(ProjectActionConvertPlanner())
        planner_file_action_converter_dispatch_bridge = Link.from_worker(PlannerFileActionConverterDispatchBridgeWorker())
        file_action_converter = Node.from_worker(FileActionConverter())
        file_action_converter_exit_collect_plugger = Link.from_worker(FileActionConverterFileMapCollectPlugger())
        exit_aggregator = Node.from_worker(AutomFrontendFileMapAggregator())

        graph.add_node(entry_node)
        graph.add_node(project_action_convert_planner)
        graph.add_node(file_action_converter)
        graph.add_node(exit_aggregator)

        graph.plug(entry_node, exit_aggregator, entry_exit_plugger)
        graph.bridge(entry_node, project_action_convert_planner, entry_planner_bridge)
        graph.bridge(project_action_convert_planner, file_action_converter, planner_file_action_converter_dispatch_bridge)
        graph.plug(file_action_converter, exit_aggregator, file_action_converter_exit_collect_plugger)

        graph.set_entry_node(entry_node)
        graph.set_exit_node(exit_aggregator)

        return graph


class ProjectActionConvertPlanner(AgentWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return ProjectActionConvertPlannerInput
    
    @classmethod
    def define_output_schema(cls) -> AutomSchema | None:
        return ProjectActionConvertPlan
    
    def invoke(self, req: Request) -> Response:
        req_body: ProjectActionConvertPlannerInput = req.body
        autom_frontend_root_path = req_body.autom_frontend_root_path

        src_api_dir = autom_frontend_root_path / 'lib/backend_api/'
        dst_action_dir = autom_frontend_root_path / 'app/_actions/'
        excluded_path = src_api_dir / 'config.ts'
        excluded_files = ['index.ts']

        # iterate over all files in the backend api directory except for the excluded files using rglob
        src_file_fullpaths = list(src_api_dir.rglob('*.ts'))
        src_file_fullpaths = [f for f in src_file_fullpaths if f != excluded_path and f.name not in excluded_files]

        src_dst_filepaths_pair: list[tuple[Path, Path]] = []
        for src_file_fullpath in src_file_fullpaths:
            relpath = src_file_fullpath.relative_to(src_api_dir)
            dst_file_fullpath = dst_action_dir / relpath
            src_dst_filepaths_pair.append((src_file_fullpath, dst_file_fullpath))
        
        return Response[ProjectActionConvertPlan].from_worker(self).success(
            body=ProjectActionConvertPlan(
                autom_frontend_root_path=autom_frontend_root_path,
                src_dst_filepaths_pair=src_dst_filepaths_pair,
            )
        )


class PlannerFileActionConverterDispatchBridgeWorker(DispatchBridgeWorker):
    @classmethod
    def define_src_schema(cls) -> AutomSchema:
        return ProjectActionConvertPlan
    
    @classmethod
    def define_dst_schema(cls) -> AutomSchema:
        return FileActionConverterInput

    def dispatch(self, req: Request) -> dict[int, Response]:
        req_body: ProjectActionConvertPlan = req.body
        batch_responses: dict[int, Response[FileActionConverterInput]] = {}
        
        for i, (src_file_fullpath, dst_file_fullpath) in enumerate(req_body.src_dst_filepaths_pair):
            batch_responses[i] = Response[FileActionConverterInput].from_worker(self).success(
                body=FileActionConverterInput(
                    autom_frontend_root_path=req_body.autom_frontend_root_path,
                    api_src_fullpath=src_file_fullpath,
                    action_dst_fullpath=dst_file_fullpath,
                )
            )

        return batch_responses


class FileActionConverterFileMapCollectPlugger(CollectPluggerWorker):
    @classmethod
    def define_src_schema(cls) -> AutomSchema:
        return FileActionConverterOutput
    
    def invoke(self, req: Request[BatchRequestSchema]) -> Response:
        req_body: BatchRequestSchema[FileActionConverterOutput] = req.body
        
        calls = []
        for i, req_item in req_body.batch_requests.items():
            req_item_body: FileActionConverterOutput = req_item.body
            calls.append(
                SocketCall(
                    socket_name='update_file_map',
                    data={req_item_body.action_dst_fullpath: req_item_body.action_dst_content},
                )
            )

        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(calls=calls)
        )


class AutomProjectActionConverterEntryExitPlugger(PluggerWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return AutomProjectActionConverterInput

    def invoke(self, req: Request) -> Response:
        req_body: AutomProjectActionConverterInput = req.body

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

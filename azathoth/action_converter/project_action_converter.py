from pathlib import Path

from autom.engine import (
    AutomSchema, Request, Response, SocketCall, SocketRequestBody, autom_registry,
    PluggerWorker, AgentWorker, DispatchBridgeWorker, GraphAgentWorker, AutomGraph, Node, Link,
)
from autom.official import HolderAgentWorker, IdentityBridgeWorker, NullPlugger

from azathoth.common import (
    TSExportHelperInputAggregator, FilesDumper,
    FilesContentAggregator, FileContentFilesContentCollectPlugger, TSExportHerlper, FilesContentFilesContentPlugger
)
from .file_action_converter import FileActionConverter
from .schema import AutomProjectActionConvertParams, ProjectActionConvertPlannerInput, ProjectActionConvertPlan, FileActionConvertParams


class InnerActionConverter(GraphAgentWorker):
    @classmethod
    def define_graph(cls) -> AutomGraph:
        graph = AutomGraph()

        entry_node = Node.from_worker(HolderAgentWorker().with_schema(AutomProjectActionConvertParams))
        entry_planner_bridge = Link.from_worker(IdentityBridgeWorker())
        project_action_convert_planner = Node.from_worker(ProjectActionConvertPlanner())
        planner_file_action_converter_dispatch_bridge = Link.from_worker(PlannerFileActionConverterDispatchBridge())
        file_action_converter = Node.from_worker(FileActionConverter())
        file_action_converter_exit_collect_plugger = Link.from_worker(FileContentFilesContentCollectPlugger())
        exit_aggregator = Node.from_worker(FilesContentAggregator())

        graph.add_node(entry_node)
        graph.add_node(project_action_convert_planner)
        graph.add_node(file_action_converter)
        graph.add_node(exit_aggregator)

        graph.bridge(entry_node, project_action_convert_planner, entry_planner_bridge)
        graph.bridge(project_action_convert_planner, file_action_converter, planner_file_action_converter_dispatch_bridge)
        graph.plug(file_action_converter, exit_aggregator, file_action_converter_exit_collect_plugger)

        graph.set_entry_node(entry_node)
        graph.set_exit_node(exit_aggregator)

        return graph


@autom_registry(is_internal=False)
class AutomProjectActionConverter(GraphAgentWorker):
    @classmethod
    def define_graph(cls) -> AutomGraph:
        graph = AutomGraph()

        entry_node = Node.from_worker(HolderAgentWorker().with_schema(AutomProjectActionConvertParams))
        entry_inner_action_converter_bridge = Link.from_worker(IdentityBridgeWorker())
        inner_action_converter = Node.from_worker(InnerActionConverter())
        inner_action_converter_action_files_dumper_bridge = Link.from_worker(IdentityBridgeWorker())
        action_files_dumper = Node.from_worker(FilesDumper())
        action_files_dumper_ts_export_aggregator_plugger = Link.from_worker(NullPlugger())
        action_files_dumper_exit_plugger = Link.from_worker(FilesContentFilesContentPlugger())

        entry_ts_export_aggregator_plugger = Link.from_worker(ConvertParamsTSExportHelperPlugger())
        ts_export_aggregator = Node.from_worker(TSExportHelperInputAggregator())
        ts_export_aggregator_ts_export_helper_bridge = Link.from_worker(IdentityBridgeWorker())
        ts_export_helper = Node.from_worker(TSExportHerlper())
        ts_export_helper_index_files_dumper_bridge = Link.from_worker(IdentityBridgeWorker())
        index_files_dumper = Node.from_worker(FilesDumper())
        index_files_dumper_exit_plugger = Link.from_worker(FilesContentFilesContentPlugger())
        exit_aggregator = Node.from_worker(FilesContentAggregator())

        graph.add_node(entry_node)
        graph.add_node(inner_action_converter)
        graph.add_node(action_files_dumper)
        graph.add_node(ts_export_aggregator)
        graph.add_node(ts_export_helper)
        graph.add_node(index_files_dumper)
        graph.add_node(exit_aggregator)
        
        graph.bridge(entry_node, inner_action_converter, entry_inner_action_converter_bridge)
        graph.bridge(inner_action_converter, action_files_dumper, inner_action_converter_action_files_dumper_bridge)
        graph.plug(action_files_dumper, exit_aggregator, action_files_dumper_exit_plugger)
        graph.plug(action_files_dumper, ts_export_aggregator, action_files_dumper_ts_export_aggregator_plugger)
        graph.plug(entry_node, ts_export_aggregator, entry_ts_export_aggregator_plugger)
        graph.bridge(ts_export_aggregator, ts_export_helper, ts_export_aggregator_ts_export_helper_bridge)
        graph.bridge(ts_export_helper, index_files_dumper, ts_export_helper_index_files_dumper_bridge)
        graph.plug(index_files_dumper, exit_aggregator, index_files_dumper_exit_plugger)
        
        graph.set_entry_node(entry_node)
        graph.set_exit_node(exit_aggregator)

        return graph


class ConvertParamsTSExportHelperPlugger(PluggerWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return AutomProjectActionConvertParams

    def invoke(self, req: Request) -> Response:
        req_body: AutomProjectActionConvertParams = req.body

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
                            req_body.autom_frontend_root_path / 'actions' / 'backend-api'
                        ],
                    )
                ]
            )
        )


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

        src_api_dir = autom_frontend_root_path / 'lib/backend-api/'
        dst_action_dir = autom_frontend_root_path / 'actions/backend-api/'
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


class PlannerFileActionConverterDispatchBridge(DispatchBridgeWorker):
    @classmethod
    def define_src_schema(cls) -> AutomSchema:
        return ProjectActionConvertPlan

    @classmethod
    def define_dst_schema(cls) -> AutomSchema:
        return FileActionConvertParams

    def dispatch(self, req: Request) -> dict[int, Response]:
        req_body: ProjectActionConvertPlan = req.body
        batch_responses: dict[int, Response[FileActionConvertParams]] = {}
        
        for i, (src_file_fullpath, dst_file_fullpath) in enumerate(req_body.src_dst_filepaths_pair):
            batch_responses[i] = Response[FileActionConvertParams].from_worker(self).success(
                body=FileActionConvertParams(
                    autom_frontend_root_path=req_body.autom_frontend_root_path,
                    api_src_fullpath=src_file_fullpath,
                    action_dst_fullpath=dst_file_fullpath,
                )
            )

        return batch_responses

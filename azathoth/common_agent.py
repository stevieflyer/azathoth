from pathlib import Path

from autom.engine import Request, Response, AggregatorWorker, Socket, PluggerWorker, SocketCall, SocketRequestBody, CollectPluggerWorker
from autom.engine.graph.base import AutomSchema, BatchRequestSchema

from .common_schema import AutomFrontendFileMap


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


class FileMapFileMapPlugger(PluggerWorker):
    @classmethod
    def define_input_schema(cls):
        return AutomFrontendFileMap

    def invoke(self, req: Request) -> Response:
        req_body: AutomFrontendFileMap = req.body
        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(
                calls=[
                    SocketCall(
                        socket_name='update_file_map',
                        data=req_body.autom_frontend_file_content_map,
                    ),
                ]
            )
        )


class FileMapFileMapCollectPlugger(CollectPluggerWorker):
    @classmethod
    def define_src_schema(cls) -> type[AutomSchema]:
        return AutomFrontendFileMap
    
    def invoke(self, req: Request[BatchRequestSchema]) -> Response:
        req_body: BatchRequestSchema[AutomFrontendFileMap] = req.body
        calls = []
        for i, req_item in req_body.batch_requests.items():
            req_item_body: AutomFrontendFileMap = req_item.body
            calls.append(SocketCall(
                socket_name='update_file_map',
                data=req_item_body.autom_frontend_file_content_map,
            ))

        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(
                calls=calls,
            )
        )

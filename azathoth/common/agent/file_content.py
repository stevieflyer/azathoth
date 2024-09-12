from pathlib import Path
from typing import Type

from autom.engine import (
    Request, Response, Socket, SocketCall, SocketRequestBody, BatchRequestSchema,
    AutomSchema, AggregatorWorker, PluggerWorker, CollectPluggerWorker, AgentWorker,
)
from autom.logger import autom_logger

from ..schema import FilesContent, FileContent


class FilesContentAggregator(AggregatorWorker):
    @classmethod
    def define_output_schema(cls):
        return FilesContent

    @classmethod
    def define_socket_list(cls) -> list[Socket]:
        return [
            Socket(
                name='update_file_map',
                input_type=dict,
                socket_handler=cls._update_file_map,
            )
        ]

    def _update_file_map(self, data: dict[Path, str]):
        for key, value in data.items():
            if not isinstance(key, Path) or not isinstance(value, str):
                raise TypeError(f"Expected dict[Path, str], got {type(key)}[{type(value)}]")

        if 'map' not in self._output_as_dict:
            self._output_as_dict['map'] = {}
        self._output_as_dict['map'].update(data)


class FileContentFilesContentPlugger(PluggerWorker):
    @classmethod
    def define_input_schema(cls):
        return FileContent

    def invoke(self, req: Request) -> Response:
        req_body: FileContent = req.body
        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(
                calls=[
                    SocketCall(
                        socket_name='update_file_map',
                        data={req_body.filepath: req_body.content},
                    ),
                ]
            )
        )


class FileContentFilesContentCollectPlugger(CollectPluggerWorker):
    @classmethod
    def define_src_schema(cls) -> type[AutomSchema]:
        return FileContent

    def invoke(self, req: Request[BatchRequestSchema]) -> Response:
        req_body: BatchRequestSchema[FileContent] = req.body
        calls = []
        for i, req_item in req_body.batch_requests.items():
            req_item_body: FileContent = req_item.body
            calls.append(SocketCall(
                socket_name='update_file_map',
                data={req_item_body.filepath: req_item_body.content},
            ))

        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(
                calls=calls,
            )
        )


class FilesContentFilesContentPlugger(PluggerWorker):
    """Plugger to merge multiple FilesContent into one."""
    @classmethod
    def define_input_schema(cls):
        return FilesContent

    def invoke(self, req: Request) -> Response:
        req_body: FilesContent = req.body
        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(
                calls=[
                    SocketCall(
                        socket_name='update_file_map',
                        data=req_body.map,
                    ),
                ]
            )
        )


class FilesContentFilesContentCollectPlugger(CollectPluggerWorker):
    @classmethod
    def define_src_schema(cls) -> type[AutomSchema]:
        return FilesContent

    def invoke(self, req: Request[BatchRequestSchema]) -> Response:
        req_body: BatchRequestSchema[FilesContent] = req.body
        calls = []
        for i, req_item in req_body.batch_requests.items():
            req_item_body: FilesContent= req_item.body
            calls.append(SocketCall(
                socket_name='update_file_map',
                data=req_item_body.map,
            ))

        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(
                calls=calls,
            )
        )


class FileContentAggregator(AggregatorWorker):
    @classmethod
    def define_output_schema(cls) -> AutomSchema | None:
        return FileContent

    @classmethod
    def define_socket_list(cls) -> list[Socket]:
        return [
            Socket(
                name='set_filepath',
                input_type=Path,
                socket_handler=cls._set_filepath,
            ),
            Socket(
                name='set_content',
                input_type=str,
                socket_handler=cls._set_content,
            ),
            Socket(
                name='add_indexed_segment',
                input_type=dict,
                socket_handler=cls._add_indexed_segment,
            )
        ]

    def _set_filepath(self, filepath: Path):
        self._output_as_dict['filepath'] = filepath
        
    def _set_content(self, content: str):
        self._output_as_dict['content'] = content
    
    def _add_indexed_segment(self, data: dict[int, str]):
        if 'indexed_segments' not in self._output_as_dict:
            self._output_as_dict['indexed_segments'] = {}
        self._output_as_dict['indexed_segments'].update(data)

    def build_output_from_dict(self):
        if 'content' in self._output_as_dict:
            return FileContent(
                filepath=self._output_as_dict['filepath'],
                content=self._output_as_dict['content'],
            )
        # Merge indexed segments into content with separator '\n\n'
        content = '\n\n'.join([self._output_as_dict['indexed_segments'][i] for i in sorted(self._output_as_dict['indexed_segments'])])
        
        autom_logger.info(f"FileContentAggregator: Merged indexed segments into content, filepath={self._output_as_dict['filepath']}, segments={self._output_as_dict['indexed_segments']}")
        return FileContent(
            filepath=self._output_as_dict['filepath'],
            content=content,
        )


class FilesDumper(AgentWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return FilesContent

    @classmethod
    def define_output_schema(cls) -> AutomSchema | None:
        return FilesContent
    
    def invoke(self, req: Request) -> Response:
        req_body: FilesContent = req.body
        try:
            req_body.dump_to_disk()
        except Exception as e:
            autom_logger.error(f"Failed to dump FilesContent to disk: {e}.")
            raise e
        return Response[FilesContent].from_worker(self).success(
            body=req_body
        )


__all__ = [
    'FilesContentAggregator',
    'FilesContentFilesContentPlugger',
    'FilesContentFilesContentCollectPlugger',
    'FileContentFilesContentPlugger',
    'FileContentFilesContentCollectPlugger',
    'FileContentAggregator',
    'FilesDumper',
]

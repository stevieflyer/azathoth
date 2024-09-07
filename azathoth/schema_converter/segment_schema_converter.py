from autom.utils import SingleLLMUsage
from autom.official import BaseOpenAIWorker
from autom.engine import Request, Response, AgentWorker

from .prompt import *
from .schema import *


# Segment Schema Converter, File Segmenter
class SegmentSchemaConverter(BaseOpenAIWorker, AgentWorker):
    @classmethod
    def define_input_schema(cls):
        return SegmentSchemaConverterInput

    @classmethod
    def define_output_schema(cls):
        return SegmentSchemaConverterOutput

    def invoke(self, req: Request) -> Response:
        from pydantic import BaseModel
        class ConvertOutput(BaseModel):
            """internal class for openai structured response"""
            converted_segment: str

        req_body: SegmentSchemaConverterInput = req.body
        resp = Response[SegmentSchemaConverterOutput].from_worker(self)
        if req_body.src_repo_enum == RepoEnum.BACKEND:
            chat_completion = self.openai_client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": backend_system_prompt},
                    {"role": "user", "content": user_input_promt.format(src_file_relpath=req_body.src_file_relpath.as_posix(), code_segment=req_body.segment)},
                ],
                response_format=ConvertOutput,
            )
            resp.add_llm_usage(SingleLLMUsage.from_openai_chat_completion(chat_completion))
            resp.body = SegmentSchemaConverterOutput(
                src_repo_enum=req_body.src_repo_enum,
                src_repo_root=req_body.src_repo_root,
                src_file_relpath=req_body.src_file_relpath,
                dst_repo_enum=req_body.dst_repo_enum,
                dst_repo_root=req_body.dst_repo_root,
                dst_file_relpath=req_body.dst_file_relpath,
                converted_segment=chat_completion.choices[0].message.parsed.converted_segment,
            )
        else:
            raise NotImplementedError

        return resp


__all__ = [
    'SegmentSchemaConverter',
]

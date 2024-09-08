from autom.utils import SingleLLMUsage
from autom.official import BaseOpenAIWorker
from autom.engine import AgentWorker, AutomSchema, Request, Response

from .prompt import *
from .schema import *


class FunctionAPIConverter(BaseOpenAIWorker, AgentWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return FunctionAPIConverterInput
    
    @classmethod
    def define_output_schema(cls) -> AutomSchema | None:
        return FunctionAPIConverterOutput

    def invoke(self, req: Request) -> Response:
        from pydantic import BaseModel
        class Output(BaseModel):
            frontend_code: str

        req_body: FunctionAPIConverterInput = req.body
        api_function_source = req_body.api_function_source

        resp = Response[FunctionAPIConverterOutput].from_worker(self)
        chat_completion = self.openai_client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": api_convert_prompt},
                    {"role": "user", "content": user_input_prompt.format(
                        src_filepath=req_body.src_file_fullpath.as_posix(),
                        api_function_source=api_function_source,
                        dst_filepath=req_body.dst_file_fullpath.as_posix(),
                    )},
                ],
                response_format=Output,
            )
        resp.add_llm_usage(SingleLLMUsage.from_openai_chat_completion(chat_completion))
        resp.body = FunctionAPIConverterOutput(
            api_function_source=req_body.api_function_source,
            src_file_fullpath=req_body.src_file_fullpath,
            dst_file_fullpath=req_body.dst_file_fullpath,
            autom_backend_root_path=req_body.autom_backend_root_path,
            autom_frontend_root_path=req_body.autom_frontend_root_path,
            frontend_api_source=chat_completion.choices[0].message.parsed.frontend_code,
        )
        return resp.success()

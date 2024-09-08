from autom.utils import SingleLLMUsage
from autom.official import BaseOpenAIWorker
from autom.engine import AgentWorker, AutomSchema, Request, Response

from .prompt import *
from .schema import *


class FileActionConverter(BaseOpenAIWorker, AgentWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return FileActionConverterInput

    @classmethod
    def define_output_schema(cls) -> AutomSchema | None:
        return FileActionConverterOutput

    def invoke(self, req: Request) -> Response:
        from pydantic import BaseModel
        class Output(BaseModel):
            server_action_code: str

        req_body: FileActionConverterInput = req.body
        with open(req_body.api_src_fullpath, 'r') as f:
            api_source = f.read()

        resp = Response[FileActionConverterOutput].from_worker(self)
        chat_completion = self.openai_client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": api_convert_prompt},
                    {"role": "user", "content": user_input_prompt.format(
                        api_source=api_source
                    )},
                ],
                response_format=Output,
            )
        resp.add_llm_usage(SingleLLMUsage.from_openai_chat_completion(chat_completion))
        resp.body = FileActionConverterOutput(
            autom_frontend_root_path=req_body.autom_frontend_root_path,
            api_src_fullpath=req_body.api_src_fullpath,
            action_dst_fullpath=req_body.action_dst_fullpath,
            action_dst_content=chat_completion.choices[0].message.parsed.server_action_code,
        )
        return resp.success()

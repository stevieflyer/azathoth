from autom.utils import SingleLLMUsage
from autom.official import BaseOpenAIWorker
from autom.engine import AgentWorker, AutomSchema, Request, Response

from azathoth.common import FileContent
from .schema import FileActionConvertParams
from .prompt import api_convert_system_prompt, api_convert_user_input_prompt


class FileActionConverter(BaseOpenAIWorker, AgentWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return FileActionConvertParams

    @classmethod
    def define_output_schema(cls) -> AutomSchema | None:
        return FileContent

    def invoke(self, req: Request) -> Response:
        from pydantic import BaseModel
        class Output(BaseModel):
            server_action_code: str

        req_body: FileActionConvertParams = req.body
        with open(req_body.api_src_fullpath, 'r') as f:
            api_source = f.read()

        resp = Response[FileContent].from_worker(self)
        chat_completion = self.openai_client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": api_convert_system_prompt},
                    {"role": "user", "content": api_convert_user_input_prompt.format(
                        api_source=api_source
                    )},
                ],
                response_format=Output,
            )
        resp.add_llm_usage(SingleLLMUsage.from_openai_chat_completion(chat_completion))
        resp.body = FileContent(
            filepath=req_body.action_dst_fullpath,
            content=chat_completion.choices[0].message.parsed.server_action_code,
        )
        return resp.success()


__all__ = [
    'FileActionConverter',
]

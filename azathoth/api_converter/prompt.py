function_api_converter_system_prompt = '''
请你协助我将我把我的后端项目（基于 Python FastAPI) 的 api 函数转换为前端项目（基于 TypeScript React) 的 api 函数。

我将先给你一些示例:

【例子 1】
【【输入】】
<src_filepath>
/home/john/workspace/future-school/app/api/v1/endpoints/classes.py
<api_function_source>
@router.get(
    "/{{class_id}}/current-representitives/{{representitive_id}}",
    response_model=ClassRepresentitiveDetail,
    tags=["class-representitive"],
)
def get_class_detail_representitive_by_id(
    representitive_id: int,
    body_data: PaginationQueryReqBody,
    db: Session = Depends(get_db),
    current_user: UserSafe = Depends(get_current_user),
):
    pass
<dst_filepath>
/home/john/workspace/future-school/lib/backend-api/classes/get_class_detail_representitive_by_id.ts
【【输出】】
import {{ cache }} from "react";

import {{ UnexpectedError }} from "@/errors";
import {{ BACKEND_API_URL }} from "../config";
import {{ ClassRepresentitiveDetail, PaginationQueryReqBody }} from "@/types";

/**
 * Get class representative detail by ID
 *
 * @param classId - The ID of the class.
 * @param representitiveId - The ID of the class representative.
 * @param accessToken - The access token for authentication.
 * @throws {{UnexpectedError}} If an unexpected error occurs.
 *
 * @returns {{Promise<ClassRepresentitiveDetail>}} The representative detail data for the class.
 */
export const getClassDetailRepresentitiveById = cache(
  async ({{
    classId,
    representitiveId,
    bodyData,
    accessToken,
  }}: {{
    classId: number;
    representitiveId: number;
    bodyData: PaginationQueryReqBody;
    accessToken: string;
  }}): Promise<ClassRepresentitiveDetail> => {{
    const response = await fetch(
      `${{BACKEND_API_URL}}/${{classId}}/current-representitives/${{representitiveId}}`,
      {{
        method: "GET",
        headers: {{
          Authorization: `Bearer ${{accessToken}}`,
        }},
        body: JSON.stringify(bodyData),
      }}
    );

    if (!response.ok) {{
      throw new UnexpectedError(
        `An unexpected error occurred. Error: ${{response.statusText}}`
      );
    }}

    return await response.json();
  }}
);
【例子 1 结束】

下面，轮到你了！请注意, 跟例子中唯一不同的一点要求是：我需要你以 json 的形式返回， 格式类似: {{ "frontend_code": "..." }}。

我再次重申你的工作职责：请你协助我将我把我的后端项目（基于 Python FastAPI) 的 api 函数转换为前端项目（基于 TypeScript React) 的 api 函数。

你应该从例子中已经知道了一些我要你完成这项工作的特别注意事项：
- 从输入信息中你可以看到, 你在输入中会知道: api_function_source, src_filepath, dst_filepath.
  - 你可以从 api_function_source 中得知: (1) $api_suffix_route (2) $api_function_name E.g.在例子 1 中, 从函数的 decorator 中你可以看到 $api_suffix_route 为 "/{{class_id}}/current-representitives/{{representitive_id}}", 从函数名中可以看到 $api_function_name 为 "get_my_worker_by_id"
  - 你可以从 dst_file_name 中得知: $router_name, 和 $api_endpoint_name, 因为 dst_file_name 的路径规范总是: `lib/backend-api/{{router_tag}}/{{api_function_name}}.ts`, 而 $router_name=$router_tag.replace("_", "-"). 例如: 如果 dst_file_name 为 `lib/backend-api/group_ticket/delete_ticket.ts`, 那么 $router_name 为 "group-ticket", $api_endpoint_name 为 "delete_ticket"

- 你输出的代码中要访问的 api url 永远不应该含有下划线 `_`, 应当使用 `-` 代替 `_`, 且与这个模式相一致: `${{BACKEND_API_URL}}/{{router_name}}/${{api_suffix_route}}`

- 如果 api_function_source 中含有 current_user: UserSafe = Depends(get_current_user), 你应当在输出的代码中添加一个 accessToken 参数，用于传递用户的 access token, 否则就不需要

- 对于 body_data, 如果后端代码中有 body_data, 那么前端代码中也应当有 bodyData, 并且类型直接指定为与后端同名的类即可, 你可以认为这个类可以从 @/types 中 import 到

- 如果后端代码中没有传递 body_data, 那么前端代码中也一定不要有 bodyData 参数

- 在编写 ts 代码时, 对于参数, 请始终使用 destructuring 的方式。哪怕只有一个参数, 也应当坚持使用 destructuring 的方式。例如: {{ classId }}: {{ classId: number }}。

- 但是如果没有任何参数(比如只需要传递 accessToken), 那么就不需要使用 destructuring 的方式, 因为一个全空的对象解构是令人疑惑且不符合语法的。

- 对于所有需要用到的 schema, 你都认为可以从 "@/types" 中 import
'''.strip()

function_api_converter_user_input_prompt = """
【输入】
<src_filepath>
{src_filepath}

<api_function_source>
{api_function_source}

<dst_filepath>
{dst_filepath}

【输出】
""".strip()

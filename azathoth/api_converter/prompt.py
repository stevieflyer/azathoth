function_api_converter_system_prompt = '''
请你协助我将我把我的后端项目（基于 Python FastAPI) 的 api 函数转换为前端项目（基于 TypeScript React) 的 api 函数。

我将先给你一些示例:

【例子 1】
【【输入】】
<src_filepath>
/home/steve/workspace/autom-backend/app/api/v1/endpoints/project.py

<api_function_source>
@router.post(
    "/create-from-dashboard",
    response_model=AutomProjectWithOwnerAndStatus,
)
async def create_project_from_dashboard(
    body_data: CreateFromDashboardReqBody,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserSafe = Depends(get_current_user),
):
    pass

<dst_filepath>
/home/steve/workspace/autom-frontend/lib/backend_api/project/create-from-dashboard.ts
【【输出】】
import {{ cache }} from "react";

import {{ UnexpectedError }} from "@/errors";
import {{ BACKEND_API_URL }} from "../config";
import {{ CreateFromDashboardReqBody, AutomProjectWithOwnerAndStatus }} from "@/types";

/**
 * Create a new autom project from dashboard
 *
 * @throws {{UnexpectedError}} If an unexpected error occurs.
 *
 * @returns {{Promise<AutomProjectWithOwnerAndStatus>}} The successfully created project.
 */
export const createProjectFromDashboard = cache(
  async ({{
    accessToken,
    data,
  }}: {{
    accessToken: string;
    data: CreateFromDashboardReqBody;
  }}): Promise<AutomProjectWithOwnerAndStatus> => {{
    const response = await fetch(`${{BACKEND_API_URL}}/project/create-from-dashboard`, {{
      method: "POST",
      headers: {{
        "Content-Type": "application/json",
        Authorization: `Bearer ${{accessToken}}`,
      }},
      body: JSON.stringify(data),
    }});

    if (!response.ok) {{
      throw new UnexpectedError(`An unexpected error occurred. Error: ${{response.statusText}}`);
    }}

    return await response.json();
  }}
);
【例子 1 结束】

下面，轮到你了！请注意, 跟例子中唯一不同的一点要求是：我需要你以 json 的形式返回， 格式类似: {{ "frontend_code": "..." }}。

我再次重申你的工作职责：请你协助我将我把我的后端项目（基于 Python FastAPI) 的 api 函数转换为前端项目（基于 TypeScript React) 的 api 函数。

你应该从例子中已经知道了一些我要你完成这项工作的特别注意事项：
- 从输入信息中你可以看到, 你在输入中会知道: api_function_source, src_filepath, dst_filepath.
- 你可以从 api_function_source 中得知: $api_suffix_route, $api_function_name 比如在例子 1 中, 从函数的 decorator 中你可以看到 $api_suffix_route 为 "/create-from-dashboard", 从函数名中可以看到 $api_function_name 为 "create_project_from_dashboard"
- 你可以从 dst_file_name 中得知: $router_name, 和 $api_endpoint_name. 因为 dst_file_name 的路径规范总是: lib/backend_api/{{router_name}}/{{api_function_name}}.ts
- 你输出的代码中要访问的 api url 应当为: `${{BACKEND_API_URL}}/{{router_name}}/${{api_suffix_route}}`
- 如果 api_function_source 中含有 current_user: UserSafe = Depends(get_current_user), 你应当在输出的代码中添加一个 accessToken 参数，用于传递用户的 access token, 否则就不需要
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

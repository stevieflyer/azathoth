function_api_converter_system_prompt = '''
请你帮我把 Python FastAPI 后端项目中的一个 api 函数转换为前端 TypeScript React 项目的一个 api 函数, 以便我在前端项目中使用。

你总是会获得以下信息:
- api_function_source: 一个 Python FastAPI 后端项目中的一个 api 函数的函数头部
- router_name: 这个 api 函数所在的 router 的名字

我给你一个例子:
# 例子 1

## 输入
<api_function_source>
@router.post("/login/cred", response_model=LoginRespBody)
def cred_login(
    body_data: CredLoginReqBody,
    db: Session = Depends(get_db),
) -> LoginRespBody:
<router_name>
users
## 输出
"use server";

import {{ cache }} from "react";

import {{ BACKEND_API_URL }} from "@/config";
import {{ CredLoginReqBody, LoginRespBody }} from "@/types";

export const credLogin = cache(
  async ({{
    bodyData,
  }}: {{
    bodyData: CredLoginReqBody;
  }}): Promise<LoginRespBody> => {{
    const response = await fetch(`${{BACKEND_API_URL}}/users/login/cred`, {{
      method: "POST",
      headers: {{
        "Content-Type": "application/json",
      }},
      body: JSON.stringify(bodyData),
    }});

    if (!response.ok) {{
      const errorData = await response.json();
      throw new Error(errorData?.detail);
    }}

    return await response.json();
  }}
);
# 例子 1 结束

除了例子, 我还有一些特别注意事项, 请你务必注意:
- 前端代码要请求的 url 始终是: `${{BACKEND_API_URL}}/{{router_name}}/${{api_suffix_route}}`, 这里的 api_suffix_route 是你在后端代码中的 api 函数的路由后缀
- 如果 api_function_source 中含有参数 current_user: UserSafe = Depends(get_current_user), 你应当在输出的代码中添加一个 accessToken 参数，并且在 fetch 请求的 headers 中添加一个 Authorization 字段，值为 `Bearer ${{accessToken}}`
- 如果 api_function_source 中不含有 current_user 参数, 那么意味着这个接口不需要登录, 你的输出代码就不需要添加 accessToken 参数, 也不需要在 fetch 请求的 headers 中添加 Authorization 字段
- 前端代码的变量名应当尽量与后端代码一致, 但是请将所有的变量名都改为 camelCase 的形式
- 如果后端代码中没有参数 body_data, 那么前端代码中也一定不要有 bodyData 参数, 也不要在 fetch 请求加入 body 字段
- 在前端代码中请始终使用 destructuring 的方式来接收参数, 即使只有一个参数
- 但是如果没有任何参数(比如只需要传递 accessToken), 那么就不需要使用 destructuring 的方式, 因为一个全空的对象解构是令人疑惑且不符合语法的。
- 对于所有遇到的 schema, 你都可以放心地从 "@/types" 中 import, 这里一定会有你需要的类型定义, 名称与后端完全相同
'''.strip()

function_api_converter_user_input_prompt = """
【输入】
<api_function_source>
{api_function_source}

<router_name>
{router_name}

【输出】
""".strip()

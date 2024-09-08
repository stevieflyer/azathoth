api_convert_prompt = '''
请你协助我将我把我的前端项目（基于 TypeScript NextJS) 的 backend api 文件调用转换为 server actions 文件。

我将先给你一些示例:

【例子 1】
【【输入】】
<api_source>
import {{ cache }} from "react";
import {{ UnexpectedError }} from "@/errors";
import {{ BACKEND_API_URL }} from "../config";
import {{ BIntegrationAuthMetaBriefWithStatus, PaginatedSearchResult }} from "@/types";

/**
 * Fetches the list of integrations with pagination.
 *
 * @throws {{UnexpectedError}} If an unexpected error occurs.
 *
 * @returns {{Promise<PaginatedSearchResult<BIntegrationAuthMetaBriefWithStatus>>}} The paginated result of integrations.
 */
export const getIntegrationAuths = cache(
  async ({{
    accessToken,
    limit = 10,
    offset = 0,
  }}: {{
    accessToken: string;
    limit?: number;
    offset?: number;
  }}): Promise<PaginatedSearchResult<BIntegrationAuthMetaBriefWithStatus>> => {{
    // some implementation
  }}
);
【【输出】】
"use server";

import {{ getIntegrationAuths }} from "@/lib/backend_api";
import {{ getAccessTokenAction }} from "@/app/(root)/_actions/token";

export const getIntegrationAuthsAction = async ({{ limit = 20, offset = 0 }}: {{ limit?: number; offset?: number }}) => {{
  const accessToken = await getAccessTokenAction();
  if (!accessToken) throw new Error("Not Authenticated");
  const result = await getIntegrationAuths({{
    accessToken,
    limit,
    offset,
  }});
  return result;
}};
【例子 1 结束】

下面，轮到你了！请注意, 跟例子中唯一不同的一点要求是：我需要你以 json 的形式返回， 格式类似: {{ "server_action_code": "..." }}。

我再次重申你的工作职责：请你协助我将我把我的前端项目（基于 TypeScript NextJS) 的 backend api 文件调用转换为 server actions 文件。

你应该从例子中已经知道了一些我要你完成这项工作的特别注意事项：
- 生成的代码中应当包含 "use server" 的声明
- 你只需要关注输入的 api_source 中的函数头, 函数体跟 server action 的生成没有关系
- 如果输入的 api_source 中含有 accessToken 参数, 那么输出的代码中你应当像例子中那样尝试 getAccessTokenAction, 并且在调用 api 函数时传递 accessToken 参数; 否则就不需要 accessToken 相关逻辑。
- 如果 api_source 中的调用参数类型涉及到自定义类型, 那么请确保你的输出代码中也包含相应的 types 引用（都从 @/types 引入）, 但是返回类型以及其它函数中用到的自定义类型, 我们是不需要引入的(正如例子1中我们不需要引入任何自定义类型)。
- 你永远可以认为 api 函数可以从 "@/lib/backend_api" 中引入, 而且你永远可以认为 getAccessTokenAction 可以从 "@/app/(root)/_actions/token" 中引入。
'''.strip()

user_input_prompt = """
【输入】
<api_source>
{api_source}

【输出】
""".strip()

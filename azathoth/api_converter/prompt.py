function_api_converter_system_prompt = '''
请你帮我从 Python FastAPI 后端项目中的一个 api 函数提取如下信息:

Rule 1: api_suffix_route: 从函数的路由路径中提取, 必须以 `/` 开头
Rule 2: has_response_model: 如果函数有 `response_model`，则为 `True`，否则为 `False`
Rule 3: response_model: 如果有 `response_model`，提供对应的类型名称；否则为 `None`
Rule 4: has_body_data: 如果函数有名为 `body_data` 的参数，则为 `True`，否则为 `False`
Rule 5: body_data_type: 如果有 `body_data` 参数，提供对应的类型名称；否则为 `None`
Rule 6: has_current_user: 如果函数中包含 `current_user: UserSafe = Depends(get_current_user)` 这样的参数，则为 `true`，否则为 `false`
Rule 7: otherParams: 从函数中提取的其他参数，且应符合类型要求（`string`、`number`、`boolean`), 其它参数就是指函数参数中除了 db, body_data, 和 current_user 之外的参数

要求就是这些, 请你认真仔细严谨地提取信息吧.
'''

function_api_converter_user_input_prompt = """
【输入】
<api_function_source>
{api_function_source}
【输出】
""".strip()

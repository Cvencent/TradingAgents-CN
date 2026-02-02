# Chat（工具调用）

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /v1/chat/completions:
    post:
      summary: Chat（工具调用）
      deprecated: false
      description: >-
        302平台为所有模型增加了工具调用能力（俗称Function Call）

        原理是：如果模型本身不支持工具调用，只需要传入tools参数，302后台会自动将参数解析，并且改造为提示词传给模型，并改造模型输出为tool_call格式

        可根据tool-use-mode来选择工具调用模式

        1：自动模式：原生支持工具调用的就走原生，不支持的就走提示词模式

        2：原生模式：强制走模型模式

        3：提示词模式： 强制走提示词模式


        注意：此模式会导致流式失效


        **价格：原有模型费用不变**
      tags:
        - 语言大模型/独家功能/工具调用
      parameters:
        - name: Content-Type
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
        - name: Accept
          in: header
          description: ''
          required: true
          example: application/json
          schema:
            type: string
        - name: Authorization
          in: header
          description: 将管理后台-API KEYS里生成的API KEY填在Bearer后面，比如Bearer sk-xxxx
          required: true
          example: Bearer {{YOUR_API_KEY}}
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                model:
                  type: string
                  description: >-
                    要使用的模型的 ID。有关哪些模型适用于聊天 API
                    的详细信息，请参阅[模型端点兼容性表。](https://platform.openai.com/docs/models/model-endpoint-compatibility)
                messages:
                  type: array
                  items:
                    type: object
                    properties:
                      role:
                        type: string
                      content:
                        type: string
                    x-apifox-orders:
                      - role
                      - content
                  description: >-
                    以[聊天格式](https://platform.openai.com/docs/guides/chat/introduction)生成聊天完成的消息。
                temperature:
                  type: integer
                  description: >-
                    使用什么采样温度，介于 0 和 2 之间。较高的值（如 0.8）将使输出更加随机，而较低的值（如
                    0.2）将使输出更加集中和确定。  我们通常建议改变这个或`top_p`但不是两者。
                top_p:
                  type: integer
                  description: >-
                    一种替代温度采样的方法，称为核采样，其中模型考虑具有 top_p 概率质量的标记的结果。所以 0.1 意味着只考虑构成前
                    10% 概率质量的标记。  我们通常建议改变这个或`temperature`但不是两者。
                'n':
                  type: integer
                  description: 为每个输入消息生成多少个聊天完成选项。
                stream:
                  type: boolean
                  description: >-
                    如果设置，将发送部分消息增量，就像在 ChatGPT
                    中一样。当令牌可用时，令牌将作为纯数据[服务器发送事件](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#Event_stream_format)`data:
                    [DONE]`发送，流由消息终止。[有关示例代码](https://github.com/openai/openai-cookbook/blob/main/examples/How_to_stream_completions.ipynb)，请参阅
                    OpenAI Cookbook 。
                stop:
                  type: string
                  description: API 将停止生成更多令牌的最多 4 个序列。
                max_tokens:
                  type: integer
                  description: 聊天完成时生成的最大令牌数。  输入标记和生成标记的总长度受模型上下文长度的限制。
                presence_penalty:
                  type: number
                  description: >-
                    -2.0 和 2.0 之间的数字。正值会根据到目前为止是否出现在文本中来惩罚新标记，从而增加模型谈论新主题的可能性。 
                    [查看有关频率和存在惩罚的更多信息。](https://platform.openai.com/docs/api-reference/parameter-details)
                frequency_penalty:
                  type: number
                  description: >-
                    -2.0 和 2.0 之间的数字。正值会根据新标记在文本中的现有频率对其进行惩罚，从而降低模型逐字重复同一行的可能性。 
                    [查看有关频率和存在惩罚的更多信息。](https://platform.openai.com/docs/api-reference/parameter-details)
                logit_bias:
                  type: 'null'
                  description: >-
                    修改指定标记出现在完成中的可能性。  接受一个 json 对象，该对象将标记（由标记器中的标记 ID 指定）映射到从
                    -100 到 100 的关联偏差值。从数学上讲，偏差会在采样之前添加到模型生成的 logits
                    中。确切的效果因模型而异，但 -1 和 1 之间的值应该会减少或增加选择的可能性；像 -100 或 100
                    这样的值应该导致相关令牌的禁止或独占选择。
                user:
                  type: string
                  description: >-
                    代表您的最终用户的唯一标识符，可以帮助 OpenAI
                    监控和检测滥用行为。[了解更多](https://platform.openai.com/docs/guides/safety-best-practices/end-user-ids)。
              required:
                - model
                - messages
              x-apifox-orders:
                - model
                - messages
                - temperature
                - top_p
                - 'n'
                - stream
                - stop
                - max_tokens
                - presence_penalty
                - frequency_penalty
                - logit_bias
                - user
            example:
              model: o1-mini
              messages:
                - role: user
                  content: What's the weather like in Boston today?
              tools:
                - type: function
                  function:
                    name: get_current_weather
                    description: Get the current weather in a given location
                    parameters:
                      type: object
                      properties:
                        location:
                          type: string
                          description: The city and state, e.g. San Francisco, CA
                        unit:
                          type: string
                          enum:
                            - celsius
                            - fahrenheit
                      required:
                        - location
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  choices:
                    type: array
                    items:
                      type: object
                      properties:
                        finish_reason:
                          type: string
                        index:
                          type: integer
                        message:
                          type: object
                          properties:
                            content:
                              type: string
                            role:
                              type: string
                          required:
                            - content
                            - role
                  created:
                    type: integer
                  id:
                    type: string
                  model:
                    type: string
                  object:
                    type: string
                  usage:
                    type: object
                    properties:
                      completion_tokens:
                        type: integer
                      completion_tokens_details:
                        type: object
                        properties:
                          content_tokens:
                            type: integer
                        required:
                          - content_tokens
                      prompt_tokens:
                        type: integer
                      prompt_tokens_details:
                        type: object
                        properties:
                          text_tokens:
                            type: integer
                        required:
                          - text_tokens
                      total_tokens:
                        type: integer
                    required:
                      - completion_tokens
                      - completion_tokens_details
                      - prompt_tokens
                      - prompt_tokens_details
                      - total_tokens
                required:
                  - choices
                  - created
                  - id
                  - model
                  - object
                  - usage
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 语言大模型/独家功能/工具调用
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/4012774/apis/api-278559236-run
components:
  schemas: {}
  securitySchemes:
    apiKeyAuth:
      type: apikey
      in: header
      name: Authorization
    BearerAuth:
      type: jwt
      scheme: bearer
      bearerFormat: JWT
      description: |
        请输入您的 API Key。格式为：`Bearer YOUR_API_KEY`。
servers:
  - url: https://api.302.ai
    description: 正式环境
  - url: https://api.302ai.cn
    description: 国内中转
security: []

```
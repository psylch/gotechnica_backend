下面是一份“最简可用”的 Dify Advanced Chat API 使用文档（Python）。同时满足“文字 + 图片（URL）输入”，并分别给出单轮与多轮对话的清晰示例。直接可运行，便于快速测试。

安全提示

- 请把 API Key 存在服务端（环境变量或安全配置），不要在前端暴露。

1. 单轮对话：文字 + 图片（URL）输入

# filename: single_turn.py

import os

import requests

API_BASE = "https://api.dify.ai/v1"

API_KEY = os.environ.get("DIFY_API_KEY")  # 从环境变量读取，避免泄露

assert API_KEY, "Please set environment variable DIFY_API_KEY"

def send_single_turn(query: str, image_url: str, user_id: str = "test-user-001"):

    """

    使用 blocking 模式进行单轮对话，并同时传入文字与图片 URL。

    若需要流式输出，可把 response_mode 改为 'streaming' 并按 SSE 处理。

    """

    url = f"{API_BASE}/chat-messages"

    headers = {

        "Authorization": f"Bearer {API_KEY}",

        "Content-Type": "application/json",

    }

    payload = {

        "inputs": {},                 # 可按你的 App 变量需求填充

        "query": query,               # 文本问题

        "response_mode": "blocking",  # 简明起见用 blocking，直接拿完整结果

        "conversation_id": "",        # 单轮对话不传旧会话ID

        "user": user_id,

        "files": [

            {

                "type": "image",

                "transfer_method": "remote_url",

                "url": image_url

            }

        ],

        "auto_generate_name": True

    }

    resp = requests.post(url, headers=headers, json=payload, timeout=60)

    resp.raise_for_status()

    data = resp.json()

    # 关键字段：answer / conversation_id / message_id / metadata.usage

    return {

        "answer": data.get("answer", ""),

        "conversation_id": data.get("conversation_id", ""),

        "message_id": data.get("message_id", ""),

        "usage": data.get("metadata", {}).get("usage", {})

    }

if __name__ == "__main__":

    result = send_single_turn(

        query="这张图片里是什么？并结合文字一起说明",

        image_url="https://cloud.dify.ai/logo/logo-site.png"

    )

    print("Answer:", result["answer"])

    print("Conversation ID:", result["conversation_id"])

    print("Message ID:", result["message_id"])

    print("Usage:", result["usage"])

2. 多轮对话：在同一 conversation_id 下继续交流（文字 + 图片 URL 均可）

# filename: multi_turn.py

import os

import requests

API_BASE = "https://api.dify.ai/v1"

API_KEY = os.environ.get("DIFY_API_KEY")

assert API_KEY, "Please set environment variable DIFY_API_KEY"

HEADERS = {

    "Authorization": f"Bearer {API_KEY}",

    "Content-Type": "application/json",

}

def send_message(query: str, user_id: str, conversation_id: str = "", image_url: str | None = None):

    """

    发送一条消息到 Dify：

    - 支持继续会话（传入 conversation_id）

    - 可选附带图片 URL

    - 使用 blocking 模式方便拿到完整结果

    返回 answer / conversation_id / message_id

    """

    payload = {

        "inputs": {},

        "query": query,

        "response_mode": "blocking",

        "conversation_id": conversation_id,  # 为空表示新对话；非空表示继续该会话

        "user": user_id,

        "auto_generate_name": True

    }

    if image_url:

        payload["files"] = [{

            "type": "image",

            "transfer_method": "remote_url",

            "url": image_url

        }]

    resp = requests.post(f"{API_BASE}/chat-messages", headers=HEADERS, json=payload, timeout=60)

    resp.raise_for_status()

    data = resp.json()

    return {

        "answer": data.get("answer", ""),

        "conversation_id": data.get("conversation_id", ""),

        "message_id": data.get("message_id", "")

    }

def get_history(conversation_id: str, user_id: str):

    """

    拉取该会话的历史消息（倒序滚动）。

    """

    resp = requests.get(

        f"{API_BASE}/messages",

        headers=HEADERS,

        params={"user": user_id, "conversation_id": conversation_id},

        timeout=30

    )

    resp.raise_for_status()

    return resp.json()

if __name__ == "__main__":

    user_id = "test-user-002"

    # 第一轮：新建会话 + 图片 URL

    first = send_message(

        query="请根据这张图片，生成一个简短描述，并回答：这属于哪类图标风格？",

        user_id=user_id,

        conversation_id="",

        image_url="https://cloud.dify.ai/logo/logo-site.png"

    )

    print("[Turn 1] Answer:", first["answer"])

    cid = first["conversation_id"]

    print("Conversation ID:", cid)

    # 第二轮：继续会话，仅文字输入

    second = send_message(

        query="好的，基于上一轮的回答，再补充两点设计建议。",

        user_id=user_id,

        conversation_id=cid

    )

    print("[Turn 2] Answer:", second["answer"])

    # 拉取历史记录（可选）

    history = get_history(conversation_id=cid, user_id=user_id)

    print("[History] has_more:", history.get("has_more"))

    for msg in history.get("data", []):

        print(f"- [{msg.get('created_at')}] Q: {msg.get('query')}")

        print(f"  A: {msg.get('answer')}\n")

进阶补充（可选）

- 如果你需要中途“打断”流式生成：先把 response_mode 改为 ‎⁠streaming⁠，从 SSE 中取到 ‎⁠task_id⁠，然后调用 Stop Generate 接口。

- 如果要上传本地文件再引用图片：先调用 ‎⁠/files/upload⁠ 拿 ‎⁠id⁠，然后把 ‎⁠files⁠ 改为 ‎⁠{"type":"image","transfer_method":"local_file","upload_file_id":"..."}⁠

- 变量与工作流版本：如需指定 ‎⁠workflow_id⁠ 或在 ‎⁠inputs⁠ 里传 App 自定义变量，按你的应用配置传入即可。

- 成本用量：从响应的 ‎⁠metadata.usage⁠ 获取 token 与价格估算，便于监控。

假设与说明

- 默认使用 blocking 模式，便于最小示例拿到完整 answer。

- 图片使用官方文档中的公开 URL 作为示例。

- user 字段示例为 test-user-00X，可替换为你系统中的真实用户标识。
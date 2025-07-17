import os

from xai_sdk import Client
from xai_sdk.chat import user
from xai_sdk.search import SearchParameters, x_source, news_source, web_source

client = Client(api_key=os.getenv("GROK_API_KEY"))
chat = client.chat.create(
    # model="grok-3-mini",
    model="grok-4",
    search_parameters=SearchParameters(
        mode="auto",
        sources=[
            x_source(included_x_handles=[]),
            web_source(),
            news_source(),
        ],
    ),
)
# chat.append(user("今日の日本のTwitterトレンドを調べてください。web検索やXを活用してしらべてください。"))

response = chat.sample()
print(response.content)
print(response.citations)
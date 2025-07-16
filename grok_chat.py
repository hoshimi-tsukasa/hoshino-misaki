
import os
from groq import Groq

# Geminiの例と同じ詳細なペルソナを定義
persona_instructions = """
# 役割
あなたは、15年以上の経験を持つシニアソフトウェアエンジニアです。
コードレビューやジュニア開発者の指導が主な役割です。

# 口調とトーン
- 基本的に少し皮肉屋で、ユーモアを交えながら話します。
- しかし、最終的には非常に協力的で、相手が理解できるまで根気強く付き合います。
- 簡潔で、要点を突いた話し方をします。無駄な美辞麗句は使いません。

# 応答形式
- コードの問題点を指摘する際は、必ず「良い点」を1つ挙げてから「改善点」を提示してください。
- 改善案を示す際は、具体的なコードスニペットを提示します。
- 応答の最後には、必ず「他に質問は？（Any other questions?）」と付け加えてください。

# 制約とルール
- 答えをそのまま教えるのではなく、相手に考えさせるようなヒントを与えてください。
- 専門用語を使う際は、簡単な注釈を添えてください。
- 質問が曖昧な場合は、「もう少し具体的に教えてくれる？（Can you be more specific?）」と返してください。
"""

# Grok APIキーを環境変数から取得
api_key = os.environ.get("GROK_API_KEY")

if not api_key:
    print("エラー: 環境変数 `GROK_API_KEY` が設定されていません。")
    exit()

# Grokクライアントの初期化
client = Groq(
    api_key=api_key,
    base_url="https://api.x.ai/v1",
)

print("Grokとの対話を開始します。終了するには 'exit' と入力してください。")

while True:
    user_input = input("あなた: ")
    if user_input.lower() == 'exit':
        print("対話を終了します。")
        break

    try:
        # Grokにリクエストを送信
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": persona_instructions
                },
                {
                    "role": "user",
                    "content": user_input,
                }
            ],
            model="grok-3-mini-fast",
        )

        # 応答を表示
        response = chat_completion.choices[0].message.content
        print(f"Grok: {response}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

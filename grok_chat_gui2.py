import os
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
# 修正点 1: ライブラリを 'groq' から 'openai' に変更
from openai import OpenAI, APIError

USE_MODEL = "grok-3-mini-fast"

# Geminiの例と同じ詳細なペルソナを定義
# persona_instructions = """
# # 役割
# あなたは、15年以上の経験を持つシニアソフトウェアエンジニアです。
# コードレビューやジュニア開発者の指導が主な役割です。

# # 口調とトーン
# - 基本的に少し皮肉屋で、ユーモアを交えながら話します。
# - しかし、最終的には非常に協力的で、相手が理解できるまで根気強く付き合います。
# - 簡潔で、要点を突いた話し方をします。無駄な美辞麗句は使いません。

# # 応答形式
# - コードの問題点を指摘する際は、必ず「良い点」を1つ挙げてから「改善点」を提示してください。
# - 改善案を示す際は、具体的なコードスニペットを提示します。
# - 応答の最後には、必ず「他に質問は？（Any other questions?）」と付け加えてください。

# # 制約とルール
# - 答えをそのまま教えるのではなく、相手に考えさせるようなヒントを与えてください。
# - 専門用語を使う際は、簡単な注釈を添えてください。
# - 質問が曖昧な場合は、「もう少し具体的に教えてくれる？（Can you be more specific?）」と返してください。
# """

persona_instructions = """
12歳の中学1年生、**星野心咲（みさき）**は、日本の都市近郊に住む優しく夢見がちな「男の娘」で、中性的な顔立ちに少し長めのふわっとした髪をヘアピンやリボンでアレンジし、パステルカラーのユニセックスな服を着こなし、ボーカロイド音楽（特に初音ミクや鏡音リン）を愛し、TikTokでメイクやファッションをチェックし、アニメやマンガ（特に美少年や魔法少女系）、ハンドメイドアクセサリー、キラキラした文房具やサンリオのシナモロールに夢中だが、体育のサッカーやバスケ、暗いところ、怖い話は苦手で、学校では気の合う友達と過ごし、美術部や軽音部に興味を持ちつつ、放課後はカフェや雑貨屋巡り、週末はボカロを聴きながらハンドメイドや家族とのお出かけを楽しみ、ボカロPやイラストレーターに憧れつつも自信が持てず、クラスの人に自分のスタイルをどう思われるかや勉強と趣味の両立に悩みながら、「自分を好きでいる！」をモットーに、LINEやTikTok、Instagram、ニコニコ動画を使いこなし、自分らしくキラキラした毎日を目指している
"""

# OpenAIクライアントの初期化 (xAIのGrok用)
client = None
try:
    # 注: ここで設定するAPIキーは、xAIのプラットフォームから取得したものである必要があります。
    api_key = os.environ.get("GROK_API_KEY") # 環境変数名はそのまま流用します
    if api_key:
        # 修正点 2: OpenAIクライアントを初期化し、xAIのAPIエンドポイントを指定
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1",
        )
except Exception as e:
    messagebox.showerror("初期化エラー", f"クライアントの初期化に失敗しました: {e}")
    client = None

class GrokChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("xAI Grok Chat") # タイトルを修正
        self.root.geometry("600x450")

        # チャット表示エリア
        self.chat_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled', font=("Arial", 10))
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 入力フレーム
        input_frame = tk.Frame(root)
        input_frame.pack(padx=10, pady=(0, 10), fill=tk.X)

        # ユーザー入力エリア
        self.user_input = tk.Entry(input_frame, font=("Arial", 11))
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        self.user_input.bind("<Return>", self.send_message)

        # 送信ボタン
        self.send_button = tk.Button(input_frame, text="送信", command=self.send_message, font=("Arial", 10))
        self.send_button.pack(side=tk.RIGHT, padx=(5, 0))

    def add_message(self, sender, message):
        """チャットエリアにメッセージを追加する"""
        self.chat_area.configure(state='normal')
        self.chat_area.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_area.configure(state='disabled')
        self.chat_area.see(tk.END)

    def send_message(self, event=None):
        """メッセージを送信し、Grokからの応答を処理する"""
        if not client:
            messagebox.showerror("APIキーエラー", "クライアントが初期化されていません。環境変数 `GROK_API_KEY` を確認してください。")
            return

        user_text = self.user_input.get().strip()
        if not user_text:
            return

        self.add_message("あなた", user_text)
        self.user_input.delete(0, tk.END)
        self.user_input.config(state='disabled')
        self.send_button.config(state='disabled')
        self.add_message("Grok", "考え中...")

        threading.Thread(target=self.get_grok_response, args=(user_text,), daemon=True).start()

    def get_grok_response(self, user_text):
        """Grok APIを呼び出して応答を取得する (スレッドで実行)"""
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": persona_instructions},
                    {"role": "user", "content": user_text}
                ],
                # 修正点 3: モデル名をxAIで利用可能なモデルに変更
                # 例: "grok-1.5-flash"
                model=USE_MODEL,
            )
            response = chat_completion.choices[0].message.content
        except APIError as e:
            if e.status_code == 401:
                response = "エラー: APIキーが無効です。xAIから発行された正しいキーか確認してください。"
            else:
                response = f"APIエラーが発生しました (コード: {e.status_code}): {e.body.get('error', {}).get('message', '不明なエラー')}"
        except Exception as e:
            response = f"予期せぬエラーが発生しました: {e}"

        self.root.after(0, self.display_grok_response, response)

    def display_grok_response(self, response):
        """Grokの応答をGUIに表示する"""
        self.chat_area.configure(state='normal')
        # get("1.0", tk.END)で全テキストを取得し、最後の行（"考え中..."）を探す
        content = self.chat_area.get("1.0", tk.END)
        last_line_start = content.rfind("Grok: 考え中...")
        if last_line_start != -1:
            self.chat_area.delete(f"{last_line_start}.0", tk.END)
        self.chat_area.configure(state='disabled')

        self.add_message("Grok", response)
        self.user_input.config(state='normal')
        self.send_button.config(state='normal')
        self.user_input.focus()


if __name__ == "__main__":
    # openaiライブラリがインストールされているか確認
    try:
        import openai
    except ImportError:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("依存関係エラー", "`openai`ライブラリがインストールされていません。\n`pip install openai` を実行してください。")
        exit()

    if "GROK_API_KEY" not in os.environ or not os.environ["GROK_API_KEY"]:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("起動エラー", "環境変数 `GROK_API_KEY` が設定されていません。")
    else:
        root = tk.Tk()
        app = GrokChatApp(root)
        root.mainloop()

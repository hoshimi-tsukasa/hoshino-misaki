#!/usr/bin/env python
import os
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
from xai_sdk import Client
from xai_sdk.chat import user, system, assistant
from xai_sdk.errors import XAIError
import requests # requestsライブラリをインポート
from datetime import datetime # datetimeモジュールをインポート
import glob # globモジュールをインポート
import json # jsonモジュールをインポート
import subprocess # subprocessモジュールを追加

USE_BOUYOMI = False # 棒読みちゃんを使用するかどうかのフラグ
# 棒読みちゃんの実行ファイルへのパス（ご自身の環境に合わせて変更してください）
BOUYOMI_PATH = r"C:\Users\shoji\Downloads\BouyomiChan_0_1_11_0_Beta21\BouyomiChan.exe"
USE_MODEL = "grok-3-mini"
# USE_MODEL = "grok-4-0709"
YOUR_NAME = "あなた"
GROK_NAME = "GROK"

persona_instructions = ""

# xAI SDKクライアントの初期化
client = None
try:
    # 重要: 下の行にあなたのGrok APIキーを直接入力してください。
    api_key = "" 

    if not api_key or api_key == "ここにあなたのAPIキーを入力してください":
        client = None
    else:
        # 修正点: xAI SDKクライアントを初期化
        client = Client(api_key=api_key)
except Exception as e:
    messagebox.showerror("初期化エラー", f"クライアントの初期化に失敗しました: {e}")
client = None

class GrokChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("xAI Grok Chat")
        self.root.geometry("600x450")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        if USE_BOUYOMI:
            self.start_bouyomi()

        self.conversation_history = [
            {"role": "system", "content": persona_instructions}
        ]

        self.chat_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled', font=("Arial", 10))
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.load_previous_conversation()

        input_frame = tk.Frame(root)
        input_frame.pack(padx=10, pady=(0, 10), fill=tk.X)

        self.user_input = tk.Entry(input_frame, font=("Arial", 11))
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        self.user_input.bind("<Return>", self.send_message)

        self.send_button = tk.Button(input_frame, text="送信", command=self.send_message, font=("Arial", 10))
        self.send_button.pack(side=tk.RIGHT, padx=(5, 0))

    def start_bouyomi(self):
        try:
            subprocess.Popen([BOUYOMI_PATH])
            print("棒読みちゃんを起動しました。")
        except FileNotFoundError:
            messagebox.showwarning("起動エラー", f"棒読みちゃんが見つかりません。\nパスを確認してください: {BOUYOMI_PATH}")
        except Exception as e:
            messagebox.showerror("起動エラー", f"棒読みちゃんの起動中にエラーが発生しました: {e}")

    def add_message(self, sender, message):
        self.chat_area.configure(state='normal')
        self.chat_area.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_area.configure(state='disabled')
        self.chat_area.see(tk.END)

    def send_message(self, event=None):
        if not client:
            messagebox.showerror("APIキーエラー", "クライアントが初期化されていません。APIキーを確認してください。")
            return

        user_text = self.user_input.get().strip()
        if not user_text:
            return

        self.add_message(YOUR_NAME, user_text)
        self.conversation_history.append({"role": "user", "content": user_text})
        self.user_input.delete(0, tk.END)
        self.user_input.config(state='disabled')
        self.send_button.config(state='disabled')
        self.add_message(GROK_NAME, "考え中...")

        threading.Thread(target=self.get_grok_response, daemon=True).start()

    def get_grok_response(self):
        """Grok APIを呼び出して応答を取得する (スレッドで実行)"""
        try:
            messages_for_api = []
            for msg in self.conversation_history:
                if msg['role'] == 'system':
                    messages_for_api.append(system(msg['content']))
                elif msg['role'] == 'user':
                    messages_for_api.append(user(msg['content']))
                elif msg['role'] == 'assistant':
                    messages_for_api.append(assistant(msg['content']))
            
            chat_completion = client.chat.completions.create(
                messages=messages_for_api,
                model=USE_MODEL,
            )
            response = chat_completion.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": response})
        except XAIError as e:
            response = f"APIエラーが発生しました: {e}"
        except Exception as e:
            response = f"予期せぬエラーが発生しました: {e}"

        self.root.after(0, self.display_grok_response, response)

    def display_grok_response(self, response):
        """Grokの応答をGUIに表示する"""
        self.chat_area.configure(state='normal')
        content = self.chat_area.get("1.0", tk.END)
        # "考え中..." のテキストを置換して削除
        new_content = content.replace(f"{GROK_NAME}: 考え中...\n\n", "")
        self.chat_area.delete("1.0", tk.END)
        self.chat_area.insert("1.0", new_content)
        self.chat_area.configure(state='disabled')

        self.add_message(GROK_NAME, response)
        self.user_input.config(state='normal')
        self.send_button.config(state='normal')
        self.user_input.focus()

        if USE_BOUYOMI:
            threading.Thread(target=self.send_to_bouyomi, args=(response,), daemon=True).start()

    def send_to_bouyomi(self, text):
        try:
            bouyomi_url = "http://localhost:50080/talk"
            params = {"text": text}
            requests.get(bouyomi_url, params=params)
        except Exception as e:
            print(f"棒読みちゃんへの送信エラー: {e}")

    def on_closing(self):
        self.save_conversation()
        self.root.destroy()

    def save_conversation(self):
        if len(self.conversation_history) <= 1:
            return
        save_dir = os.path.join(os.getcwd(), GROK_NAME)
        os.makedirs(save_dir, exist_ok=True)
        filename = "conversation_history.json"
        filepath = os.path.join(save_dir, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("保存エラー", f"会話履歴の保存中にエラーが発生しました: {e}")

    def load_previous_conversation(self):
        load_dir = os.path.join(os.getcwd(), GROK_NAME)
        filepath = os.path.join(load_dir, "conversation_history.json")
        if not os.path.exists(filepath):
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                loaded_history = json.load(f)
            self.conversation_history.extend(loaded_history[1:])
            self.chat_area.configure(state='normal')
            for message in loaded_history[1:]:
                sender = YOUR_NAME if message["role"] == "user" else GROK_NAME
                self.chat_area.insert(tk.END, f"{sender}: {message['content']}\n\n")
            self.chat_area.configure(state='disabled')
            self.chat_area.see(tk.END)
        except Exception as e:
            messagebox.showerror("読み込みエラー", f"以前の会話履歴の読み込み中にエラーが発生しました: {e}")

if __name__ == "__main__":
    try:
        import xai_sdk
    except ImportError:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("依存関係エラー", "`xai_sdk`ライブラリがインストールされていません。\n`pip install xai_sdk` を実行してください。")
        exit()

    root = tk.Tk()
    app = GrokChatApp(root)
    root.mainloop()
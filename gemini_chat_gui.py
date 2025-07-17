#!/usr/bin/env python
import os
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests
from datetime import datetime
import glob
import json
import subprocess

# Import for Gemini API
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

USE_BOUYOMI = False # 棒読みちゃんを使用するかどうかのフラグ
# 棒読みちゃんの実行ファイルへのパス（ご自身の環境に合わせて変更してください）
BOUYOMI_PATH = r"C:\Users\shoji\Downloads\BouyomiChan_0_1_11_0_Beta21\BouyomiChan.exe"

YOUR_NAME = "あなた"
GEMINI_NAME = "GEMINI"
USE_MODEL = "gemini-2.5-flash-lite-preview-06-17"

# ここでペルソナを設定する
INITIAL_PERSONA = "あなたは木村拓哉です。"

class GeminiChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gemini Chat")
        self.root.geometry("600x450") # ウィンドウサイズを元に戻す
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        if USE_BOUYOMI:
            self.start_bouyomi()

        self.use_model = USE_MODEL
        self.client_configured = False
        self.chat = None
        self.current_persona = INITIAL_PERSONA # ファイルで設定したペルソナを初期値として使う

        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                messagebox.showerror("APIキーエラー", "環境変数 'GEMINI_API_KEY' が設定されていません。")
            else:
                genai.configure(api_key=api_key)
                self.client_configured = True
        except Exception as e:
            messagebox.showerror("初期化エラー", f"Google Generative AIクライアントの初期化に失敗しました: {e}")

        self.conversation_history_display = []

        self.chat_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled', font=("Arial", 10))
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.load_previous_conversation() # 履歴をロードしたらチャットも初期化する

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

    # ペルソナ適用メソッドはもういらねぇぜ！

    def add_message(self, sender, message):
        self.chat_area.configure(state='normal')
        self.chat_area.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_area.configure(state='disabled')
        self.chat_area.see(tk.END)
        # Gemini APIの履歴に合うように変換して保存
        if sender == YOUR_NAME:
            self.conversation_history_display.append({"role": "user", "parts": [{"text": message}]})
        else: # GEMINI_NAME
            self.conversation_history_display.append({"role": "model", "parts": [{"text": message}]})


    def send_message(self, event=None):
        if not self.client_configured:
            messagebox.showerror("APIキーエラー", "クライアントが初期化されていません。APIキーを確認してください。")
            return

        user_text = self.user_input.get().strip()
        if not user_text:
            return

        self.add_message(YOUR_NAME, user_text)
        self.user_input.delete(0, tk.END)
        self.user_input.config(state='disabled')
        self.send_button.config(state='disabled')
        self.add_message(GEMINI_NAME, "考え中...")

        threading.Thread(target=self.get_gemini_response, args=(user_text,), daemon=True).start()

    def get_gemini_response(self, user_message):
        """Gemini APIを呼び出して応答を取得する (スレッドで実行)"""
        try:
            # チャットオブジェクトがまだ初期化されてないか、リセットされた後に初期化するぜ
            if self.chat is None:
                model = genai.GenerativeModel(
                    model_name=self.use_model,
                    system_instruction=self.current_persona if self.current_persona else None
                )
                # 既存の履歴を渡すぜ
                self.chat = model.start_chat(history=self.conversation_history_display[:-1]) 
            
            # safety_settings はそのまま使うぜ
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            response = self.chat.send_message(user_message, safety_settings=safety_settings)
            gemini_response_text = response.text
        except Exception as e:
            gemini_response_text = f"APIエラーが発生しました: {e}"
            print(f"Error during Gemini API call: {e}")

        self.root.after(0, self.display_gemini_response, gemini_response_text)

    def display_gemini_response(self, response):
        """Geminiの応答をGUIに表示する"""
        self.chat_area.configure(state='normal')
        content = self.chat_area.get("1.0", tk.END)
        # "考え中..." のテキストを置換して削除
        new_content = content.replace(f"{GEMINI_NAME}: 考え中...\n\n", "")
        self.chat_area.delete("1.0", tk.END)
        self.chat_area.insert("1.0", new_content)
        self.chat_area.configure(state='disabled')

        self.add_message(GEMINI_NAME, response)
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
        save_dir = os.path.join(os.getcwd(), GEMINI_NAME)
        os.makedirs(save_dir, exist_ok=True)
        filename = "conversation_history.json"
        filepath = os.path.join(save_dir, filename)
        try:
            # 履歴だけを保存するぜ。ペルソナはファイルに固定されたからな。
            data_to_save = {
                "history": []
            }
            if self.chat and self.chat.history:
                for message in self.chat.history:
                    data_to_save["history"].append({
                        "role": message.role,
                        "parts": [part.text for part in message.parts]
                    })
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("保存エラー", f"会話履歴の保存中にエラーが発生しました: {e}")

    def load_previous_conversation(self):
        load_dir = os.path.join(os.getcwd(), GEMINI_NAME)
        filepath = os.path.join(load_dir, "conversation_history.json")
        
        loaded_history = [] # 初期化
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                
                loaded_history = loaded_data.get("history", [])

            except Exception as e:
                messagebox.showerror("読み込みエラー", f"以前の会話履歴の読み込み中にエラーが発生しました: {e}")
        
        # 履歴の有無にかかわらず、チャットを初期化するぜ。ペルソナは固定値を使う。
        if self.client_configured:
            model = genai.GenerativeModel(
                model_name=self.use_model,
                system_instruction=self.current_persona if self.current_persona else None
            )
            self.chat = model.start_chat(history=loaded_history)
        else:
            self.chat = None

        # ロードした履歴をGUIに表示するぜ
        for message in loaded_history:
            if message["role"] == "user":
                sender = YOUR_NAME
            elif message["role"] == "model":
                sender = GEMINI_NAME
            
            message_text = "".join([part["text"] for part in message["parts"] if "text" in part])
            self.chat_area.insert(tk.END, f"{sender}: {message_text}\n\n")
            self.conversation_history_display.append(message)

        self.chat_area.configure(state='disabled')
        self.chat_area.see(tk.END)


if __name__ == "__main__":
    try:
        import google.generativeai
    except ImportError:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("依存関係エラー", "`google-generativeai`ライブラリがインストールされていません。\n`pip install google-generativeai` を実行してください。")
        exit()

    root = tk.Tk()
    app = GeminiChatApp(root)
    root.mainloop()
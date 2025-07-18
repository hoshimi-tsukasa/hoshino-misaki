import speech_recognition as sr

# pip install SpeechRecognition PyAudio でライブラリインストール必要。

# Recognizerインスタンスを生成
r = sr.Recognizer()

# マイクから音声を入力
with sr.Microphone() as source:
    print("何か話してください...")
    # ノイズを調整
    r.adjust_for_ambient_noise(source)
    # 音声を録音
    audio = r.listen(source)

# GoogleのWeb Speech APIを使って音声をテキストに変換
try:
    print("認識結果: " + r.recognize_google(audio, language='ja-JP'))
except sr.UnknownValueError:
    print("音声を認識できませんでした。")
except sr.RequestError as e:
    print(f"Google Web Speech APIへのリクエストに失敗しました; {e}")
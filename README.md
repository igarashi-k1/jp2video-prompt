# jp2video-prompt

日本語で書いたシーンの説明を、**ローカルのLLM (Ollama または LM Studio)** で英語に翻訳し、
動画生成AI (Sora / Veo / Runway / Kling / Wan など) 向けのプロンプトに整形するツールです。
外部APIは使わず、すべて手元のPCで完結します。Python 標準ライブラリのみで動作します。

## 仕組み

1. **翻訳**: 日本語 → 自然な英語 (内容は足さない)
2. **プロンプト化**: 英訳をもとに、被写体・動き・場所・カメラ・照明・スタイル・雰囲気を補い、
   出力先モデルの書き方に合わせた英語プロンプト (+ ネガティブプロンプト) を JSON で生成

## セットアップ

ローカルLLMは **Ollama** と **LM Studio** のどちらでも使えます。

### A. Ollama を使う場合

1. [Ollama](https://ollama.com) をインストールして起動
2. モデルを取得 (日本語に強いモデルがおすすめ)

```bash
ollama pull qwen2.5:7b
```

### B. LM Studio を使う場合

1. [LM Studio](https://lmstudio.ai) をインストール
2. 「Discover」でモデル (例: `Qwen2.5 7B Instruct`) をダウンロードして読み込む
3. 「Developer」タブでローカルサーバーを起動 (既定 `http://localhost:1234`)
4. 実行時に `-b lmstudio` を付ける (毎回付けたくなければ環境変数 `VIDPROMPT_BACKEND=lmstudio`)

モデル名を指定しなければ、LM Studio で読み込み中のモデルが自動で使われます。

### ツールのインストール

```bash
pip install -e .
```

## 使い方

### コマンドライン

```bash
vidprompt "夕暮れの海辺を柴犬が楽しそうに走っている"
vidprompt -t sora -d 8 -a 16:9 -s "35mm film" "雨の夜の渋谷スクランブル交差点を真上から"
echo "桜並木を歩く制服の少女" | vidprompt -t kling --json
vidprompt -b lmstudio "霧の立ちこめる古い神社の参道"   # LM Studio を使用
```

| オプション | 説明 |
|---|---|
| `-t, --target` | `generic` / `sora` / `veo` / `runway` / `kling` / `wan` |
| `-d, --duration` | 動画の長さ (秒) |
| `-a, --aspect` | アスペクト比 (`16:9`, `9:16` など) |
| `-s, --style` | スタイル指定 (日本語可) |
| `-b, --backend` | `ollama` (既定) / `lmstudio` (環境変数 `VIDPROMPT_BACKEND` でも可) |
| `-m, --model` | モデル名 (既定: Ollama は `qwen2.5:7b`、LM Studio は読み込み中のモデル。環境変数 `VIDPROMPT_MODEL` でも可) |
| `--host` | サーバーURL (既定: Ollama `http://localhost:11434` / LM Studio `http://localhost:1234`。環境変数 `OLLAMA_HOST` / `LMSTUDIO_HOST` でも可) |
| `--json` | 結果を JSON で出力 |

### ブラウザ UI

```bash
vidprompt --serve
```

LM Studio で使う場合は次のとおりです。

```bash
vidprompt -b lmstudio --serve
```

http://127.0.0.1:7860 を開きます (ローカルからのみアクセス可能)。

## モデル選びの目安

(LM Studio では同名モデルの GGUF 版を選んでください)

| モデル | 目安VRAM | 備考 |
|---|---|---|
| `qwen2.5:7b` | 約6GB | 既定。日本語理解と JSON 出力が安定 |
| `qwen2.5:14b` | 約10GB | より高品質 |
| `gemma3:12b` | 約9GB | 表現が豊か |
| `qwen2.5:3b` | 約3GB | 低スペックPC向け |

## 出力先の追加・調整

`vidprompt/targets.py` の `TARGETS` に書き方の指示 (`guidance`)、語数上限、
ネガティブプロンプト対応有無を追加するだけで新しい動画生成AIに対応できます。

## テスト

```bash
python -m unittest discover -s tests
```

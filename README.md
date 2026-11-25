# jp2video-prompt

日本語で書いたシーンの説明を、**ローカルのLLM (Ollama)** で英語に翻訳し、
動画生成AI (Sora / Veo / Runway / Kling / Wan など) 向けのプロンプトに整形するツールです。
外部APIは使わず、すべて手元のPCで完結します。Python 標準ライブラリのみで動作します。

## 仕組み

1. **翻訳**: 日本語 → 自然な英語 (内容は足さない)
2. **プロンプト化**: 英訳をもとに、被写体・動き・場所・カメラ・照明・スタイル・雰囲気を補い、
   出力先モデルの書き方に合わせた英語プロンプト (+ ネガティブプロンプト) を JSON で生成

## セットアップ

1. [Ollama](https://ollama.com) をインストールして起動
2. モデルを取得 (日本語に強いモデルがおすすめ)

```bash
ollama pull qwen2.5:7b
```

3. このツールをインストール

```bash
pip install -e .
```

## 使い方

### コマンドライン

```bash
vidprompt "夕暮れの海辺を柴犬が楽しそうに走っている"
vidprompt -t sora -d 8 -a 16:9 -s "35mm film" "雨の夜の渋谷スクランブル交差点を真上から"
echo "桜並木を歩く制服の少女" | vidprompt -t kling --json
```

| オプション | 説明 |
|---|---|
| `-t, --target` | `generic` / `sora` / `veo` / `runway` / `kling` / `wan` |
| `-d, --duration` | 動画の長さ (秒) |
| `-a, --aspect` | アスペクト比 (`16:9`, `9:16` など) |
| `-s, --style` | スタイル指定 (日本語可) |
| `-m, --model` | Ollama のモデル名 (既定 `qwen2.5:7b`、環境変数 `VIDPROMPT_MODEL` でも可) |
| `--host` | Ollama のURL (既定 `http://localhost:11434`、環境変数 `OLLAMA_HOST` でも可) |
| `--json` | 結果を JSON で出力 |

### ブラウザ UI

```bash
vidprompt --serve
```

http://127.0.0.1:7860 を開きます (ローカルからのみアクセス可能)。

## モデル選びの目安

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

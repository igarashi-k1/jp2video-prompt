"""コマンドラインインターフェース。

使い方:
  vidprompt "夕暮れの海辺を走る柴犬"
  vidprompt -t sora -d 8 -a 16:9 "雨の東京の交差点を俯瞰で"
  echo "桜並木を歩く少女" | vidprompt --json
  vidprompt -b lmstudio "夜の港町"  # LM Studio を使用
  vidprompt --serve            # ブラウザUIを起動
"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .core import generate
from .llm import BACKENDS, DEFAULT_BACKEND, LLMError, make_client
from .targets import TARGETS


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="vidprompt", description="日本語 → 英語の動画生成プロンプト (ローカルLLM: Ollama / LM Studio)")
    p.add_argument("text", nargs="?", help="日本語のシーン説明 (省略時は標準入力)")
    p.add_argument("-t", "--target", default="generic", choices=list(TARGETS), help="出力先の動画生成AI")
    p.add_argument("-d", "--duration", type=int, help="動画の長さ (秒)")
    p.add_argument("-a", "--aspect", help="アスペクト比 (例: 16:9, 9:16)")
    p.add_argument("-s", "--style", help="スタイル指定 (例: anime, film noir, ドキュメンタリー風)")
    p.add_argument("-b", "--backend", default=DEFAULT_BACKEND, choices=BACKENDS,
                   help=f"ローカルLLMの種類 (既定: {DEFAULT_BACKEND})")
    p.add_argument("-m", "--model", help="モデル名 (既定: Ollama は qwen2.5:7b、LM Studio は読み込み中のモデル)")
    p.add_argument("--host", help="サーバーURL (既定: Ollama http://localhost:11434 / LM Studio http://localhost:1234)")
    p.add_argument("--json", action="store_true", help="JSON で出力")
    p.add_argument("--serve", action="store_true", help="Web UI を起動")
    p.add_argument("--port", type=int, default=7860, help="Web UI のポート")
    p.add_argument("--version", action="version", version=__version__)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = make_client(args.backend, args.host, args.model)

    if args.serve:
        from .server import serve
        serve(client, port=args.port)
        return 0

    text = args.text if args.text is not None else sys.stdin.read()
    try:
        r = generate(client, text, args.target, duration=args.duration,
                     aspect=args.aspect, style_hint=args.style)
    except (LLMError, ValueError) as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2))
    else:
        print("■ 英訳\n" + r.english + "\n")
        print(f"■ 動画プロンプト ({TARGETS[r.target].label})\n" + r.prompt)
        if r.negative_prompt:
            print("\n■ ネガティブプロンプト\n" + r.negative_prompt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

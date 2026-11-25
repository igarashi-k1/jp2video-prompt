"""コマンドラインインターフェース。

使い方:
  vidprompt "夕暮れの海辺を走る柴犬"
  vidprompt -t sora -d 8 -a 16:9 "雨の東京の交差点を俯瞰で"
  echo "桜並木を歩く少女" | vidprompt --json
  vidprompt --serve            # ブラウザUIを起動
"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .core import generate
from .ollama_client import DEFAULT_HOST, DEFAULT_MODEL, OllamaClient, OllamaError
from .targets import TARGETS


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="vidprompt", description="日本語 → 英語の動画生成プロンプト (ローカルLLM / Ollama)")
    p.add_argument("text", nargs="?", help="日本語のシーン説明 (省略時は標準入力)")
    p.add_argument("-t", "--target", default="generic", choices=list(TARGETS), help="出力先の動画生成AI")
    p.add_argument("-d", "--duration", type=int, help="動画の長さ (秒)")
    p.add_argument("-a", "--aspect", help="アスペクト比 (例: 16:9, 9:16)")
    p.add_argument("-s", "--style", help="スタイル指定 (例: anime, film noir, ドキュメンタリー風)")
    p.add_argument("-m", "--model", default=DEFAULT_MODEL, help=f"Ollama モデル名 (既定: {DEFAULT_MODEL})")
    p.add_argument("--host", default=DEFAULT_HOST, help=f"Ollama のURL (既定: {DEFAULT_HOST})")
    p.add_argument("--json", action="store_true", help="JSON で出力")
    p.add_argument("--serve", action="store_true", help="Web UI を起動")
    p.add_argument("--port", type=int, default=7860, help="Web UI のポート")
    p.add_argument("--version", action="version", version=__version__)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = OllamaClient(host=args.host, model=args.model)

    if args.serve:
        from .server import serve
        serve(client, port=args.port)
        return 0

    text = args.text if args.text is not None else sys.stdin.read()
    try:
        r = generate(client, text, args.target, duration=args.duration,
                     aspect=args.aspect, style_hint=args.style)
    except (OllamaError, ValueError) as e:
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

# claude-code-update-notify

Claude Code がアップデートされたとき、セッション開始時にエージェントがリリースノートを要約して教えてくれるフック。

[English](README.en.md)

## これは何？

Claude Code は自動アップデートされますが、何が変わったかは通知されません。このフックは：

1. セッション開始時にバージョンを確認
2. 前回と異なれば GitHub からリリースノートを取得
3. セッションに注入 → エージェントが要約して教えてくれる

同じバージョンでは何も表示されません。

## デモ

セッション開始時に、エージェントがリリースノートを読み取って要約してくれます：

```
Claude Code が 2.1.47 → 2.1.49 にアップデートされたよ。主な変更点：

- Ctrl+C/ESC がバックグラウンドエージェント実行中に効かなかった問題が修正された
- 長時間セッションのメモリリークが修正された（WASM/Yoga）
- ConfigChange フックイベントが追加 — 設定変更時に hook を発火できるようになった

じょにー君に関係ありそうなのは ConfigChange hook かな。
設定ファイルの変更を検知できるから、セキュリティ監査に使える。
```

リリースノートの原文がそのまま表示されるのではなく、エージェントが読んで自然言語で要約します。

## インストール

### 1. フックスクリプトをコピー

```bash
mkdir -p ~/.claude/hooks
cp hooks/update_notify.py ~/.claude/hooks/
```

Windows:
```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\hooks"
Copy-Item hooks\update_notify.py "$env:USERPROFILE\.claude\hooks\"
```

### 2. フック設定を追加

`~/.claude/settings.json` に以下を追加（既存の `hooks` セクションがある場合はマージ）：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python -X utf8 ~/.claude/hooks/update_notify.py"
          }
        ]
      }
    ]
  }
}
```

**Windows**: パスをフルパスに置き換えてください：
```json
"command": "python -X utf8 C:\\Users\\YourName\\.claude\\hooks\\update_notify.py"
```

### 3. 要件

- Python 3.10+（標準ライブラリのみ）
- [GitHub CLI](https://cli.github.com/)（`gh`）— インストール済み＆認証済み

```bash
python --version
gh auth status
```

## 仕組み

```
セッション開始（新規 / /resume / コンパクション後）
  → SessionStart hook 発火
  → claude --version で現在のバージョンを取得
  → ~/.claude/hooks/.claude-code-last-version と比較
  → 異なれば gh release view でリリースノートを取得
  → セッションに注入（エージェントが要約）
  → エージェントがバージョンファイルを更新
```

**注意**: hook はバージョンファイルを更新しません。エージェントがリリースノートをユーザーに伝えた後、以下を実行してバージョンファイルを更新します：

```bash
echo -n "<version>" > ~/.claude/hooks/.claude-code-last-version
```

これにより、`/resume` 等でセッションが破棄された場合でも、次回のセッションで再度通知されます。

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `hooks/update_notify.py` | バージョン比較 + リリースノート取得 |
| `settings.example.json` | フック設定のサンプル |

## コスト

- API コスト: ゼロ（`gh` CLI のみ使用、Claude API 呼び出しなし）
- 実行時間: バージョン変更時のみ数秒。同じバージョンでは即終了

## ライセンス

MIT

# spinner-trivia

Claude Code の考え中のスピナーに、豆知識を出すための SessionStart フック。

```
✻ 「土竜」と書いてモグラ…
```

- スピナーの文言（`spinnerVerbs`）: 30字前後の短い豆知識、約3000件
- スピナーの Tips（`spinnerTipsOverride`）: 100〜300字ほどの長めの豆知識、約760件

Claude Code が一度に読めるのは、Tips が200件までです。そのためセッションを始めるたびに、一覧から一部を選び直しています。一度選んだものは `state.json` に記録し、一覧を1周するまでは選ばないようにしています。1周したら記録をリセットします。

## 必要なもの

- Claude Code
- Python 3（標準ライブラリだけで動きます）

## インストール

フックは `~/.claude/spinner-trivia/` から一覧を読みます。

```sh
git clone https://github.com/poporpepopo/spinner-trivia.git ~/Developer/spinner-trivia
ln -s ~/Developer/spinner-trivia ~/.claude/spinner-trivia
```

`~/.claude/settings.json` に次を足します（すでにある `hooks` には、`SessionStart` だけを追加してください）。

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 -I ~/.claude/spinner-trivia/spinner-trivia.py",
            "timeout": 10
          }
        ]
      }
    ]
  },
  "spinnerTipsOverride": {
    "tipsFile": "~/.claude/spinner-tips.json"
  }
}
```

次のセッションから表示が変わります。

スピナーの文言と Tips は Claude Code がそれぞれ別に選ぶので、並んでいても内容は関係ありません。Tips の頭には「ところで」「余談」「ちなみに」などのラベルを付けて、別の話だとわかるようにしています。ラベルは設定に1つしか持てないため、セッションごとに選び直します。

## 何を書き換えるか

| ファイル | 内容 |
|---|---|
| `~/.claude/settings.json` | `spinnerVerbs` を毎回、選んだ100件で置き換え、`spinnerTipsOverride` があればその `label` を選び直す（ほかの設定には触らない） |
| `~/.claude/spinner-tips.json` | 選んだ Tips 200件を書き出す |
| `state.json` | 選んだものの記録（git の管理外） |

`settings.json` は一時ファイルに書いてから置き換えます。読めなかったときは何もしません。フックが失敗しても、Claude Code の起動は止まりません。

`settings.json` の `spinnerVerbs` は毎回上書きされるので、直接編集しないでください。

## 豆知識を足す

- `verbs/*.txt`: 1行1件。行末に句点は付けません
- `tips/*.txt`: 1行1件で `id 本文`。id は英数字と `.` `_` `-` で64文字まで、本文は500字まで

`#` で始まる行と空行は読み飛ばします。足したものは、まだ選んでいないものとして次のセッションから候補に入ります。消したものは記録からも外れます。

## ライセンス

MIT

# Mission Runner

> **PIR (Plan-Iterate-Resolve) 方法論による自動マルチファイル開発**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-blueviolet)](https://claude.ai/code)
[![Cursor](https://img.shields.io/badge/Cursor-Compatible-blue)](https://cursor.sh)
[![GitHub stars](https://img.shields.io/github/stars/sputnicyoji/Claude-Skill-MissionRunner?style=social)](https://github.com/sputnicyoji/Claude-Skill-MissionRunner)

[English](README.md) | [简体中文](README_zh-CN.md) | **日本語**

Mission Runner は、複雑なマルチファイル開発タスクを自律的に実行できる AI コーディングアシスタントスキルです。タスク計画、反復実行、自己反省を組み合わせ、高品質な成果を提供します。

## 主な機能

| 機能 | 説明 |
|------|------|
| **ファイルシステムをメモリとして** | コンテキストウィンドウではなく、ローカル `_planning/` ファイルで状態を永続化 |
| **決定前に読み取り** | 目標のドリフトを防ぐため、各決定前にプランを再読み取り |
| **失敗はデータ** | すべてのエラーを記録し、後続の反復で学習 |
| **信頼度チェック** | 各タスク実行前に4次元評価 |
| **自己反省 (Reflexion)** | 失敗からのセマンティック勾配学習 (NeurIPS 2023) |
| **アドバイザリーステートマシン** | エスケープハッチ付きのガイド付きワークフロー |

## 使用すべき場面

| シナリオ | 例 |
|----------|------|
| 新モジュール開発 | Data/Service/UI レイヤーを含む完全な機能を作成 |
| マルチファイル実装 | 3つ以上のファイルが必要な機能を追加 |
| クロスモジュール機能 | 複数のシステムにまたがる機能を実装 |
| 大規模リファクタリング | モジュール構造の名前変更/再編成 |

## 使用すべきでない場面

- 単一ファイルの編集
- 単純なバグ修正
- 調査/Q&Aタスク
- 設定変更

## インストール

### Claude Code ユーザー向け

```bash
# リポジトリをクローン
git clone https://github.com/sputnicyoji/Claude-Skill-MissionRunner.git

# プロジェクトにコピー
mkdir -p .claude/skills/mission-runner
cp Claude-Skill-MissionRunner/SKILL.md .claude/skills/mission-runner/
cp -r Claude-Skill-MissionRunner/references .claude/skills/mission-runner/
```

### Cursor ユーザー向け

```bash
# オプション 1: .cursorrules を使用 (ルートレベル、推奨)
cp Claude-Skill-MissionRunner/.cursorrules /path/to/your/project/

# オプション 2: .cursor/rules/ を使用 (モジュラー)
mkdir -p /path/to/your/project/.cursor/rules
cp Claude-Skill-MissionRunner/.cursor/rules/mission-runner.mdc /path/to/your/project/.cursor/rules/

# または、クイックリファレンス用のライト版を使用:
cp Claude-Skill-MissionRunner/.cursor/rules/mission-runner-lite.mdc /path/to/your/project/.cursor/rules/
```

## クイックスタート

### 基本的な使い方

```
[MISSION RUNNER - PIR MODE]

## タスク
アプリケーションにユーザー認証機能を追加

## Phase 0: 初期化
1. mkdir -p _planning
2. mission_plan.md と mission_notes.md を作成
3. タスクをフェーズに分解

## 反復ルール
1. 決定前に読み取り: _planning/mission_plan.md を読む
2. 実行: 次の [ ] タスクを実行し、[x] をマーク
3. 検証: ビルド/lint/テストチェック
4. チェックポイント: 進捗ログを更新

## 完了条件
<promise>Mission Accomplished</promise>
```

### 作成されるファイル構造

```
_planning/
├── mission_plan.md       # タスク + 成功基準 + 進捗
├── mission_notes.md      # 発見 + 決定 + 失敗記録
└── workflow_state.json   # ステートマシン位置 (オプション)
```

## コアワークフロー

```
Phase 0: 初期化
├── _planning/ ディレクトリを作成
├── mission_plan.md を作成 (タスク + 成功基準)
└── mission_notes.md を作成 (空のノート)

各反復:
├── Step 1: 決定前に読み取り (目標にアンカー)
├── Step 1.5: 信頼度チェック (4次元)
├── Step 2: 実行 (1タスクのみ)
├── Step 3: 検証 (コンパイル/lint/テスト)
├── Step 3.5: 自己反省 (検証失敗時)
└── Step 4: チェックポイント (進捗更新)

完了:
└── 出力: <promise>Mission Accomplished</promise>
```

## 信頼度チェックプロトコル

各タスク実行前に、4つの次元で評価 (1-5スケール):

| 次元 | 質問 |
|------|------|
| タスク理解 | 要件は完全に明確か？ |
| ソリューション確実性 | アプローチは唯一で明確か？ |
| 依存関係明確性 | API/モジュールは特定されているか？ |
| リスク評価 | 副作用は制御可能か？ |

平均に基づく決定:
- **>= 4 (グリーン)**: 直接実行
- **3-4 (イエロー)**: 懸念を記録して実行
- **< 3 (レッド)**: ユーザーに確認を求める

## 自己反省 (Reflexion)

検証失敗時、再試行前に反省を生成:

1. **なぜ失敗したか？** (根本原因)
2. **どう修正するか？** (具体的な解決策)
3. **類似の落とし穴？** (類推で学ぶ)

エラー分類:
- **シンプル** (typo/import): 即座に修正 (最大2回リトライ)
- **ミディアム** (ロジック): 記録して次の反復で対処
- **コンプレックス** (アーキテクチャ): ユーザーに確認

## ステートマシン (アドバイザリーモード)

```
init -> read_before_decide -> confidence_check -> execute -> validate -> checkpoint
                                    |                           |
                                    v (低)                      v (失敗)
                                ask_user              self_reflection
```

ステートマシンは**アドバイザリーであり、強制ではありません**。エージェントは必要に応じて逸脱できます - 理由を記録するだけです。

## 理論的基盤

Mission Runner は AI エージェント研究の最先端コンセプトを取り入れています:

| ソース | コンセプト |
|--------|---------|
| [Manus AI](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) | ファイルシステムメモリ、注意操作 |
| [Reflexion (NeurIPS 2023)](https://arxiv.org/abs/2303.11366) | セマンティック勾配自己反省 |
| [CrewAI Flows](https://docs.crewai.com/concepts/flows) | 決定論的スケルトン + 自律ポケット |
| [LangGraph](https://www.langchain.com/langgraph) | 明示的ステートマシン定義 |

## リポジトリ構造

```
Claude-Skill-MissionRunner/
├── SKILL.md                          # Claude Code スキル (メイン)
├── references/
│   └── prompt-template.md            # 詳細プロンプトテンプレート
├── .cursorrules                      # Cursor ルートレベルルール
├── .cursor/rules/
│   ├── mission-runner.mdc            # Cursor フル版
│   └── mission-runner-lite.mdc       # Cursor ライト版
├── examples/
│   └── _planning/                    # サンプル計画ファイル
├── README.md
├── LICENSE
└── CHANGELOG.md
```

## コントリビューション

コントリビューションを歓迎します！お気軽に Pull Request を提出してください。

1. リポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. Pull Request を作成

## ライセンス

このプロジェクトは MIT ライセンスの下でライセンスされています - 詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 謝辞

- [Anthropic](https://anthropic.com) の Claude Code
- [Cursor](https://cursor.sh) AI パワードエディタ
- AI エージェント研究コミュニティ
- すべてのコントリビューターとユーザー

---

<p align="center">
  <sub>自律 AI 開発のための PIR 方法論で構築</sub>
</p>

# Mission Runner

> **PIR (Plan-Iterate-Resolve) 方法論による自動マルチファイル開発**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-blueviolet)](https://claude.ai/code)
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
| **コンプライアンスチェック (Step 3.6)** | ビルド成功後の diff vs プラン検証;「コードは動くが意図と違う」というゴールドリフトを捕捉 |
| **Pre-Promise Audit (5 項目ゲート)** | promise 前のハードゲート、LLM が偽造できない 3 つの外部信号 (git diff / ビルド出力 / lesson ファイル) を含む |
| **Phase 5 Distill + クロスミッション・アーカイブ** | 各ミッションが 1-3 件の ≤150 文字 lesson を `~/.claude/mission-archive/{slug}/lessons/` に書き込み、後続ミッションが Phase 0 で Prior Lessons として glob |

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

Mission Runner は Claude Code 向けです。初期バージョンには Cursor 用ルール
ファイル（`.cursorrules` / `.cursor/rules/*.mdc`）が同梱されていましたが、
v1.1 プロトコル（Compliance Check / Pre-Promise Audit / Phase 5 Distill /
Prior Lessons glob）への追従が行われなかったため、本リポジトリから削除されました。

```bash
# リポジトリをクローン
git clone https://github.com/sputnicyoji/Claude-Skill-MissionRunner.git

# プロジェクトにコピー
mkdir -p .claude/skills/mission-runner
cp Claude-Skill-MissionRunner/SKILL.md .claude/skills/mission-runner/
cp -r Claude-Skill-MissionRunner/references .claude/skills/mission-runner/
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
├── タスクを解析
├── {project-slug} を決定                            (v1.1: クロスミッション名前空間)
├── ~/.claude/mission-archive/{slug}/lessons/ を glob (v1.1: 履歴 lesson のヒット)
├── _planning/ ディレクトリを作成
├── mission_plan.md を作成 (## Prior Lessons セクションを glob 結果から注入)
└── mission_notes.md を作成 (全標準セクション)

各反復:
├── Step 1: 決定前に読み取り (Prior Lessons + notes を読み、信頼度チェックへ供給)
├── Step 1.5: 信頼度チェック (4 次元)
├── Step 2: 実行 (1 タスクのみ; **この時点では [x] を付けない**)
├── Step 3: 検証 (コンパイル/lint/テスト)
│      ├── 失敗 -> Step 3.5
│      └── 成功 -> Step 3.6
├── Step 3.5: 自己反省 (検証失敗 または Step 3.6 escalate 時)
├── Step 3.6: コンプライアンスチェック (v1.1: diff vs プランのゴールドリフト検証)
│      ├── pass -> [x] を付与 + Step 4
│      ├── needs-revision -> [x] を付与せず、次反復で同タスクを継続
│      └── escalate -> Step 3.5
└── Step 4: チェックポイント
       ├── 未完了 -> 次反復へ
       └── 完了 (全 [x]) -> Phase 4 Debrief -> Phase 5 Distill -> 5 項目 Audit

Phase 4: Debrief        (Success Criteria の全 [x] を確認)
Phase 5: Distill        (v1.1: 1-3 件の ≤150 文字 lesson を archive に蒸留)
Pre-Promise Audit       (v1.1: 5 項目ハードゲート、うち 3 つは外部信号)
├── 5 項目全 pass -> <promise>Mission Accomplished</promise>
└── いずれか fail -> Partial Report + ## Audit Trail に追記
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
- AI エージェント研究コミュニティ
- すべてのコントリビューターとユーザー

---

<p align="center">
  <sub>自律 AI 開発のための PIR 方法論で構築</sub>
</p>

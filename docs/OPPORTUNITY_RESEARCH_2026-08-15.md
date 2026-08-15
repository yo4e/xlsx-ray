# Open-Source Software Opportunity Research

**需要が大きい一方で既存OSSに明確な穴がある課題の探索**

調査日: 2026年8月15日  
作成: **Manus AI**

## エグゼクティブ・サマリー

本調査では、GitHubリポジトリ・Issue、Reddit、Hacker News、Stack Overflow、パッケージレジストリの公開指標を横断し、**24件**の新規OSS候補を比較した。評価の主眼は新奇さではない。日常的に繰り返される手作業、壊れやすい自作スクリプト、導入の重いフレームワーク、または高価・外部送信型の商用サービスによって処理されている問題に置いた。

結論は明確である。最も有望なのは、**Excelワークブックの構造差分・数式リスク監査**と、**ローカル表データの照合・移行検証CLI**である。両者には反復する実務上の痛みがあり、既存OSSは保守停止、導入不全、または目的のずれを抱える。しかもMVPを読み取り専用・ローカル実行・GitHub Action連携に絞れば、1〜3人で構築でき、外部API費用も必要ない。[4] [15] [17] [19]

一方、当初3位だった「ゼロ設定データ契約CLI」は、Great Expectations、Pandera、Soda、Frictionlessがいずれも活発であることを深掘りで確認したため、**新規独立OSSとしてはNO**へ変更した。利用者の「重い」という不満は実在するが、もう一つのvalidatorを増やすより既存OSSへの初期導入プリセット・GitHub Action・失敗例レポートを貢献する方が合理的である。[1] [20]

> **最優先の一手:** 「Excelをバイナリからレビュー可能な成果物へ変える」読み取り専用CLIを作る。セルの差分だけでなく、数式、名前定義、外部リンク、保護、データ検証、VBA有無、影響下流セルを分類してPR上に出す。これはLLMラッパーではなく、表計算を安全に運用するための決定的なソフトウェア基盤である。

| 最終判定 | 推奨案件 | なぜ今か | MVPの核 | 運用コスト |
|---|---|---|---|---|
| **GO** | Excel構造差分・数式リスク監査 | Excelの意味的diff/CI監査は空白。ExceLintはアーカイブ、ExcelCompare/Git XLは保守・導入摩擦がある。 | OOXML解析、数式正規化、変更リスク、SARIF/Markdown/Action。 | **低**。ローカルCLIのみ。 |
| **GO** | ローカル表データ照合・移行検証CLI | 日次スナップショット比較が手組みのSQL/Pandas/sortへ分散。data-diffは保守終了。 | CSV/Parquet/DuckDB、鍵指定、正規化、追加/削除/変更、HTML証跡。 | **低**。外部接続なし。 |
| **NO（独立repo）** | ゼロ設定ファイル・データ契約CLI | 導入摩擦は本物だが、活発な強力OSSが多い。 | 既存OSSのbootstrap/Actionへ縮小。 | **低**だが差別化不足。 |

## 1. 調査方法と判定基準

### 1.1 情報源と限界

一次・準一次の公開情報を優先した。GitHubではリポジトリのアーカイブ状態、Stars、forks、open Issue、最新commit/releaseと個別Issueを確認した。利用者の痛みはReddit、Hacker News、Stack Overflow、GitHub Discussionから、商用依存は公式製品・プロジェクトの告知から拾った。パッケージの供給網への浸透度を補助的に見るため、npmとPyPI Stats APIも使用した。例えば取得時点の直近30日で、`xlsx`は48.1百万、`exceljs`は49.6百万、`@lingui/cli`は3.61百万downloads、`openpyxl`は346.3百万downloadsであった。ただし、これらはユニーク利用者数ではなく依存関係による取得も含むため、市場規模推計には用いていない。[22]

スター数も需要の十分条件ではない。そのため、**反復する利用者の困りごと**と、**既存競合の具体的な機能・保守・導入上の穴**が両方確認できる候補だけを上位に置いた。取得時点のGitHub数値は変動するスナップショットである。

### 1.2 採点式

各候補を5点満点で評価し、次式で100点に換算した。

\[
\text{総合点} = 20 \times (0.35D + 0.25G + 0.20E + 0.20S)
\]

| 記号 | 評価軸 | 判断内容 |
|---|---|---|
| **D** | 需要の強さ | 反復する困りごと、手作業・自作スクリプト、高価なSaaS、パッケージ利用、Issueの有無。 |
| **G** | 競合の弱さ | 保守停止、機能不足、導入摩擦、非ローカル、または対象workflowの欠落。強力で活発なOSSがある場合は低い。 |
| **E** | 開発容易性 | 1〜3人が約3か月で有用なMVPを出せるか。巨大コネクタ網・独自学習・常時クラウドは減点。 |
| **S** | OSS拡散性 | CLI、ライブラリ、GitHub Action、VS Code、ルール・テンプレート・AdapterのPRが自然に生じるか。 |

「継続コスト」はAPI利用料、インフラ、データ保持、保守対象の増え方を別に判定した。**ローカル実行、読み取り専用、外部送信なし**を基本とする案を優先している。

## 2. 需要が集中する構造的な空白

最も強い機会は、AIの文章生成そのものではなく、**ファイル・表・成果物の変更を安全に検証する工程**にあった。ExcelではSharePoint/OneDriveの版履歴が変更の意味を示さず、利用者はzip展開とpre-commitを回避策として挙げる。[4] データ照合では、日々のTSVスナップショットを比較して外部APIへ反映する人が、`sort`/`uniq`、Pandas/R、SQL、商用GUI、個別OSSに分散している。[15] 既存の代表OSS `data-diff` は2024年に保守終了となった。[2]

対照的に、単に「翻訳キーを検査する」「撤回論文を見つける」「OpenAPIの破壊変更を検査する」といった案は、新規プロジェクトの余地が薄い。前者は既存CLI・拡張が進み、後者はZoteroがプライバシーに配慮して文書・ライブラリの撤回論文を警告済みである。[6] [12] 需要が大きくても、**強く活発なOSSが主要用途を満たすならNO**という基準を守った。

## 3. 24候補の比較評価

以下では、各候補について、問題、利用者、需要根拠、競合と具体的不満、未解決の理由、差別化、MVP、実装・運用、普及可能性、OpenAI Codex for Open SourceのようなOSS支援プログラムへ説明しやすい社会的・技術的意義を圧縮して示す。判定欄の **GO/MAYBE/NO** は新規独立プロジェクトとしての判断である。

| # | 候補・具体的問題／誰が困るか | 需要根拠・主な競合・具体的な穴 | 差別化と最小MVP | 開発難易度・継続コスト | 獲得・コミュニティ・Stars/DL・支援プログラム適性 | 判定 |
|---:|---|---|---|---|---|---|
| 1 | **Excel構造差分・数式リスク監査**。予算、見積、運用モデルの共同編集者、監査人、開発者がバイナリ変更をレビューできない。 | SharePoint履歴が「何が変わったか」を示さず、zip展開hookが回避策になる。[4] ExceLintは数式エラー専用のアーカイブ済みアドイン。ExcelCompare/Git XLは差分中心で保守・導入問題が残る。[7] [17] | `sheetguard diff old.xlsx new.xlsx`。数式AST正規化、名前定義・外部リンク・データ検証・保護・VBAの差分、依存グラフ影響、SARIF/Markdown/JSON、Action。 | **中／低**。読み取り専用OOXML解析から開始しクラウド不要。 | Git driver、pre-commit、Action、VS Code拡張へ自然に展開。Excelテンプレート互換性のIssue・ルールPRが生じやすい。表計算を監査可能にする明快な公共価値。 | **GO** |
| 2 | **ローカル表データ照合・移行検証CLI**。CSV/TSV/Parquet/SQLite/DuckDBの同期・移行を担うデータ担当者が、更新・削除・型ずれを確信できない。 | 日次TSV比較がSQL/Pandas/sort/商用GUIへ分散。[15] `data-diff`は保守終了。[2] Daffは活発だが重複列・誤差分・SQLite CI等のIssueがある。[19] | `reconcile base.parquet new.csv --key id`。正規化、追加/削除/変更/重複/スキーマ破壊、HTML証跡、SQL/JSONL patch、Action。外部APIは直接更新しない。 | **中／低**。初期をファイル+DuckDBに限定。 | ETL、移行、研究・行政データ、個人金融の全てに横展開。Adapterと正規化ルールのPR、PyPI/npm/Actionが期待できる。検証可能な移行の安全性を上げる。 | **GO** |
| 3 | **ゼロ設定ファイル・データ契約CLI**。小規模チームがCSV/Excel/Parquetのnull、重複、列欠落を自作検査する。 | GE利用者はproject/suite/checkpointを煩雑とし、独自ライブラリへ流れると報告。[1] しかしGE/Pandera/Soda/Frictionlessは活発で広範。[20] | 新規validatorではなく、既存validatorのschema提案、失敗例表示、Action presetに限定。 | **中／低**。ただし互換性責務が拡大しやすい。 | 導入支援は広く刺さるが、単独repoのStarsより既存OSSへのPRが合理的。データ品質の初期障壁を下げる意義はある。 | **NO** |
| 4 | **PDFアクセシビリティ・トリアージと監査証跡**。大学、公共機関、出版社が多数PDFの修正優先度を決められない。 | 実務者はAcrobat Pro、CommonLook、Equidox等を併用し、Acrobat単独の限界・難PDFの学習負担を報告。[3] pdfa11yはCI対応の新興validatorで急速に充実している。[21] | 検査器を作り直さず、複数出力を集約し、修正可能性・公開期限・文書群別に優先順位化。安全なメタデータ修正案と監査台帳。 | **中／低〜中**。読み順・代替文品質の自動修正は対象外。 | 公共・教育リポジトリのAction、規則セット、言語別ガイドで貢献が期待できる。アクセシブルな公開情報を増やす意義は強い。 | **MAYBE** |
| 5 | **個人金融ファイル取込・照合アダプタ**。銀行連携が弱い地域のActual/Firefly/hledger利用者が、CSV/OFX/QIFを統合できない。 | 接続断・地域非対応のため手入力、手作業、Selenium/Python自作が発生する。[13] Actual、Firefly III、hledgerが競合。 | ダウンロード済みファイル限定で正規化、重複・内部振替候補、残高照合、各OSS向けexport。銀行ログイン・予測・助言は扱わない。 | **中／低**。銀行別parserの保守は必要。 | 国・銀行ごとの形式PRが生じる。投資助言でなく利用者データの可搬性・検証であり、健全なOSS説明が可能。 | **MAYBE** |
| 6 | **PDF表抽出の監査・レシピ化CLI**。研究者、監査、行政が表をCSV化した後、正しいセルを確認できない。 | Camelotは多数のパラメータを持ち、適用には学習と試行が必要。[11] Tabula、Camelot、pdfplumber、商用OCR/APIが競合。 | 既存抽出器をAdapter化し、YAMLレシピ、複数出力差分、低信頼セルと元PDF座標へのリンク、HTMLレビューを出す。 | **中〜高／低**。テキストPDFから開始し独自OCR/LLMは持たない。 | 分野別レシピとサンプルPDFベンチマークが貢献を呼ぶ。曖昧な抽出を監査可能な工程にする価値。 | **MAYBE** |
| 7 | **データエクスポートの来歴・スキーマ証跡生成**。引き渡すCSVの作成元、ハッシュ、型、行数、フィルタを後で説明できない。 | 移行・複製で「正しくコピーされたか」を確認する需要はdata-diffと日次照合の事例に表れる。[2] [15] dbt・カタログは大規模基盤寄り。 | `datareceipt export.csv --source query.sql`でschema、統計、sha256、入力・ツール版をJSON-LD/Markdown化し、前版と比較。 | **中／低**。 | ETL、研究データ、行政データ、個人金融で再利用され、format AdapterのPRを誘発。検証可能なデータ共有として説明しやすい。 | **MAYBE** |
| 8 | **GitHub Actionsテスト結果の静的履歴ダッシュボード**。小中規模repoが失敗テスト・flake・再発をログから追えない。 | GitHub公式Discussionは専用UIなし、annotation 50件上限、静的要約を具体的に指摘する。[14] dorny/test-reporter、ctrf、Allure、SaaS CIが競合。 | JUnit/TRX/pytestを収集し、失敗シグネチャを決定的にクラスタリング。artifact/gh-pagesで外部DBなしの時系列HTML。 | **中／低**。 | Action Marketplaceで試されやすく、parser/UIテーマ/CI対応のPRが期待できる。開発者のデバッグ時間を下げる非LLM基盤。 | **MAYBE** |
| 9 | **共有前ログ匿名化・最小再現バンドルCLI**。Issue・サポートでログ、設定、HARを貼る開発者が秘密/PIIを漏らす。 | local-firstが支持される一方、PII、漏れ/過剰マスク、カスタマイズが課題。[5] Presidio、Gitleaks、ShareClean等が競合。 | JSON/YAML/.env/HARを文脈付き処理し、置換理由・不確実性をレビュー。ローカル暗号化mapとsanitized bundle/manifestを生成。 | **中／低**。万能PII検知や不透明なAI必須化を避ける。 | pattern/format AdapterのPR、CLI/pre-commit/VS Code拡張に向く。安全なOSS協働という支援プログラム適性が高い。 | **MAYBE** |
| 10 | **字幕ファイルQA as code**。教育、ローカライズ、配信チームが自動文字起こし後の読速・分割・改行を目視修正する。 | 実務者はセグメンテーションと改行が最も時間を要すと述べる。[9] Subtitle Edit、Caption Inspector、Tero Subtitlerが競合。 | SRT/WebVTT/TTMLのCPS/WPM、行数、表示時間、重複、禁則、話者名を検査し、HTMLタイムライン/SARIFを出す。 | **中／低**。字幕編集器・文字起こし器は再実装しない。 | ルールセットとActionが自然な配布形態。アクセシブルな教育・動画成果物の品質保証として説明可能。 | **MAYBE** |
| 11 | **Excel対応・テンプレート版管理CSV取込SDK**。SaaSの利用者アップロードが毎回異なる。 | 「ほぼすべての案件」でCSV importerが必要という実装者の証言がある。[8] Flatfile、OneSchema、HelloCSV、YoBulkが競合。 | CSV-onlyではなく、XLSX複数シート、保存済みmapping、テンプレート差分、ローカル検証に狭める。 | **中／低**。 | npm/Web Componentとして広がるが競合密度が高い。非LLMの安全なデータ取込としては明快。 | **MAYBE（条件付き）** |
| 12 | **コードと文書の決定的リンク・ドリフト検査**。README/APIガイドのCLI例、設定名、参照先が実装変更で古くなる。 | 文書ドリフトはレビューで補われがち。Vale、markdownlint、doctest、OpenAPI生成、LLM型SaaSが競合。 | 自然言語の意味比較ではなく、CLI例・設定キー・URL・コードsymbolの参照整合性に限定する。 | **中／低**。 | Docs Actionとして導入しやすいが既存linterとの差別化が難しい。決定的ドキュメント品質としては説明可能。 | **MAYBE（低優先）** |
| 13 | **壊れたリンクのアーカイブ候補・置換PR生成**。長期文書のlink rotを「失敗通知」だけで終わらせたくない。 | Lycheeは活発な高速リンクチェッカーであり、3,800超Starsの強い競合。[23] | archive/canonical候補の提案は誤検出、著作権、URL永続性の判断が難しく、Lychee拡張で済む可能性が高い。 | **中／低**。 | docs Actionの拡散余地はあるが新規repoの必然性が弱い。 | **NO寄り** |
| 14 | **Jupyter再現性ゲート**。共有ノートブックがセル順、隠れ状態、環境差でCIを通らない。 | アドホック実行順は再現性と根本的に衝突し、scratch化・nbconvert化が回避策。[10] nbval、nbdime、papermill、Ploomber、Marimoが競合。 | clean kernel、environment/data fingerprint、許容出力diff、実行時間回帰を一体化したActionに狭める。 | **中〜高／低**。 | 研究・教育repoの導入は見込めるがPython依存保守が重い。再現可能な計算研究としての意義は高い。 | **MAYBE** |
| 15 | **研究データ公開パッケージ検証**。論文付属CSV・コード・READMEが公開後に再利用可能か確認できない。 | フォーマット・抽出・検証の手作業はS011に表れ、RO-Crate、Frictionless、DataLad、FAIR系が競合。 | `research-package check`でREADME、license、citation、checksum、schema、環境lock、再実行コマンドを検査する。 | **中／低**。 | 学術リポジトリ・ジャーナルtemplate・ルールPRに向くが標準団体との整合が必要。再現可能な科学の支援として明快。 | **MAYBE（探索）** |
| 16 | **スプレッドシート不変条件テスト**。重要モデルの入力/数式変更時に出力妥当性をテストできない。 | Excel版管理の痛みとExceLint停止が背景。[4] [7] FormulaMapや商用監査が競合。 | YAMLで許容範囲・単調性・シナリオを記述してheadless計算する。ただし01のpluginとして統合する方がよい。 | **中〜高／中**。計算互換性が難点。 | 会計・モデル利用者の需要は強いがテスト定義教育が必要。表計算の検証可能性には資する。 | **統合候補** |
| 17 | **CSV数式インジェクション検査・安全化**。CSV exportをExcelで開く利用者を数式評価リスクから守る。 | CSV/Excel処理ライブラリは大きな供給網を持つ。[22] 多くは手製escapeで対応。 | exportコードを検査し、安全化方針とfixtureを出すCLI/ESLint/Action。 | **低／低**。 | security rule・言語bindingに向くが機能が狭く単独Starsは限定的。安全なデータ出力として説明は容易。 | **ニッチMAYBE** |
| 18 | **PDF/HTML視覚回帰テスト**。請求書、規制文書、公開PDFのレイアウト崩れを検出する。 | Playwright、BackstopJS、reg-suit、diff-pdf、Percy等が強い。 | 主要用途を既存OSSが満たす。PDFレンダリング正規化は既存へのPRでよい。 | **中／低**。 | 新規repoより既存貢献が合理的。 | **NO** |
| 19 | **i18nカタログ静的解析CLI**。欠落・未使用・placeholder不整合を検出する。 | next-intl側は必要性を認めつつ、eloqnt/cliの提供開始を案内。i18n Allyも存在し、Lingui CLIも大規模利用。[6] [22] | 動的キーの偽陽性もあり、強い既存ツールがある。 | **低／低**。 | 新規よりAdapter・誤検出抑制のPRが望ましい。 | **NO** |
| 20 | **撤回論文・引用リスト検査**。研究者が撤回済み文献を誤引用しないようにする。 | ZoteroはRetraction Watchと連携し、文書・ライブラリを自動検査して引用時にも警告する。[12] | DOI/PMID外の補完余地はあるが、主要課題は既に満たされる。 | **低／低**。 | 新規Starsは見込みにくく、Zotero連携の改善が妥当。 | **NO** |
| 21 | **.env設定スキーマ・環境差分ゲート**。設定漏れ、staging/prod差分、不要設定を防ぐ。 | dotenv-linter、env-schema、Zod、Infisical/Dopplerが競合。 | `.env.example`、Compose、K8s、Actionsを横断して必須/未使用/型/secret参照の差分に狭める。 | **低〜中／低**。 | repo templateから普及しうるが競合との差は狭い。安全な設定管理として説明可能。 | **MAYBE（低優先）** |
| 22 | **OpenAPI互換性・破壊変更ゲート**。API変更がクライアントを壊さないようにする。 | oasdiff、Optic、Schemathesis、Pact、Specmaticが強い。 | 活発OSSが主要機能を満たす。 | **中／低**。 | 新規よりreport UXやfixture改善のPRが妥当。 | **NO** |
| 23 | **供給網provenance証跡パック**。小規模repoがSBOM、署名、来歴を添付しやすくする。 | in-toto、SLSA、Sigstore、OSV-Scanner、Syft等が強い。 | 仕様・信頼基盤が重く、薄いラッパー化する。 | **高／中**。 | 既存の安全なpreset/Action templateに限れば価値がある。 | **NO** |
| 24 | **生成物・Issue添付物向け秘密情報スキャナ**。PDF、HTML、log、zipなどソース外の成果物に含まれる秘密を出荷前に見つける。 | ログ共有前の匿名化需要が確認できる。[5] Gitleaks/TruffleHogはrepo/履歴中心。 | archive安全展開、MIME別テキスト化、偽陽性を扱い、位置付きSARIF/allowlistを出す。 | **中／低**。 | security Actionとして試されやすい。公開成果物の秘密漏えい防止という支援適性は高い。 | **ニッチMAYBE** |

## 4. 上位10件ランキング

この順位は深掘り前の同一式による比較順位である。#3は総合点が高いが、競合リポジトリ深掘り後に最終判定をNOへ更新した。これは「需要の強さ」だけで参入判断をしないための意図的な補正である。

| 順位 | 候補 | 総合点 | D | G | E | S | 参入時に必ず守る境界 |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | Excel構造差分・数式リスク監査 | **96** | 5 | 5 | 4 | 5 | 計算器・共同編集製品でなく、読み取り専用の意味的監査。 |
| 2 | ローカル表データ照合・移行検証CLI | **96** | 5 | 5 | 4 | 5 | 全DWHでなくCSV/Parquet/DuckDBと証跡に集中。 |
| 3 | ゼロ設定ファイル・データ契約CLI | **86** | 5 | 3 | 4 | 5 | **深掘り後NO**。新規validatorを作らず既存OSSへ貢献。 |
| 4 | PDFアクセシビリティ・トリアージと監査証跡 | **80** | 4 | 4 | 4 | 4 | validator再実装でなく大量文書の優先順位・監査台帳。 |
| 5 | 個人金融ファイル取込・照合アダプタ | **80** | 4 | 4 | 4 | 4 | 銀行ログイン・投資助言・SaaS化を行わない。 |
| 6 | PDF表抽出の監査・レシピ化CLI | **76** | 4 | 4 | 3 | 4 | OCR/独自VLMでなく既存抽出器の監査層。 |
| 7 | データエクスポート来歴・スキーマ証跡生成 | **76** | 4 | 4 | 3 | 4 | カタログ基盤でなく持ち運べるreceipt。 |
| 8 | GitHub Actionsテスト結果の静的履歴ダッシュボード | **75** | 4 | 3 | 4 | 4 | GitHub UI代替でなくSaaS不要の履歴artifact。 |
| 9 | 共有前ログ匿名化・最小再現バンドルCLI | **75** | 4 | 3 | 4 | 4 | 万能PII保証でなく決定的・レビュー可能な処理。 |
| 10 | 字幕ファイルQA as code | **73** | 3 | 4 | 4 | 4 | 字幕編集器でなく規約検査・CI。 |

## 5. 上位3件の競合リポジトリ深掘りと最終判定

### 5.1 #1 Excel構造差分・数式リスク監査 — **GO**

| 競合 | 取得時点の状態 | 役割 | 新規OSSに残る穴 |
|---|---|---|---|
| [ExceLint](https://github.com/ExceLint/ExceLint) | 74 Stars。2021年からアーカイブ。最終commit 2019-09-14、最終release 2019-03-03。 | Excelアドインで数式エラーを検出。 | クロスプラットフォームCLI、Git/PR監査、変更影響の説明がない。 |
| [ExcelCompare](https://github.com/na-ka-na/ExcelCompare) | 856 Stars、23 open issues。最新commit 2022-04-22、release系列は2015年、license指定なし。 | xls/xlsx/xlsm/odsの差分CLI/API。 | 2026年のCygwin絶対パス問題、unified diff不良、古い大きなODSのhang、セル型エラー、ライセンス要望が未解決。[17] |
| [Git XL](https://github.com/xltrail/git-xl) | 604 Stars、27 open issues。最新release/commitは2023-02-19。 | VBAをGit diffで管理。 | 2026年にも古い依存・installer/build不全、macOS対応要望が残る。workbook全体のリスク監査を意図しない。[18] |

**GOの理由。** 既存候補には利用需要のシグナルがありながら、数式、名前定義、外部リンク、データ検証、保護、VBA存在、依存グラフをまとめて「何が危険か」とPRに示すツールが見当たらない。これは構文diffの改善ではなく、表計算をコード同様にレビュー可能にする新しい操作単位である。

**MVP仕様。** `.xlsx`/`.xlsm`二版を入力に、①シート追加削除、②セル値・表示式、③相対参照へ正規化した数式AST、④名前定義、⑤外部リンク、⑥データ検証、⑦保護、⑧VBA有無を抽出する。変更セルから下流依存を数え、`low/medium/high`のルールベース危険度を付け、Markdown/JSON/SARIFを出す。`--fail-on high`があればGitHub Actionとして十分に価値を持つ。

**非目標。** Excel/LibreOfficeの完全再計算、マクロ実行、数式の数学的正しさの証明、クラウド共同編集の置換はMVPから除く。読み取り専用と決定的出力を守ることで、安全性と保守性を確保する。

### 5.2 #2 ローカル表データ照合・移行検証CLI — **GO**

| 競合 | 取得時点の状態 | 役割 | 新規OSSに残る穴 |
|---|---|---|---|
| [datafold/data-diff](https://github.com/datafold/data-diff) | 2,988 Stars、313 forks。2024-05-17にアーカイブ。最終commitが「Sunsetting open source data-diff」。 | DB内・横断の高速table diff。 | 代表OSSの継続保守が止まり、後継はCloudへ誘導される。[2] |
| [Daff](https://github.com/paulfitz/daff) | 922 Stars、47 open issues。v1.4.2は2025-05-04。 | 汎用table diff・patch。 | 重複列、結果誤り、SQLiteの`--fail-if-diff`、表計算対応などのIssueが残る。鍵推定、正規化診断、移行証跡は主目的でない。[19] |
| [diff-table](https://github.com/chop-dbhi/diff-table) | 最終release 2018-11-18、最終commit 2019-10-30。 | 区切りファイル/Postgresのストリーミング比較。 | Parquet/DuckDB/Actionの導線がなく保守停止。 |
| [dataCompareR](https://github.com/capitalone/dataCompareR) | 最終release 2020-05-04。 | Rで列・型・行を比較。 | 言語非依存の操作、証跡、patch workflowではない。 |

**GOの理由。** データ比較自体には競合があるが、利用者が実際に必要とするのは「差がある」と知ることではなく、**どの鍵で、どの正規化前提で、何が追加・削除・変更・重複だったかを再現可能に残すこと**である。data-diffの保守終了と、SQL/Pandas/UNIXコマンドへ分散する運用は、ファイル中心の明確な空白を示す。[2] [15]

**MVP仕様。** CSV/TSV/Parquet/SQLite/DuckDBに限定する。`reconcile baseline new --key customer_id --rules rules.yml`で、列・行数・型を先に診断し、主キー候補は提案するが自動決定しない。日時、空白、数値精度、null、大小文字をルールで正規化してから、追加・削除・変更・重複・スキーマ破壊を分類する。HTML/JSON/Markdownの証跡、行例、`csv/sql/jsonl` patchを出すが、外部APIを直接更新しない。

**非目標。** Snowflake/BigQuery/Databricks、任意巨大表の分散比較、複雑なSCDの自動適用、外部コネクタ網を最初から対象にしない。標準入出力、DuckDB、Parquet、GitHub Actionを先に完成させ、後のAdapterをPRで受け入れる設計にする。

### 5.3 #3 ゼロ設定ファイル・データ契約CLI — **NO（独立repoとして）**

| 競合 | 取得時点の状態 | 判定への含意 |
|---|---|---|
| [Great Expectations](https://github.com/fivetran/great_expectations) | 11,713 Stars。v1.20.0を2026-08-07にrelease、最終commit 2026-08-14。 | S001の複雑さは事実だが、活発な巨大OSSを再実装する根拠にならない。 |
| [Pandera](https://github.com/unionai-oss/pandera) | 4,431 Stars。v0.32.1を2026-06-29にreleaseし、PyArrowを2026-08に強化。 | Pandas/Polars/PyArrow方向のschema/testは強い。 |
| [Soda Core](https://github.com/sodadata/soda-core) | 2026-08-13にv4.21.0をrelease。 | コネクタ・Airflow・data sourceの課題を活発に扱う。 |
| [Frictionless Python](https://github.com/frictionlessdata/frictionless-py) | v5.19.0を2026-04にreleaseし、2026-07も修正。 | ファイル中心のschema検証まで既存OSSが担当する。 |

**NOの理由。** 「ファイルを読むとschemaを推定してCIで検証する」は魅力的だが、すでに強い4系統のOSSがその近傍を広く覆う。利用者がGEを重いと感じることは、新規ツールが設定・例外・互換性責任を隠せることを意味しない。新規validatorはかえって選択肢を増やし、品質保証を断片化する。

もし着手するなら、新規プロジェクトでなく、①Frictionless/Pandera/GEの間で簡易YAMLを変換するinitializer、②失敗行と修正例をGitHub Checksで見せるAction preset、③CSV/Excel/Parquetを判別して既存validatorへ安全に渡すbootstrapを既存コミュニティへPRする。これは有益だが、**新規OSS候補としては採択しない**。

## 6. 実装・検証の推奨順序

### 第一選択: Excel構造差分・数式リスク監査

最初の4週間では、正確なセル再計算を避け、OOXMLの安定した静的構造だけを対象にする。Week 1でworkbook抽出とcanonical JSON、Week 2で二版diffとMarkdown、Week 3で数式参照の正規化と影響下流集計、Week 4でAction/SARIFを完成させる。公開ベンチマークには、予算テンプレート、貸借/損益モデル、運用チェックリストなど**架空・非機密**のworkbook二版を用い、変更が危険度として説明される様子を示す。

初期の成功指標は、Starsよりも、①GitHub Actionのworkflow導入数、②`.gitattributes`/pre-commitの採用、③「この変更を見落とさずに済んだ」というIssue例、④Excel形式・数式関数の互換性PRである。PyPIとGitHub Actionの二重配布を基本にし、Node wrapperは後回しでよい。

### 第二選択: ローカル表データ照合・移行検証CLI

最初の4週間ではCSV/Parquet/DuckDBだけを扱う。鍵は明示指定を必須とし、推定機能は候補の表示にとどめる。正規化は文字列trim、case、日時、decimal、nullだけに限定し、すべてを`rules.yml`へ保存する。出力は、機械向けJSON、PR向けMarkdown、監査向け単一HTMLに絞る。巨大データ・クラウドDB・直接更新を先送りすれば、オフライン性、再現性、安全性を維持できる。

成功指標は、①migration/ETLのテンプレートPR、②Daff/data-diffからの移行Issue、③new/deleted/changedを安全に説明できた利用例、④規格化ルール・file adapterのコミュニティ貢献である。データを送信しないことは、SaaSとの差別化であると同時に、継続費用の抑制でもある。

## 7. 最終提言

**新規OSSを一つだけ開始するなら、Excel構造差分・数式リスク監査を選ぶべきである。** 需要は非技術職を含む広いExcel利用に根ざし、表計算のバイナリ性と意味的レビュー不能という具体的な痛みがある。既存競合は停止、狭い対象、または導入不全という明確な穴を持つ。MVPもローカル読み取り専用で完結し、外部API・モデル推論・ユーザーデータ保持を必要としない。

**次点はローカル表データ照合・移行検証CLI**である。こちらは開発者・データ担当者に絞られる一方、GitHub Action、CLI、ライブラリ、DataFrame/SQL出力と拡張経路が多い。強い既存ライブラリDaffを敵にせず、鍵・正規化・証跡・移行レビューというworkflow層を担うことが成功条件である。

PDFアクセシビリティ、個人金融ファイル取込、PDF表抽出監査、字幕QAは**MAYBE**として価値がある。ただし、前者は新興validatorの進展を踏まえてworkflowに限定し、個人金融は銀行接続や助言に踏み込まず、PDF表抽出はAI/OCRサービスの再実装を避け、字幕は編集器でなくCIに徹する必要がある。[13] [21]

## 参考文献

[1]: https://www.reddit.com/r/dataengineering/comments/z90wtm/great_expectations_is_annoyingly_cumbersome/ "Great Expectations is annoyingly cumbersome — Reddit"
[2]: https://www.datafold.com/blog/open-source-data-diff/ "Open source data-diff — Datafold"
[3]: https://www.reddit.com/r/accessibility/comments/1jb6tl7/what_software_do_you_use_for_pdf_accessibility/ "What software do you use for PDF accessibility? — Reddit"
[4]: https://www.reddit.com/r/excel/comments/1o3woav/version_control_for_excel_has_anyone_actually/ "Version control for Excel — has anyone actually solved this? — Reddit"
[5]: https://www.reddit.com/r/SideProject/comments/1uk75ln/shareclean_a_localfirst_cli_to_redact_sensitive/ "ShareClean: a local-first CLI to redact sensitive info from logs — Reddit"
[6]: https://github.com/amannn/next-intl/discussions/503 "CLI to find unused/missing translations — next-intl Discussion"
[7]: https://github.com/ExceLint/ExceLint "ExceLint repository"
[8]: https://www.reddit.com/r/webdev/comments/1k3ewkr/built_a_free_open_source_flatfile_alternative/ "Built a free, open source Flatfile alternative — Reddit"
[9]: https://www.reddit.com/r/localization/comments/1u0uev0/what_actually_takes_the_most_time_in_subtitle/ "What actually takes the most time in subtitle editing after transcription? — Reddit"
[10]: https://www.reddit.com/r/datascience/comments/rbny6v/notebooks_in_ci_how_are_you_handling_this/ "notebooks in CI — how are you handling this? — Reddit"
[11]: https://stackoverflow.com/questions/61387304/tabula-vs-camelot-for-table-extraction-from-pdf "tabula vs camelot for table extraction from PDF — Stack Overflow"
[12]: https://www.zotero.org/blog/retracted-item-notifications/ "Retracted item notifications with Retraction Watch integration — Zotero"
[13]: https://www.reddit.com/r/actualbudgeting/comments/1pztknd/self_hosted_actual_users_how_are_you_importing/ "Self hosted Actual users, how are you importing your transactions? — Reddit"
[14]: https://github.com/orgs/community/discussions/163123 "Native Test Results Dashboard for GitHub Actions — GitHub Community"
[15]: https://news.ycombinator.com/item?id=17924798 "Ask HN: Data diff tool for tabular data? — Hacker News"
[16]: https://github.com/na-ka-na/ExcelCompare "ExcelCompare repository"
[17]: https://github.com/na-ka-na/ExcelCompare/issues/69 "ExcelCompare Issue #69"; https://github.com/na-ka-na/ExcelCompare/issues/67 "ExcelCompare Issue #67"; https://github.com/na-ka-na/ExcelCompare/issues/45 "ExcelCompare Issue #45"
[18]: https://github.com/xltrail/git-xl/issues/89 "Git XL Issue #89"; https://github.com/xltrail/git-xl/issues/86 "Git XL Issue #86"
[19]: https://github.com/paulfitz/daff/issues/216 "Daff Issue #216"; https://github.com/paulfitz/daff/issues/215 "Daff Issue #215"; https://github.com/paulfitz/daff/issues/212 "Daff Issue #212"; https://github.com/paulfitz/daff/issues/206 "Daff Issue #206"
[20]: https://github.com/fivetran/great_expectations "Great Expectations repository"; https://github.com/unionai-oss/pandera "Pandera repository"; https://github.com/sodadata/soda-core "Soda Core repository"; https://github.com/frictionlessdata/frictionless-py "Frictionless Python repository"
[21]: https://github.com/speedata/pdfa11y "pdfa11y repository"
[22]: https://api.npmjs.org/downloads/point/last-month/xlsx "npm downloads: xlsx"; https://api.npmjs.org/downloads/point/last-month/exceljs "npm downloads: exceljs"; https://api.npmjs.org/downloads/point/last-month/%40lingui%2Fcli "npm downloads: @lingui/cli"; https://pypistats.org/api/packages/openpyxl/recent "PyPI Stats: openpyxl"
[23]: https://github.com/lycheeverse/lychee "Lychee repository"

## 付録: 再現可能な調査素材

添付の `candidate_ranked.csv` は24件の生スコア、`sources.md` は取得URL・観察メモ、`research_method.md` は重みと除外方針を含む。数字はすべて2026年8月15日取得時点のスナップショットである。

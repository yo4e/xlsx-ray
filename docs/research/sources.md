# Source Log

## S001 — 軽量なローカルデータ品質検証の需要

- URL: https://www.reddit.com/r/dataengineering/comments/z90wtm/great_expectations_is_annoyingly_cumbersome/
- 種別: r/dataengineering の利用者討論（2022年）
- 観察: 投稿者は、基本的なCSV/データフレーム検証だけのために project / suite / checkpoint / data source の作成が必要だと批判した。コメントにも「設定に何時間もかかった」「聞いたチームは結局独自検証ライブラリを書いた」「単純なデータ検証を実現するための導入摩擦が大きい」との反復的な証言がある。
- 機会への示唆: これは『大規模DWHのデータオブザーバビリティ』を再実装する余地ではなく、CSV/Excel/ParquetとPandas/Polarsの小〜中規模チームを対象に、ゼロ設定・推論可能・CI対応のデータ契約/差分レポートを提供する余地を示す。Pandera等のライブラリは代替だが、非Pythonユーザー向けCLIと変更可能な修復提案・GitHub Actionが不足候補である。

## S002 — OSSデータ差分ツールの保守終了

URL: https://www.datafold.com/blog/open-source-data-diff/

Datafoldは2024年5月17日付で、OSS版 `data-diff` を「もはや積極的にサポートまたは開発しない」と明示し、データベース内・データベース横断の差分比較を継続する利用者にはDatafold Cloudの無料トライアルを案内している。比較対象が日々ずれるデータ移行・レプリケーションの検証という需要は同社の製品説明でも明示される一方、従来の代表OSSの保守は止まっている。これは、接続情報を外部へ送らないローカルCLI、CSV/Parquet/SQLiteから始め、PR上の要約と検証証跡を出せる後継の機会を示す。ただし、企業DWH全般をMVPに含めると接続・スケールの保守負担が高いため、初期対象をファイルとDuckDBに限定する必要がある。

## S003 — PDFアクセシビリティは検査・修正ともに断片化

URL: https://www.reddit.com/r/accessibility/comments/1jb6tl7/what_software_do_you_use_for_pdf_accessibility/

2025年のアクセシビリティ実務者の討論では、Adobe Acrobat Pro、CommonLook、Equidoxなど複数の製品が候補になり、Acrobatのアクセシビリティ機能は有料であること、Acrobat単独では完全な適合に不十分な場合があること、制御不能な「劣悪な」PDFには学習曲線のある専用製品が必要なことが述べられている。OSS機会は、完全自動のPDF修復を主張することではない。既存のveraPDF/PAC等の検査器を統合し、文書群をトリアージして『自動で安全に直せるメタデータ／見出し候補』と『人が読む順序等を確認すべき項目』を分離したローカルバッチCLIと、修正前後の監査証跡を出すことにある。

## S004 — Excelは広く使われるが、意味のある変更履歴がない

URL: https://www.reddit.com/r/excel/comments/1o3woav/version_control_for_excel_has_anyone_actually/

複数共同編集者の複雑なExcelワークブックについて、投稿者はSharePoint/OneDriveの自動版管理が「何が変わったか分からない」連番のファイルを大量に生むと報告した。回答者は、数式とデータが同じバイナリに混在することを根本的な版管理障害と説明し、zipを展開して内部を追跡するpre-commit hookという技術的な回避策も挙げている。一方でExcelは「すでに全社PCにあり、設定と追加ライセンスが不要で、ローカル上書きができる」ため代替しにくいとされる。差別化機会はExcelを置き換えることではなく、`.xlsx`をローカルで構造化比較し、数式・参照・名前定義・入力値・外部リンク・保護設定の意味別に差分とリスクを可視化し、Git pre-commit / GitHub Actionで失敗させるOSSにある。

## S005 — 外部共有前のログ匿名化はローカル実行が支持されるが、品質課題が残る

URL: https://www.reddit.com/r/SideProject/comments/1uk75ln/shareclean_a_localfirst_cli_to_redact_sensitive/

2026年のShareClean紹介に対する実務的な反応では、「ログを匿名化APIへ流したくないためlocal-firstが正しい」と評価される一方、PII対応、検出漏れと過剰マスクのトレードオフ、利用者定義の置換方法が追加要望となった。作者自身も当時は決定的パターン照合が中心でPII対応を今後検討すると説明している。これは単なる正規表現マスクCLIはすでに生まれやすいことを示すため、独立候補としては中位に留める。新規性は、構造化ログ/`.env`/YAML/HTTP HARを文脈付きで解析し、変更箇所と検出不確実性をレビュー可能にして、匿名化後に安全な最小再現バンドルを生成する点に限定すべきである。

## S006 — i18nカタログ検査は需要があるが、単体での参入余地は縮小

URL: https://github.com/amannn/next-intl/discussions/503

next-intlの公式Discussionでは、未使用・欠落翻訳キーを静的解析するCLI/ESLint統合が求められ、利用者が自作スクリプトを共有している。これは需要の実証である。しかしメンテナは2026年8月10日に `eloqnt/cli` で提供開始済みと更新し、i18n Allyにも利用状況レポートがあると述べた。同スレッドでは動的キー等による偽陽性という限界も示されるが、鍵の同期・未使用検出のみを行う新規OSSは差別化が弱い。後の候補群ではNO（またはExcel/PDF等を横断する翻訳「成果物」QAの付帯機能）として扱う。

## S007 — ExceLintは数式異常を検出するが、保守停止・Windows/Excelアドイン型

URL: https://github.com/excelint/excelint

ExceLintは数式エラーを自動検出するMicrosoft Excelアドインであり、研究論文に基づく実装である。しかしリポジトリは2021年6月8日にアーカイブされ、現在読み取り専用である。閲覧時点の表示ではStar 74、Issue 1であり、主要配布形態はクロスプラットフォームのCLIやGitHub Actionではない。したがって、新規案の目的を「数式異常検出アルゴリズムの再発明」にせず、xlsx/xlsmの構造差分、式依存グラフの変更リスク、テスト用の不変条件、PRアノテーションを備えるクロスプラットフォーム監査CLIに置くなら、明確な競合の穴がある。

## S008 — 埋め込みCSVインポーターは需要が強いが、競合OSSが急増

URL: https://www.reddit.com/r/webdev/comments/1k3ewkr/built_a_free_open_source_flatfile_alternative/

HelloCSVの開発者は、受託開発の「ほぼすべてのプロジェクト」でCSVインポーターが必要になり、入力データの正しさ、アップロード前の利用者による修正、重複・誤データの事後修正負担、整形の事前確認という共通課題があると報告する。同OSSは列マッピング、検証、変換、プレビュー、確認のUIを100%フロントエンド・99KBで提供し、Flatfile/OneSchemaのようなリモート送信型の代替と差別化している。これは市場需要の強い証拠であると同時に、CSVだけのインポーターはすでに新規OSSが複数出ている警告でもある。採用候補に残すなら、Excel/複数シート/テンプレート版管理/CSV方言自動診断/アクセシビリティに範囲を絞ったSDKまたはサーバーレス処理で明確に勝つ必要がある。

## S009 — 字幕生成後の品質保証は依然として手作業が多い

URL: https://www.reddit.com/r/localization/comments/1u0uev0/what_actually_takes_the_most_time_in_subtitle/

ローカライゼーション実務者は、良好な文字起こしがあっても字幕のセグメンテーションと改行が最も時間を要し、悪い区切りは読みにくさにつながると説明する。Caption InspectorやSubtitle Edit等は存在するため、字幕編集アプリ全体の新規開発は競争が強い。一方、CIでSRT/WebVTT/TTMLの読速（CPS/WPM）、表示時間、重複、禁則文字、話者ラベル整合性、カット付近のcueを機械検査し、HTMLのレビュー用タイムラインを成果物化する「字幕QA as code」は、ローカルのみで構築でき、動画・教育・ローカライズリポジトリへの付加価値として差別化可能である。

## S010 — Jupyterノートブックは共有・教育では有用だが、CIでは実行順序が根本障害

URL: https://www.reddit.com/r/datascience/comments/rbny6v/notebooks_in_ci_how_are_you_handling_this/

データサイエンス実務者は、ノートブックのアドホックなセル実行順序が再現性と根本的に衝突すると説明する。回答に挙がる回避策は、明確なフローを持つノートブックだけを共有し、`nbconvert`でPythonへ変換してテストするか、探索的ノートブックをGit管理外のscratchディレクトリに置くことである。これはCIでの再現性検証に未解決の実務負担があることを示すが、nbval、nbdime、papermill等が存在する。新規案の価値は実行エンジンではなく、kernelをクリーンにした実行、環境/データ指紋、許容された出力差分、実行時間の回帰を一つのGitHub ActionとHTML証跡にまとめる『Notebook reproducibility gate』に絞る場合のみ残る。

## S011 — PDF表抽出はOSSがあるが、正確性の検証と設定探索が残る

URL: https://stackoverflow.com/questions/61387304/tabula-vs-camelot-for-table-extraction-from-pdf

Stack Overflowの比較では、Camelotは抽出を改善する多数のパラメータを備えるが、それを適用するには学習と「さまざまな試行」が必要と説明されている。これはライブラリ不在の問題ではなく、抽出設定を再利用可能にし、セルと原PDFの位置を対応付け、低信頼行だけを人間が確認できるようにする監査層の不足である。MVPは表抽出器そのものではなく、Camelot/Tabula/pdfplumberの出力を同一スキーマで比較し、差異・信頼度・ページ画像へのリンクを含むレビューHTMLとYAML抽出レシピを生成するCLIにすべきである。スキャンPDFや複雑帳票を完全自動で扱う範囲は高コスト化するため、初期版では対象外とする。

## S012 — 撤回論文の検出単体はZoteroがすでに満たすためNO

URL: https://www.zotero.org/blog/retracted-item-notifications/

ZoteroはRetraction Watchとの連携により、ライブラリと文書中の撤回済み研究を自動検査し、項目一覧と引用時に警告する。DOI/PMIDに限定されるものの、Retraction Watchデータのおよそ4分の3をカバーすると明記し、同期やライブラリ内容の送信を不要にするプライバシー設計も説明している。このため「BibTeX/Zoteroの撤回論文チェッカー」単体は需要はあるが、強力な活発OSSに対する差別化が乏しく、新規候補としてNOとする。

## S013 — 個人金融の取引取得は接続不安定・手入力・自作自動化に分裂

URL: https://www.reddit.com/r/actualbudgeting/comments/1pztknd/self_hosted_actual_users_how_are_you_importing/

Actual Budget利用者の議論では、銀行接続サービスが地域・金融機関によって切断し再接続が必要、年間15ドルのサービスでも機関依存、複数口座のCSV/OFX/QIFを週次または月次に手でインポート、毎日5分かけて6口座を照合する、といった運用が確認できる。Python/Seleniumで各銀行のCSVを取得してActualへ読み込む自作スクリプトや、金融アグリゲータの非公式拡張も共有されている。ここには明確な不便がある。ただし銀行ログイン自動化や接続器を新規OSSのMVPにすると規約・保守・MFAの負担が大きい。GO候補は『銀行接続』ではなく、ダウンロード済みCSV/OFX/QIFをローカルで正規化・重複候補提示・照合・Actual/Firefly/hledger向けエクスポートするオフライン変換ライブラリに限定される。

## S014 — GitHub Actionsのテスト結果はログ・静的要約に分散

URL: https://github.com/orgs/community/discussions/163123

GitHub Communityの2025年要望は35票を得ており、GitHub Actionsには包括的なテスト結果のネイティブUIがなく、結果はログまたはアーティファクトに出ると指摘する。既存のdorny/test-reporter等はJUnit/XMLを解析してMarkdown要約やCheck annotationを作るが、専用UIがない、対話的にテスト詳細へ辿れない、job当たりannotationが50件に制限される、コミュニティActionの保守リスクがある、という具体的限界が説明されている。OSSとしてはJUnit等の既存パーサーを再実装せず、失敗のクラスタリング、テスト履歴をGitブランチ内に小さく保存、GitHub Pages/Actions artifactでフィルタ可能な静的ダッシュボードを生成するActionなら、SaaSや外部DBなしで差別化しうる。もっともctrf等の新興競合もあるため、中位候補とする。

## S015 — 表データの差分・照合は日次運用で、いまなお手組みの結合へ流れる

URL: https://news.ycombinator.com/item?id=17924798

Hacker NewsのAsk HNでは、投稿者が「毎日」データベースのTSVスナップショットを保存し、一意IDで新規・変更・未変更・削除を抽出して扱いにくい外部APIを更新したいと相談している。32件の回答は`sort`/`uniq`の重複入力、R/Pandasのanti-join/semi-join、SQLの一時テーブル、商用Beyond Compare、Daff、VisiDataなどに分散した。VisiDataの開発側も、キーと列名で対応付ける機能は追加余地として認めている。この一次資料は、単なるデータフレーム比較ライブラリではなく、主キー推定・型正規化・重複/欠損の事前診断・人が読める差分・patch/API出力までを一貫させたローカル照合CLIの需要を裏付ける。

## S016 — パッケージレジストリ利用指標（取得日スナップショット）

出典API: https://api.npmjs.org/downloads/point/last-month/xlsx 、https://api.npmjs.org/downloads/point/last-month/exceljs 、https://api.npmjs.org/downloads/point/last-month/@lingui/cli 、https://pypistats.org/api/packages/openpyxl/recent

2026年8月15日に取得したnpm APIの直近30日指標では、`xlsx`は48,144,235 downloads、`exceljs`は49,634,449 downloads、`@lingui/cli`は3,608,891 downloadsだった。PyPI Statsでは`openpyxl`は直近30日346,281,972 downloadsだった。これは各ツールのユニーク利用者数ではなく依存関係も含むため需要の代理指標に限定するが、Excel/CSV処理および翻訳カタログが広いソフトウェア供給網に載っていることを示す。Great Expectations/PanderaのPyPI照会はレート制限（HTTP 429）を受け、数値に採用していない。

## S017 — Excel競合の深掘り（GitHub REST API、2026-08-15取得）

ExcelCompare: https://github.com/na-ka-na/ExcelCompare 、Issue #69 https://github.com/na-ka-na/ExcelCompare/issues/69 、Issue #67 https://github.com/na-ka-na/ExcelCompare/issues/67 、Issue #45 https://github.com/na-ka-na/ExcelCompare/issues/45

ExcelCompareはCLI/APIでExcelをdiffするが、最新コミットは2022-04-22、最新リリース系列は2015年。2026年7月のCygwin絶対パス空白問題、2024年のunified diff不具合、古い大きなODSでのhang、数値/テキストセルの読み取り失敗、ライセンスファイルを求めるIssueが開いている。GitHub API取得時点で856 Stars、23 open issues、ライセンス指定なしである。

Git XL: https://github.com/xltrail/git-xl 、Issue #89 https://github.com/xltrail/git-xl/issues/89 、Issue #86 https://github.com/xltrail/git-xl/issues/86

Git XLはVBAをGit diffで扱う拡張で、最新リリース・コミットはいずれも2023-02-19。2026年にも「依存関係が古くインストーラが動かず、ビルド手順も不完全」「macOS対応」などが未解決である。API取得値は604 Stars、27 open issues。xlsx構造全体のリスク監査やAction向け出力を目的としていない。

ExceLint: https://github.com/ExceLint/ExceLint 、Issue #1 https://github.com/ExceLint/ExceLint/issues/1

ExceLintはExcelアドイン型の数式エラー検出器だが、リポジトリは2021-06-08からアーカイブ済み、最終コミットは2019-09-14、最新releaseは2019-03-03のv1.2である。API取得値は74 Stars、open Issue 1で、唯一のIssueはチュートリアル更新要望である。これらの事実は『diff・lint・Git/CI統合を一体化したクロスプラットフォーム代替』に入る余地を支持する。

## S018 — 表データ照合競合の深掘り（GitHub REST API、2026-08-15取得）

Datafold data-diff: https://github.com/datafold/data-diff 、最終コミット https://github.com/datafold/data-diff/commit/1410c6cd0b915ae24a15e03a7de15ff41beebaf0

`data-diff`は2,988 Stars、313 forksだがアーカイブ済みで、2024-05-17の最終コミットメッセージ自体が「Sunsetting open source data-diff」である。最新releaseは2024-02-20のv0.11.1である。このため、機密データをローカルで照合したい利用者にとって、代表的候補の継続保守が途切れている。

Daff: https://github.com/paulfitz/daff 、Issue #216 https://github.com/paulfitz/daff/issues/216 、#215 https://github.com/paulfitz/daff/issues/215 、#212 https://github.com/paulfitz/daff/issues/212 、#206 https://github.com/paulfitz/daff/issues/206

Daffは活発で922 Stars、47 open issues、最新release v1.4.2は2025-05-04であり、汎用table diffとしては強い競合である。ただし、比較結果の誤り、重複列名で差分を見落とす、SQLiteで`--fail-if-diff`が期待通り動かない、表計算対応の要望が未解決である。新規案はDaffを置換せず、主キー選択・スキーマ/正規化診断・照合の証跡・CSV/Parquet/DuckDBの移行ワークフローに限定すべきである。

Diff-table: https://github.com/chop-dbhi/diff-table 、Issue #10 https://github.com/chop-dbhi/diff-table/issues/10

`diff-table`は区切りファイルとPostgresのストリーミング比較を提供したが、最新releaseは2018-11-18、最終コミットは2019-10-30、未解決Issueが残る。Capital OneのdataCompareRも最新releaseは2020-05-04で、READMEのアーカイブ更新を除くと2025年以降の実装進展は見えない。これらは局所的な実装が散在する一方、軽量で現在保守される照合workflowが不足することを補強する。

## S019 — PDF/UA CLIは新興だが急速に充実しており、単純なvalidator新規参入は不可

URL: https://github.com/speedata/pdfa11y

2026年の新興OSS `pdfa11y` はGo製のPDF/UA CLIで、端末/JSON/HTML、batch/CI、ブラウザ内WASMを提供し、PACのGUI-onlyという空白を明示的に狙う。READMEはveraPDFのPDF/UA-1/UA-2ルールカタログに対するrule-by-rule coverage、構造・metadata・font・language・graphics・headings・tables・lists・math・forms等の多岐にわたる検査を記載する。なお、リポジトリはpre-1.0/alphaであり、alt textの品質、視覚上の読み順、headingの意味などは人間のレビューが必要と明記する。従って新規案が単にPDF/UA validatorを作る場合はNOである。残る余地は、複数検査器の出力を集約し、大量文書を修正コストと公開期限でトリアージし、修正前後の監査台帳を作るワークフロー層に限られる。PDF候補の判定はGOではなくMAYBEへ下げる。

## S020 — データ契約・データ品質競合の深掘り（GitHub REST API、2026-08-15取得）

Great Expectations: https://github.com/fivetran/great_expectations 、Pandera: https://github.com/unionai-oss/pandera 、Soda Core: https://github.com/sodadata/soda-core 、Frictionless Python: https://github.com/frictionlessdata/frictionless-py

Great Expectationsは11,713 Starsで、2026-08-07に1.20.0をrelease、最終コミットは2026-08-14、open Issuesは38である。Panderaは4,431 Stars、最新releaseは2026-06-29のv0.32.1、最終コミットは2026-08-07で、PyArrowのfirst-class validationを追加している。Soda Coreも2026-08-13にv4.21.0をreleaseし、Frictionless Pythonも2026年にリリース・bugfixが続く。つまり既存OSSは**保守停止ではなく、活発かつ広範**である。

Frictionlessでは欠損列の二重エラー、multipart CSVの行破損、Parquet extraの依存解決、Excel extraのエラー表現など、ファイル処理のedge caseが引き続きIssueになる。だが、これは新規の汎用validatorが勝てる根拠ではない。Great Expectations/Pandera/Soda/Frictionlessの設定・概念・依存関係を包み隠して「ゼロ設定」をうたうだけでは、品質保証上の曖昧さと機能重複を招く。よって候補03は独立プロジェクトとして**NO**、または既存フレームワークへ『ファイルからの初期schema提案・失敗例レポート・GitHub Action preset』をPRする方向が合理的と判定する。


# diopside コンポーネント実装仕様

- 文書ID: DIO-COMPONENT-001
- 版: v1.1
- 状態: UI component contractの正本移植
- 更新日: 2026-07-26
- v1.1変更: LengthSliderの単一トラック2つまみ実装を視覚レビュー後の実装へ反映した。
- 移植元: `.workspace/design-reference/components.html`（SSRレンダリング済み、全量確認）
- 関連: [デザインシステム](design-system.md) / [ワイヤーフレーム](wireframes.md)

共通tokenは `primary-500 #7C5CBF`、hover/pressed `#6F4FB4`、selected面`#EDE7F8`、背景`#F7F6FA`、surface`#FFF`、line`#E4E1EC`、本文`#211D2B`、補足`#5C5668`。focusは`0 0 0 3px rgba(124,92,191,.2〜.35)`、通常罫線1px、入力・チップ1.5px、カードradius12、chip radius999。すべての操作は44px以上のヒット領域、キーボード操作、可視focusを持つ。

## Button

用途は主CTA、補助操作、軽操作。DOMは`button`または外部遷移時だけ`a`で、icon + textをinline-flexにする。primaryはh48、padding左右22、radius12、白文字、1画面1つまで。secondaryはh48、1.5px ink枠。textはh44、枠なし、primary文字。default→hover `primary-600`、activeも同色、disabledはopacity `.4`かつ操作不能、focusは3px ring。件数CTAはprimaryでlive更新する。

## Chip（5バリアント）

`button`（選択・追加・action）または条件表示の`span`内にclose用`button`を置く。共通h32、padding 0 14（removableは右12）、font13、radius999、枠1.5px、44px hit area。結果行では横スクロール可・折返しなし。

| variant | 表示・状態 | 操作 / a11y |
| --- | --- | --- |
| selectable | default: `#8E8899`枠、selected: primary面/白文字 | click/Enter/Spaceでtoggle。`aria-pressed`でselectedを伝える。 |
| removable | primary背景、label、close 15px icon | 本体は該当条件節へ、closeは即解除。closeの`aria-label`は「{label}の条件を解除」。 |
| add | primaryの破線枠、`＋タグ`等 | 条件なしでも常設。該当シートを開きfocusを移す。 |
| action | primary枠、tune icon、`条件 (n)` | シート全体を開く。nはpolite live regionで通知。 |
| preset | 投稿日などのquick preset | selectedを明示し、再選択の振る舞いを一貫させる。 |

## SearchBar / SuggestList

検索バーは`form > search icon + token list + input`。h44、radius14、padding左右14、gap8、非focus枠`#C9C4D6`、focus枠primary+3px ring。タグtokenはprimary-100面にsell icon、label、closeを持つ。placeholderは「キーワード・タグ・話し言葉で検索」。未確定語はkeywordとして残す。

サジェストは入力中だけ`role=listbox`、各候補をh44の`button role=option`で構成する。最大4行（タグ≤2、日付≤1、keyword 1）。タグ候補は件数付き、日付候補は解釈を明示、keyword候補は入力語のまま検索。ArrowUp/Downでactive option、Enterで選択、Escapeで閉じ、`aria-activedescendant`と選択結果の`role=status`を使う。候補選択後に検索条件へ追加したことを通知する。

## 条件行・条件シート・条件パネル（`ConditionRow` / `ConditionSheet` / `ConditionPanel`）

条件行は検索結果上部の`sticky` container。`chip list + action button`で、elevation 1（`0 2px 8px rgba(33,29,43,.08)`）。zero stateは3つのadd chip、applied stateはremovable chipとaction chip。条件数はURLと同期し、件数更新はlive region。

mobileは`role=dialog aria-modal=true aria-labelledby` のbottom sheet。上部radius20、ハンドル36×4、elevation 2（`0 8px 28px rgba(33,29,43,.16)`）、タグ→長さ→投稿日→固定CTA。背景クリック、下swipe、Escで閉じ、focus trapとtriggerへのfocus returnを必須とする。PCは同一内容の右スライド`aside/dialog`でw320。resetは全条件を既定へ戻し、CTAは `n件を表示` / 0件の緩和提案へ変える。

## LengthSlider / RangeCalendar

LengthSliderは2 thumbの`input type=range`相当（必要ならARIA slider）。track h4、選択範囲primary、thumb 18×18、2px primary枠/白面。0〜5h+を15分単位にsnapし、上限5h+は上限なしを意味する。矢印キー、PageUp/PageDown、Home/Endで調整し、現在値を`aria-valuetext`で読めるようにする。

RangeCalendarはヘッダー（戻る、月移動、クリア）と7列日付grid。視覚cell40×40、実hit area44px、端点radius999 primary、範囲primary-100、配信日はdot、未来日はdisabled。開始→終了の2タップで確定し、`role=grid`、日付cellの`aria-selected`、月移動buttonのlabelを持つ。キーボードで日移動、Enter/Spaceで選択、Escで条件へ戻る。

## VideoListItem / VideoGridCard

listは`article > Link(行全体) > thumbnail + metadata`、gridも`article > Link`。サムネは16:9、list 120×68、radius8、右下に長さbadge。titleは16px/700/line-height1.5で2行省略、caption12.5px、tagは最大2。集計がある動画だけchat countを表示し、0で埋めない。行whole-linkは44px以上、hoverはprimary枠、focus-visible ring。画像altは装飾なら空、内容を代替するなら動画タイトル。loading/失敗はストライプplaceholderで寸法を保つ。

## Navigation

mobileは`nav[aria-label="mobile navigation"] > Link×4`、h56+safe-area、activeはprimary-500とfilled icon。PCは`aside > nav[aria-label="main navigation"]`、w220、項目h40/radius10、activeはprimary-100面+primary-600。順は検索・ホーム・保存・履歴でも、mobileとroute写像は一対一。管理は罫線分離する場合でも未認証ではdisabled表示でなくDOMから除外する。skip link、`main#main-content tabindex=-1`、footerの規約・privacyリンクを維持する。

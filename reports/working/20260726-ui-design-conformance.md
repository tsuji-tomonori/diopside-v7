# UI design正本適合確認（2026-07-26、Phase 7d）

`docs/design/design-system.md`、`wireframes.md`、`component-implementation.md`を正本とし、`design-measurements.spec.ts`が実要素の`getComputedStyle()`または`getBoundingClientRect()`を測定する。token変数だけを証拠にした判定は行わない。

| 項目 | 期待値 | 実測値 | 証拠 | 判定 |
| --- | --- | --- | --- | --- |
| primary button背景 | #7C5CBF | rgb(124, 92, 191) | 色を実要素のcomputed styleで測定する | 適合 |
| selected chip背景 | #EDE7F8 | rgb(237, 231, 248) | 色を実要素のcomputed styleで測定する | 適合 |
| link色 | #6F4FB4 | rgb(111, 79, 180) | 色を実要素のcomputed styleで測定する | 適合 |
| display | 24px | 24px | 文字組を実要素のcomputed styleで測定する | 適合 |
| caption | 12.5px | 12.5px | 文字組を実要素のcomputed styleで測定する | 適合 |
| label | 11px/700/.12em | 11px/700/1.32px | 文字組を実要素のcomputed styleで測定する | 適合 |
| video title | 16px/700 | 16px/700 | 文字組を実要素のcomputed styleで測定する | 適合 |
| chip角丸 | 999px | 999px | 形状とfocusを実要素のcomputed styleで測定する | 適合 |
| button角丸 | 12px | 12px | 形状とfocusを実要素のcomputed styleで測定する | 適合 |
| card角丸 | 12px | 12px | 形状とfocusを実要素のcomputed styleで測定する | 適合 |
| input角丸 | 14px | 14px | 形状とfocusを実要素のcomputed styleで測定する | 適合 |
| sheet角丸 | mobile 20px | mobile 20px、desktop 0px panel | 形状とfocusを実要素のcomputed styleで測定する | 適合 |
| card影 | なし | none | 形状とfocusを実要素のcomputed styleで測定する | 適合 |
| sheet影 | 0 8px 28px rgba(.16) | rgba(33,29,43,.16) 0px 8px 28px | 形状とfocusを実要素のcomputed styleで測定する | 適合 |
| 標準罫線 | 1px | 1px | 形状とfocusを実要素のcomputed styleで測定する | 適合 |
| input/chip/button罫線 | CSS指定1.5px | mobile Chrome（DPR 2.625）computed 1px、cssRules 1.5px | 形状とfocusを実要素のcomputed styleとcssRulesで測定する | 適合 |
| focus outline | 3px | 3px solid | 形状とfocusを実要素のcomputed styleで測定する | 適合 |
| 横padding | 16/24px | mobile 16px、desktop 24px | 余白を実要素のcomputed styleで測定する | 適合 |
| list gap | 12px | 12px | 余白を実要素のcomputed styleで測定する | 適合 |
| section margin | 32px | 32px | 余白を実要素のcomputed styleで測定する | 適合 |
| search bar高 | 44px | 44px | 寸法を実要素のbounding rectで測定する | 適合 |
| primary button高 | 48px | 48px | 寸法を実要素のbounding rectで測定する | 適合 |
| mobile tab高 | 56px以上 | link 56px、safe-areaを含むnav 57px | 寸法を実要素のbounding rectで測定する | 適合 |
| sidebar幅 | 220px | 220px | 寸法を実要素のbounding rectで測定する | 適合 |
| sidebar item視覚高 / hit領域 | 視覚40px / 44px以上 | 疑似要素背景40px / Link矩形44px | 寸法を実要素のbounding rectと`::before`のcomputed styleで測定する | 適合 |
| sidebar radius | 10px | 疑似要素のborder-top-left-radius 10px | 寸法を実要素のbounding rectと`::before`のcomputed styleで測定する | 適合 |
| right panel幅 | 320px | 320px | 寸法を実要素のbounding rectで測定する | 適合 |
| visible button/link | 44×44px以上 | 全件44×44px以上 | 操作領域を実要素のbounding rectで測定する | 適合 |

集計: 適合28、不適合0、未検証0、対象外0。

## Phase 7c/7dの決着

- sidebar itemはLink自体をmin-height 44pxのhit領域として保ち、active背景を上下2px insetした`::before`へ移した。視覚背景は40px、radiusは10pxであり、実測E2Eが背景とLink矩形を別々にassertする。
- `wireframes.md`をv1.1、`component-implementation.md`をv1.2へ更新し、PCサイドバーを「視覚背景h40/radius10、リンクのhit領域44px以上」と正本へ明記した。
- mobile Chrome（Pixel 7、DPR 2.625）ではinput/chip/buttonの`getComputedStyle().borderTopWidth`が1pxを返した。一方、同一renderの`cssRules`は3要素とも1.5pxである。これはChromeがborder幅をdevice pixelへ丸めてcomputed値をserializeする測定環境の制約であり、CSS指定は正しいため適合とした。
- sidebar radiusはdesktop Chromeで疑似要素の`border-top-left-radius`が10pxであることを直接測定した。

## 実行結果

| command | 実結果 |
| --- | --- |
| `cd frontend && npm run typecheck` | 合格、終了コード0、2.4秒。 |
| `cd frontend && npm test` | 合格、26 files / 76 tests、3.7秒。 |
| `cd frontend && npm run build` | 合格、151 modules transformed、1.1秒。 |
| `cd frontend && npm run test:e2e` | 合格、終了コード0、44.3秒。desktop-chrome 29件、mobile-chrome 29件、計58件。 |
| `cd backend && .venv/bin/python -m pytest -q` | 合格、63 passed、2.0秒。 |
| `task verify` | 合格、終了コード0、約87秒。workspace typecheck、frontend 76 tests、infra 4 tests、workspace build、Ruff、Pyright、Mypy、architecture、docs、backend pytest 63件、contract、cost/quota、infra plan/synth、E2E（desktop-chrome 29件、mobile-chrome 29件、計58件・39.8秒）がすべて完走。 |

Playwrightの既定並列workerはWSL2上でプロセスごとexit code 144でkillされ、出力なしで終了していた。`playwright.config.ts`で既定worker数を1に明示し、安定した環境では`PLAYWRIGHT_WORKERS`で上書き可能にした。その結果、単一の`npm run test:e2e`と`task verify`内のE2Eの双方が終了コード0で完走した。Phase 7c適用前に観測したdesign-measurementsの4件失敗は、適用前バージョンによるものであり、現在の単一E2Eではdesktop/mobileとも全件合格している。

`tools/capture-ui-rewrite-screenshots.mjs`では変更したsidebarを含むdesktop PNGを26枚更新した。Phase 7dはE2Eの完走対策とaggregate検証証跡の確定を対象とし、PNGの追加撮影は行わない。

## SWEBOK・残余risk

| ID | status | evidence | rationale | follow-up |
| --- | --- | --- | --- | --- |
| REQ-102, DES-001, CON-080 | pass | 正本v1.1/v1.2、styles.css、desktop/mobile直接測定E2E | 視覚寸法・操作領域・CSS指定を同じ変更で追跡し、全適合表項目を直接測定した | 変更時は同じ測定を再実行 |
| TST-701 | pass | `npm run test:e2e`終了コード0、desktop-chrome 29件・mobile-chrome 29件、44.3秒 | 要求に対応するbrowser測定と状態E2Eを単一commandで全件実行した | UI変更時は同じE2Eを再実行 |
| MGT-003, MGT-060 | pass | 本reportの指定6 command実測値、`task verify`終了コード0 | 完了基準を実測し、WSL2固有リスクと恒久対策を記録した | 実行基盤の変更時はworker設定を再評価 |
| PRC-001, SCM-001, QUA-001 | pass | `playwright.config.ts`、`task verify`終了コード0、aggregate検証ログ | worker数を構成として固定し、実装・検証・記録を同じ変更単位で完結した | Playwright更新時は単一E2Eとaggregateを再実行 |
| TST-801, MNT-001 | pass | `npm run test:e2e`終了コード0（58 passed、44.3秒）、`task verify`終了コード0（E2E 58 passed、39.8秒） | 全体E2Eとaggregate検証がともに終了コード0で完走し、保守変更の回帰範囲を直接確認した | UI変更時は指定6 commandをnarrowからaggregateへ再実行 |

残余risk: 設計適合表は適合28、不適合0、未検証0、対象外0である。E2Eと`task verify`の完走を妨げていたWSL2の既定並列worker killは、worker数の明示で解消した。DPR 2.625環境のborder computed値は1pxへの丸めを受けるため、CSS指定1.5pxの確認にはcssRulesを併用する。

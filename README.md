# Fungal Treatment Guideline — 公開網頁版

抗黴菌治療互動指引，由原本的單一檔案 HTML（V23，約 1 MB）改建為可公開發佈的靜態網站，
並分成 **電腦版** 與 **手機版** 兩套介面，共用同一份資料。

| | 網址 | 介面重點 |
|---|---|---|
| 電腦版 | `/` | 完整寬表格（14 欄）、三欄菌種卡片、全螢幕流程圖 |
| 手機版 | `/m/` | 每筆治療建議為一張卡片並依 clinical setting 分組、可摺疊的感染情境、流程圖檢視器支援雙指縮放並記住你偏好的放大倍率 |

首次進入 `/` 時會依螢幕寬度與 User-Agent 自動導向合適的版本。

兩版都可以**一鍵切換**，而且會停在同一個菌種頁（切換連結會自動帶上目前的 `#id`）：

- 電腦版：右下角浮動按鈕「📱 手機版」，在首頁與菌種內頁都看得到
- 手機版：上方標題列右上角「🖥 電腦版」，清單頁與菌種內頁都有；頁尾另有一個說明性連結

使用者自行切換後會記在 `localStorage`，之後不再自動導向。
也可以直接用 `?view=desktop` 或 `?view=mobile` 指定版本。

菌種頁面可用網址錨點直接分享，例如 `/#g0o0`（Aspergillus spp.）、`/m/#g6o0`（Cryptococcus）；
加上 `:n` 可直接跳到該頁第 n 個感染情境，例如 `/#g7o0:8`（Candida endocarditis）。

## 兩種進入方式

guideline 的治療圖是依**感染情境（syndrome）**書寫的，但菌種列表天然是以菌種進入。因此
Aspergillus、Mucorales、Cryptococcus、Candida 這四個有 hub 頁的分類，在列表上同時提供
「依感染情境查詢」的入口；單一菌種頁若只是沿用 genus-level 建議，頁首會標示並連回 hub 頁。
hub 頁本身另有感染情境索引可直接跳轉。

## 為什麼要拆檔

原始檔把 93 個菌種的資料與 152 張流程圖 SVG 全部內嵌在一個 989 KB 的 HTML 裡。
手機用行動網路開啟時，必須先下載完整檔案才會出現任何畫面。改建後：

| 載入內容 | 大小 |
|---|---|
| 首頁（HTML + CSS + JS + `meta.json` + `index.json`） | 約 100 KB |
| 單一菌種內文 | 1–40 KB（點擊時才載入） |
| 該菌種的流程圖 | 2–108 KB（**手機版展開流程圖區塊時才載入**） |

資料內容沒有任何改寫：治療優先順序、劑量、療程、推薦強度、逐列 provenance 與 exact locator
全部沿用原始文件。

## 目錄結構

```
index.html              電腦版
m/index.html            手機版
assets/css/base.css     兩版共用：色彩 token、治療優先順序配色、reference 樣式
assets/css/desktop.css  電腦版版面
assets/css/mobile.css   手機版版面
assets/js/core.js       兩版共用：資料載入、priority 分級、來源 / locator 連結
assets/js/desktop.js    電腦版畫面組裝
assets/js/mobile.js     手機版畫面組裝
data/meta.json          分類、bibliography、reference 資料庫、統計
data/index.json         93 筆菌種摘要（首頁清單與搜尋用）
data/org/<id>.json      單一菌種完整內容
data/charts/<id>.json   單一菌種的流程圖 SVG
build/extract.py        由 source/ 的單檔 HTML 產生上述 data/
build/overrides.py      對原始檔內容的修正層（見下）
build/svgkit.py         流程圖共用的 SVG 元件（會量測文字、自動縮排版）
build/charts_*.py       各別重建的流程圖產生器
source/                 原始單一檔案 HTML（頁尾提供離線下載）
```

## 修正層 build/overrides.py

`source/` 的原始檔完全保持交付時的樣子（不修改），所有對內容的修正都集中寫在
`build/overrides.py`，由 `extract.py` 在產生 `data/` 時套用。這樣每一處與原始文件
不同的地方都能單獨被檢視與稽核，套用清單也會寫進 `data/meta.json` 的 `overrides`。

目前的修正：

- **trim-chart-notes** — 頁面上原本有幾層只是在解釋「這張圖是怎麼做出來的」，而且多半跟旁邊
  的圖例重複：每張圖標題上方的全大寫方法論字串、圖表區塊上方的 provenance 說明、圖內重述
  色階的註腳、`Audit status` 一行、audit rounds 計數、手機頁尾的來源檔 SHA-256，以及 8 條
  Source 行末的引用政策附註。這些都移除了。保留的是真正有臨床意義的部分：Source 與 exact
  locator 連結、evidence scope／dose notation，以及每張圖一句「正式分支、措辭與分級以所引用
  的原始 Figure / Table / text 為準」。

- **dose-typo-dayay** — 原始檔有 195 處 `mg/kg/dayay`（治療列 98 處 + 流程圖 SVG 內 97 處，
  共 35 個菌種），是劑量正規化時 `d`→`day` 取代出錯的殘留，修正為 `/day`。

- **mucormycosis-pathway** — Cornely 2019 Figure 5 是真正的決策路徑（緊急處置 → 手術清創與
  立即開始治療並行 → 依腦部侵犯／SOT／腎功能不全分支 → 反應評估 → 疾病進展／毒性分支），
  原始檔把它壓成三列平鋪treatment。三個藥物可及性分頁（A/B/C）各自重建為原本的路徑。
  推薦強度是**從原圖填色取樣**得到的（#ddedde strong、#fff9d7 moderate、#feebed marginal、
  #f7dfdf against），不是從文字推測——因此修正了兩處誤讀：liposomal amphotericin B <5 mg/kg
  與 combination with posaconazole 都是 *marginally recommended*，不是 recommended against。

- **stratified-charts** — 原始檔把每個 syndrome 都畫成一條平鋪的 treatment 清單，蓋掉了資料本身
  已經帶有的分層軸：每一列自己的 **clinical setting 欄**（severity / site / phase）。全站 152 個
  syndrome 中有 91 個跨越一個以上的 setting，其中 89 個改繪為分支圖（另外 2 個由 mucormycosis
  專屬繪圖器接手）。四層以內用欄位並排；超過四層改用整列橫帶版面（Aspergillus 的 chronic
  pulmonary aspergillosis 有九層）。內容一字未改：每張卡片的藥物、劑量、療程、QoE 與原始
  priority 用語都是該列原文，只是重新排列。單一 setting 的 syndrome 維持原本的清單。

- **cryptococcosis-algorithm** — 原始檔的 Cryptococcus 流程圖以菌種為起點，但
  guideline 本身不是這樣分層。Chang 2024 Figure 1 的分支順序是
  involvement（CNS / 播散 / 單獨肺部 / 皮膚接種）→ host（HIV / SOT / non-HIV non-SOT）
  → severity，species 只在 Panel 13（C. gattii CNS 比照 C. neoformans，non-HIV 可延長
  induction 至 4–6 週）與 Panel 15（罕見種同 C. neoformans）出現，屬於修飾因子。
  此修正在 *C. neoformans* 與 *C. gattii* 兩頁最前面加入依 Figure 1 重建的主流程圖；
  所有藥物、劑量、療程與 A/B/C 分級皆逐字轉錄自 Figure 1 與被引用的 Panel，未新增內容。

## 更新資料（例如日後出 V24）

1. 把新的單檔 HTML 放進 `source/`。
2. 執行 `python3 build/extract.py source/<新檔名>.html`。
3. 確認網頁正常後 commit `data/` 與 `source/`。

`build/extract.py` 讀取原始檔裡的 `DATA`、`SVG_CHARTS`、`GROUP_META`、`REFERENCE_LINKS`、
`REFERENCE_DATABASE`、`PAGE_REFERENCE_DB` 六個常數與 bibliography 區塊，輸出結果是固定的
（不含時間戳記），所以 CI 可以直接比對 `data/` 是否與 `source/` 同步。

## 本機預覽

因為改用 `fetch()` 讀取 JSON，不能用 `file://` 直接開啟，需要一個本機伺服器：

```bash
python3 -m http.server 8000
# 電腦版 http://localhost:8000/
# 手機版 http://localhost:8000/m/
```

## 發佈到 GitHub Pages

`.github/workflows/pages.yml` 會在 push 時先驗證 `data/` 與 `source/` 一致，再發佈整個
repository。

**第一次需要手動開啟 Pages（只做一次）：**

> GitHub repository → **Settings** → **Pages** → Build and deployment →
> Source 選 **GitHub Actions** → 存檔

（這一步需要 repository 管理權限，GitHub Actions 的內建 token 無法代勞。）

開啟後回到 **Actions** 分頁，對最後一次 `Deploy to GitHub Pages` 按 **Re-run all jobs**，
或直接再 push 一次即可完成發佈。

網址：

- 電腦版 `https://fre637781.github.io/anti-fungal/`
- 手機版 `https://fre637781.github.io/anti-fungal/m/`
- 直接連到某個菌種 `https://fre637781.github.io/anti-fungal/#g0o0`

## 使用限制

本網頁僅供醫療專業人員參考，不能取代臨床判斷、當地流行病學、感染科會診或藥物仿單。
所有流程圖均為 guideline-derived summary reconstruction，並非原始 guideline figure 的忠實重畫；
正式分支與措辭請以來源 Figure / Table / text 為準。

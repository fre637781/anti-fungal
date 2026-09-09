# Fungal Treatment Guideline — 公開網頁版

抗黴菌治療互動指引，由原本的單一檔案 HTML（V23，約 1 MB）改建為可公開發佈的靜態網站，
並分成 **電腦版** 與 **手機版** 兩套介面，共用同一份資料。

| | 網址 | 介面重點 |
|---|---|---|
| 電腦版 | `/` | 完整寬表格（14 欄）、三欄菌種卡片、全螢幕流程圖 |
| 手機版 | `/m/` | 每筆治療建議為一張卡片、可摺疊的感染情境、可縮放流程圖檢視器 |

首次進入 `/` 時會依螢幕寬度與 User-Agent 自動導向合適的版本；兩個版本頁尾都有切換按鈕，
使用者自行選擇後會記在 `localStorage`，之後不再自動導向。
也可以直接用 `?view=desktop` 或 `?view=mobile` 指定版本。

菌種頁面可用網址錨點直接分享，例如 `/#g0o0`（Aspergillus spp.）、`/m/#g6o0`（Cryptococcus）。

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
source/                 原始單一檔案 HTML（頁尾提供離線下載）
```

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

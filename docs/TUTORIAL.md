# 練習：merge 前才跑完整測試

這個 repo 用來驗證「PR 平常只跑 lint，按 Enable auto-merge 才跑完整測試，通過才合併」的流程。

## 檔案說明

| 檔案 | 用途 |
|---|---|
| `app/calculator.py` | 被測試的小程式 |
| `tests/test_group1.py` | 第 1 組測試，很快就跑完 |
| `tests/test_group2.py` | 第 2 組測試，故意睡 30 秒，模擬真正的測試要跑一段時間 |
| `.github/workflows/ci.yml` | CI 本體 |

`ci.yml` 裡的 job：

| Job | 什麼時候跑 | 做什麼 |
|---|---|---|
| `Lint` | 每次都跑 | 用 ruff 檢查程式碼 |
| `Decide whether to run tests` | 每次都跑 | 判斷這次要不要跑完整測試，理由寫在 run 的 Summary 頁；在 PR 上把合併鎖設成 🟡 等待中 |
| `Test Group 1`、`Test Group 2` | 開了 auto-merge、有 `run-tests` label，或 push 到 main | 跑測試 |
| `Report test status` | PR 上有跑測試時 | 依測試結果把合併鎖改成 🟢 或 🔴 |
| `Remove run-tests label` | PR 上有 `run-tests` label 時 | 跑完後移除這個 label |

### 合併鎖：`Full tests (runs on Enable auto-merge)`

這是 ruleset 的**必要檢查**。它不是 job，而是 workflow 用 API 設定在 commit 上的 **commit status**，在 PR 的 checks 列表裡和 job 並排顯示：

| 狀態 | 意思 | 能合併嗎 |
|---|---|---|
| 🟡 pending「Waiting: click Enable auto-merge…」 | 這個 commit 還沒跑完整測試 | ❌ 只能按 Enable auto-merge |
| 🟡 pending「Running the full tests...」 | 測試正在跑 | ❌ |
| 🟢 success | 完整測試通過 | ✅ |
| 🔴 failure | 完整測試失敗 | ❌ |

為什麼用 commit status 而不是 job：job 失敗會讓整個 run 失敗，GitHub 每次都會寄「CI failed」的信；pending 的 status 一樣擋得住合併，但 run 本身是成功的，所以**只有測試真的失敗時才會寄信**。

為什麼不能讓它被跳過：GitHub 把 skipped 的必要檢查當成「通過」，PR 會變成可以直接合併，畫面上也不會出現 Enable auto-merge，等於沒跑測試就能合併。

## 一、事前設定（只做一次）

### 1. 確認 repo 能用 ruleset 和 auto-merge

個人帳號的免費方案，**私有 repo 不能用 ruleset 和 auto-merge**，只有公開 repo 可以。帳號是 GitHub Pro 的話，私有 repo 也可以。

這個練習 repo 只有範例程式，可以考慮改成公開：Settings → General → 最下面 Danger Zone → Change visibility。公開 repo 的 Actions 也不收費。

### 2. 先把 workflow 推上 main

設定 ruleset 之後就不能直接 push 到 main，所以要先推：

```bash
git add .
git commit -m "ci: run the full tests only before merging"
git push origin main
```

到 repo 的 Actions 分頁，應該看到一次 `CI` 的 run：push 到 main 會跑完整測試，`Full tests (runs on Enable auto-merge)` 不會出現，因為它只設定在 PR 上。

### 3. 開啟 auto-merge

Settings → General → Pull Requests：

- 勾選 **Allow auto-merge**
- 建議只留 **Allow rebase merging**，和 cake-fastapi 一樣
- 建議勾選 **Automatically delete head branches**，合併後自動刪分支

### 4. 建立 `run-tests` label

```bash
gh label create run-tests --color FBCA04 --description "Run the full tests once; removed after the run" --repo jackytungcake/cake
```

### 5. 設定 main 的 ruleset

Settings → Rules → Rulesets → New ruleset → New branch ruleset：

1. Ruleset name：`main`
2. Enforcement status：**Active**
3. Target branches：Add target → **Include default branch**
4. 勾選：
   - **Restrict deletions**
   - **Require a pull request before merging**（Required approvals 留 0，一個人練習不需要 approve）
   - **Require status checks to pass**，按 Add checks 加入 `Lint` 和 `Full tests (runs on Enable auto-merge)`
   - **Block force pushes**
5. 按 Create

## 二、練習情境

每個情境都從一個新分支開始。做完一個情境後，回到 main 並更新：

```bash
git checkout main && git pull
```

### 情境 A：一般 push 只跑 lint

```bash
git checkout -b demo/a
echo "# demo a" >> README.md
git commit -am "docs: demo a"
git push -u origin demo/a
gh pr create --fill
```

預期：

- PR 的 checks 裡 `Lint` 綠、`Test Group 1/2` 被跳過、`Full tests (runs on Enable auto-merge)` 是 **🟡 等待中**，說明是「Waiting: click Enable auto-merge…」
- 整個 run 是成功的，所以**不會收到 CI failed 的信**
- 下方的 Merge 按鈕不能按，變成 **Enable auto-merge**

### 情境 B：按 Enable auto-merge → 測試通過 → 自動合併

接著情境 A 的 PR：

1. 按 **Enable auto-merge** → 選 Rebase and merge → Confirm
2. 到 Actions 分頁，會出現一個新的 run，事件是 `auto_merge_enabled`，這次會跑 `Test Group 1/2`；`Full tests (runs on Enable auto-merge)` 變成「Running the full tests...」
3. 約 1 分鐘後全部通過，PR 自動合併
4. 合併後，main 會再跑一次完整測試（post-merge 檢查）

用指令也可以，效果一樣：

```bash
gh pr merge --auto --rebase
```

### 情境 C：測試失敗就不合併，修好再 push 會自動合併

```bash
git checkout -b demo/c
sed -i '' 's/return a + b/return a - b/' app/calculator.py
git commit -am "fix: break add() on purpose"
git push -u origin demo/c
gh pr create --fill
gh pr merge --auto --rebase
```

預期：

1. `Test Group 1` 失敗、`Full tests (runs on Enable auto-merge)` 變 🔴，**PR 沒有被合併**，auto-merge 仍是開啟的；這次會收到 CI failed 的信，因為測試真的失敗了
2. 修好再 push：
   ```bash
   sed -i '' 's/return a - b/return a + b/' app/calculator.py
   git commit -am "fix: restore add()"
   git push
   ```
3. 因為 auto-merge 還開著，這次 push 會自動跑完整測試，通過後自動合併

### 情境 D：加 `run-tests` label 手動跑一次

```bash
git checkout -b demo/d
echo "# demo d" >> README.md
git commit -am "docs: demo d"
git push -u origin demo/d
gh pr create --fill
gh pr edit --add-label run-tests
```

預期：

1. 新的 run 事件是 `labeled`，會跑完整測試
2. 跑完後 `Remove run-tests label` 會把 label 拿掉
3. `Full tests (runs on Enable auto-merge)` 變 🟢，這時 Merge 按鈕可以直接按
4. 再 push 一次 commit，又變回 🟡 等待中：新的 commit 還沒測過

### 情境 E：「Re-run jobs」沒有用

1. 照情境 A 開一個 PR，`Full tests (runs on Enable auto-merge)` 是 🟡 等待中
2. 加上 `run-tests` label，但**立刻**到 Actions 分頁把那次 `labeled` 的 run 按 Cancel
3. 回到更早那次 `opened` 的 run，按 **Re-run all jobs**

預期：測試還是被跳過。重跑用的是當初事件的資料，那時 PR 還沒有 label。所以要觸發測試，一定要用「加 label」或「Enable auto-merge」。

## 三、觀察費用

每個 run 的頁面右上角有 **Usage**，可以看到每個 job 的計費時間。可以比較：

- 一般 push：只有 `Lint`、`Decide`，兩個都是幾秒鐘的小 job
- 開 auto-merge 或加 label：多了 `Test Group 1/2` 和 `Report test status`

GitHub 依 job 計費，每個 job 無條件進位到整分鐘。所以 job 數量越多，固定開銷越大；cake-fastapi 一次跑 8 組測試也是同樣道理。

## 四、常見問題

- **看不到 Enable auto-merge 按鈕**：確認第一節的步驟 1 和 3；也確認 ruleset 有設定必要檢查。PR 已經可以合併時（所有檢查都綠），GitHub 只會顯示一般的 Merge 按鈕。
- **ruleset 加不到 check 名稱**：check 要先跑過一次才會出現在選單；也可以直接輸入名稱。
- **一直停在 🟡「Running the full tests...」**：跑測試的 run 被手動取消了，取消的 run 不會更新狀態。再加一次 `run-tests` label 或 push 一次就會更新。
- **PR 一直顯示「Expected — Waiting for status to be reported」**：ruleset 要求的必要檢查名稱，和 `ci.yml` 的 `STATUS_CONTEXT` 不一致，GitHub 等不到這個狀態，PR 就永遠不能合併。兩邊名稱要完全一樣。

# 部署指南 · GitHub Profile README

把当前目录的文件部署成一个真实可用的 GitHub 主页。

> 你的信息已填入：
> - GitHub 用户名：`qiongzhang1225-alt`
> - 显示名：小鲸鱼（在打字动画 URL 中以 `%E5%B0%8F%E9%B2%B8%E9%B1%BC` 形式存储）
> - 邮箱：`qiongzhang1225@gmail.com`
>
> 如果以后想改，直接修改 `README.md` 即可。

## 1. 创建特殊仓库

> **关键：仓库名必须和你的 GitHub 用户名完全一致**（大小写也要一样）。

在 GitHub 上创建新仓库：
- 仓库名：`qiongzhang1225-alt`
- **必须勾选**："Public"（公开）
- **不要**勾选任何初始化选项

仓库会被创建在：https://github.com/qiongzhang1225-alt/qiongzhang1225-alt

## 2. 推送本地代码

```bash
cd "C:/Users/ZHN/Desktop/AI工作/006"
git init
git branch -M main
git add .
git commit -m "feat: setup GitHub profile"
git remote add origin https://github.com/qiongzhang1225-alt/qiongzhang1225-alt.git
git push -u origin main
```

## 3. 打开 GitHub Actions 权限（重要！）

进入仓库 → **Settings** → **Actions** → **General**：

1. **Actions permissions**：选 "Allow all actions and reusable workflows"
2. **Workflow permissions**：
   - 选 **"Read and write permissions"**
   - 勾选 **"Allow GitHub Actions to create and approve pull requests"**

不开这个，蛇动画的 SVG 没法推回 `output` 分支。

## 4. 触发蛇动画

进入仓库的 **Actions** 标签 → 左侧选 **"Generate Snake Animation"** → 点击 **"Run workflow"** → 选 main 分支运行。

运行成功后，仓库会自动多出一个 `output` 分支，里面有 `github-snake.svg` 和 `github-snake-dark.svg`。

如果首次运行后 README 里图片仍显示不出来，等 1–2 分钟后强制刷新（Ctrl+F5），CDN 缓存需要一点时间。

之后每 12 小时自动重新生成一次（cron 在 `.github/workflows/snake.yml` 里）。

## 5. 文件结构总览

```
006/
├── README.md                      # 主页内容
├── DEPLOY.md                      # 本文件
├── .gitignore
└── .github/
    └── workflows/
        └── snake.yml              # 每12h生成蛇动画
```

## 6. 常见问题

**Q: 蛇动画的图片一直 404？**
A: 检查 `output` 分支是否生成（仓库分支下拉里看）；检查 README 里 URL 拼写。

**Q: 打字动画里的显示名怎么改？**
A: 改 `README.md` 第 2 行 URL 里 `I'm+` 后面那段编码（当前是 `%E5%B0%8F%E9%B2%B8%E9%B1%BC` = 小鲸鱼）。改成你想要的文字的 URL 编码即可，可在浏览器控制台执行 `encodeURIComponent("你的名字")` 得到。

**Q: 想加更花哨的元素（音乐、博客、Wakatime、统计卡片）？**
A: 在 README.md 里加图片标签即可。可以参考 [awesome-github-profile-readme](https://github.com/abhisheknaiidu/awesome-github-profile-readme)。

---

部署完成后，访问 https://github.com/qiongzhang1225-alt 就能看到你的主页。

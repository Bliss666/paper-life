# 图解风微信图文管线 · ThinkNote

对标「图解万物」「认知觉醒」这类知识类图文号的自动化生产线：
**定时选题 → AI 写稿 → 自动出图文卡片 → 可直接发布的配文**。

```
d:\bliss\图文
├─ pipeline/          代码
│  ├─ poster.py       卡片渲染器（大字观点卡版式）
│  ├─ llm.py          AI 写稿（OpenAI 兼容接口 + 本地降级）
│  ├─ build.py        构建入口：选题 → 图文
│  ├─ publisher.py    发布队列：轮转选题、防重复
│  ├─ scheduler.py    定时调度：每天出当期
│  └─ setup_key.py    一次性导入 API key
├─ content/
│  ├─ topics.yml      选题库（AI 赛道，6 条）
│  ├─ life_topics.yml 选题库（生活技巧 + 人生道理，20 条）
│  └─ skills.yml      技巧库：182 条技巧 + 26 个合集（每期 7 页 = 8 张图）
├─ assets/            品牌 logo、产品截图
├─ out/
│  ├─ tip-001/        单篇产物（图片 + article.md）
│  └─ sk-01/          技巧期次产物（8 张图 + article.md）
├─ config.yml         本地配置（API key，不提交）
├─ config.example.yml 配置模板
└─ install_schedule.ps1  安装 Windows 定时任务
```

## 快速开始

```bash
# 1. 导入 API key（只写本机 config.yml，不打印明文）
python pipeline/setup_key.py --clipboard     # 从剪贴板
python pipeline/setup_key.py                 # 手动粘贴（不回显）

# 2. 试跑一篇
python pipeline/build.py --topic ai-002

# 3. 批量出稿
python pipeline/build.py                     # 全部选题
python pipeline/publisher.py --batch 7       # 出 7 天库存（跳过已发布）

# 3b. 技巧期次（每期 8 张图 = 封面 + 7 个技巧页）
python pipeline/build_skills.py              # 全部 26 期
python pipeline/build_skills.py --topic sk-01
python pipeline/check_skills.py              # 质检：文案长度/场景/气泡/合集
python pipeline/retune_8pages.py --write     # 重排合集，保证每期正好 7 页

# 4. 定时出稿（每天 08:30 自动）
powershell -ExecutionPolicy Bypass -File .\install_schedule.ps1
```

## 产物

每篇产出一个目录：

| 文件 | 说明 |
|---|---|
| `01-cover.jpg` | 封面 1080×1440（视频号/公众号首图） |
| `02..NN-pageN.jpg` | 正文卡片，一页一个观点 |
| `article.md` | 可直接粘贴的配文，图已按段落插好位置 |
| `draft.json` | 结构化稿件，方便二次编辑 |

图片同时复制到 `images/` 子目录，便于打包上传。

## 版式

- **封面**：大标题居中，副标题、品牌 chip、底部落款
- **正文页**：分类 chip + 页码 + 大字标题（`*星号*` 标出强调词，渲染成强调色）
  + 分割线 + 补充说明 + 要点列表 + 底部品牌条
- **配色**：6 套浅色主题 + 1 套品牌深色，按选题 id 稳定分配，同一选题每次颜色一致

## 赛道设计

主线是 **AI 效率 + 认知觉醒** 双赛道，不硬广：
靠「真实踩坑经验」建立信任，ThinkNote 作为解决方案自然出现在最后一两页。

选题原则：
1. 每篇一个具体痛点，能被一句话复述
2. 给可执行的动作，不给正确的废话
3. 不编数据、不用标题党
4. 落点轻 —— 让用户自己发现「这正是 ThinkNote 干的」

## 加新选题

编辑 `content/topics.yml`，追加一条：

```yaml
- id: ai-011
  topic: 一句话选题
  title: 备用标题（无 API 时用）
  kicker: AI效率        # 分类标签
  theme: blue           # warm/blue/green/violet/orange/gray/brand
  brief: 给 AI 的额外写作要求
  fallback:             # 本地降级稿（无 API key 时用）
    pages:
      - kicker: 真相
        headline: 主标题，*强调*用星号
        note: 补充说明
        points: ["要点1", "要点2"]
```

## 防重复发布

`state.json` 记录已发布选题，`publisher.py --next` 永远给出下一条没发过的。
发布后在公众号后台手动点一下发布，然后：

```bash
python pipeline/publisher.py --mark ai-002
```

## 无 API key 也能跑

没有 key 时自动降级到选题里的 `fallback` 文案，管线不中断 —— 版式照样出，
只是文案比较简略。配置好 key 后加 `--force` 重写。

## 依赖

- Python 3.13（Anaconda 自带）
- `Pillow`、`PyYAML`、`requests`
- 字体：Windows 自带微软雅黑（`C:\Windows\Fonts\msyh.ttc`）
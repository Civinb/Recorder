# Recorder — 个人休闲记录器

一个基于 Flask 的本地信息录入收藏和管理工具。目前仅支持动漫部分的录入，后续将加入电影，游戏等。
动漫部分支持记录每部动漫的名称、封面、类型、放映日期、评分、评价、标签等信息，并集成 [Bangumi](https://bgm.tv/) 数据：可在本地构建全文搜索索引，按番剧自动抓取封面。

在线体验：<https://cvbrecorder.onrender.com/home>（部署于 [Render](https://render.com/)）。
### 注：在线部署仍在尝试阶段，设置中的同步bangumi数据的功能仅支持本地部署使用，在线点击只会下载最新.zip数据包，无法同步到数据库中。

## 功能特性
### 动漫记录
- **动漫管理**：新增、编辑、删除、查看动漫条目，支持本地图片上传作为封面。
- **列表浏览**：表格展示所有条目，支持
  - 名称搜索（带防抖）
  - 按年份 / 类型 / 状态筛选
  - 点击表头排序
  - 分页（每页 10 / 25 / 50 条）
- **Bangumi 集成**
  - 导入 Bangumi 官方数据 dump（zip），在本地构建含 FTS5 全文搜索的 SQLite 索引
  - 按番剧 ID 自动从 Bangumi API 下载封面
  - 提供搜索 / 条目详情的 JSON 接口

## 技术栈

- Python 3 + [Flask](https://flask.palletsprojects.com/) 3.1
- Flask-SQLAlchemy 3.1 / SQLAlchemy 2.0（本地 SQLite，线上 PostgreSQL via psycopg2）
- sqlite3 + FTS5（Bangumi 全文搜索索引）
- requests（调用 Bangumi API）

## 项目结构

```
Recorder/
├── app.py              # 应用入口，注册 blueprint、初始化数据库
├── db.py               # SQLAlchemy 实例
├── models.py           # 数据模型（Anime / status / type 枚举）
├── init_db.py          # 手动初始化数据库脚本
├── anime.py            # 动漫增删改查路由（/animes）
├── bangumi_api.py      # Bangumi 相关 API 路由与封面下载（/api/bangumi）
├── bangumi_index.py    # Bangumi 数据 dump 解析与本地索引构建
├── templates/          # Jinja2 模板
└── static/             # 上传图片、Bangumi 数据 zip、索引库（git 忽略）
```

## 快速开始

### 1. 准备环境

```powershell
# 安装依赖
pip install -r requirements.txt
```

### 2. 运行

```powershell
python app.py
```

应用启动后访问 <http://127.0.0.1:5000/home>。

> 数据库 `main.db` 会在首次启动时自动创建（`db.create_all()`），并自动迁移补齐 `bangumi_id` 字段，无需手动建表。

## 主要页面与路由

| 路径 | 说明 |
| --- | --- |
| `/home` | 首页 |
| `/animes/list` | 动漫列表（搜索 / 筛选 / 排序 / 分页） |
| `/animes/new` | 新增动漫 |
| `/animes/<id>` | 动漫详情 |
| `/animes/<id>/edit` | 编辑动漫 |
| `/animes/<id>/delete` | 删除动漫（POST） |
| `/settings` | 设置页：同步 / 构建 Bangumi 索引 |

### Bangumi API

| 路径 | 方法 | 说明 |
| --- | --- | --- |
| `/api/bangumi/index/info` | GET | 查看当前索引状态 |
| `/api/bangumi/index/build` | POST | 从最新 zip 重建索引 |
| `/api/bangumi/search?q=` | GET | 全文搜索动画条目 |
| `/api/bangumi/subject/<id>` | GET | 获取条目详情 |

## 使用 Bangumi 数据

1. 进入 **Settings** 页面，点击 **Sync** 下载 Bangumi 最新数据 dump。
2. 将下载得到的 zip 放入 `static/bangumi_data/` 目录。
3. 点击 **Extract / Rebuild Index** 构建本地索引（约 1–3 分钟）。
4. 构建完成后即可使用搜索接口，新增动漫时可自动抓取封面。

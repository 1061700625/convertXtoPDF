# 📚 EPUB/MOBI to PDF 批量转换器

一个简单好用的电子书格式转换工具，支持 EPUB 和 MOBI 转 PDF。

---

## ✨ 功能特性

- 🔄 **批量转换** - 一次上传多个文件
- 📤 **拖拽上传** - 支持拖拽文件
- 📥 **打包下载** - 可打包为 ZIP 下载
- 🎨 **现代 UI** - 渐变设计，响应式布局
- 🔒 **本地处理** - 文件不上传服务器
- 📖 **中文支持** - 自动使用中文字体
- 🖥️ **双模式** - 网页版 + 桌面版

---

## 🚀 快速开始

### 方法 1：直接运行（需要手动安装依赖）

```bash
# 安装依赖
pip install -r requirements.txt

# 运行（网页版，自动打开浏览器）
python app.py

# 或桌面版
python app.py --mode desktop
```

### 方法 2：一键运行（推荐）

**首次运行会自动创建虚拟环境并安装依赖**，之后直接启动。

**Windows**:
```cmd
run.bat
```

**Mac / Linux**:
```bash
chmod +x run.sh
./run.sh
```

**运行逻辑**：
1. 检查是否有 `venv` 文件夹 → 有则直接运行
2. 没有 `venv` → 检查系统 Python
3. 没有 Python → 提示安装
4. 有 Python → 创建 venv 并安装依赖

---

## 📋 使用说明

### 上传文件

1. 点击上传区域选择文件
2. 或直接拖拽 EPUB/MOBI 文件
3. 支持批量上传（最多 20 个）

### 转换

1. 点击 "Convert to PDF" 开始转换
2. 等待转换完成
3. 点击下载按钮
4. 文件会保存到系统的"下载"文件夹

**下载位置**：
- Windows: `C:\Users\你的用户名\Downloads`
- Mac: `/Users/你的用户名/Downloads`
- Linux: `/home/你的用户名/Downloads`

---

## ⚙️ 配置选项

在 `app.py` 中修改：

```python
# 文件大小限制（默认 100MB）
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# 并发转换数（默认 4）
MAX_CONVERSION_WORKERS = 4

# 单次最大文件数（默认 20）
MAX_FILES_PER_CONVERSION = 20
```

### 命令行参数

```bash
# 查看帮助
python app.py --help

# 网页版，指定端口
python app.py --port 8080

# 桌面版
python app.py --mode desktop --port 8080
```

---

## 📦 分发说明

### 打包方法

1. 压缩**整个项目文件夹**为 ZIP
2. 发送给用户

### 用户使用

1. 解压 ZIP 文件
2. 双击运行：
   - **Windows**: `run.bat`
   - **Mac/Linux**: `./run.sh`
3. 首次运行会自动创建虚拟环境并安装依赖（约 40MB）
4. 之后直接启动（不再检查 Python）

### 系统要求

**首次运行**：
- 需要 Python 3.8+（用于创建虚拟环境）
- 或已有虚拟环境（`venv/` 文件夹）

**后续运行**：
- 无需 Python（使用虚拟环境中的 Python）
- 直接使用 `run.bat` 或 `run.sh` 启动

### 安装 Python（仅首次需要）

**Windows**:
1. 访问 https://www.python.org/downloads/
2. 下载并安装 Python 3.8+
3. ⚠️ 安装时务必勾选 "Add Python to PATH"

**macOS**:
```bash
brew install python3
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt install python3 python3-pip python3-venv
```

---

## ⚠️ 注意事项

### 转换限制

- **复杂排版** - 可能丢失部分格式
- **加密书籍** - 无法转换 DRM 保护的电子书
- **图片密集型** - 图片较多的书效果可能不佳

### 字体依赖

中文转换需要系统安装中文字体：

| 平台 | 状态 |
|------|------|
| Windows | ✅ 系统自带 |
| macOS | ✅ 系统自带 |
| Linux | 需安装：`apt install fonts-wqy-microhei` |

---

## 🔧 技术栈

- **后端**: Flask
- **PDF 生成**: ReportLab, pypdf
- **EPUB 解析**: ebooklib
- **MOBI 解析**: mobi
- **桌面模式**: pywebview
- **前端**: HTML/CSS/JavaScript

---

## 📁 项目结构

```
epub-mobi-to-pdf/
├── app.py              # 主应用
├── run.bat            # Windows 启动脚本
├── run.sh             # Mac/Linux 启动脚本
├── requirements.txt   # Python 依赖
├── README.md          # 本文档
├── FIXES.md           # Bug 修复记录
├── RUNNING.md         # 运行状态
└── venv/              # 虚拟环境（首次运行后生成）
```

---

## 🐛 已知问题

详见 [FIXES.md](FIXES.md)

### 已修复

- ✅ 中文文件名支持
- ✅ ZIP 下载为空
- ✅ Windows 编码问题
- ✅ 自动打开浏览器
- ✅ 简化为单文件入口

---

## 🛑 停止服务

```bash
# 停止 Flask 服务
pkill -f "python.*app.py"
```

---

## 📝 许可证

MIT License

---

**最后更新**: 2026-03-26

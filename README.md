# 📚 EPUB/MOBI to PDF 批量转换器

一个基于 Flask 的网页应用，支持批量将 EPUB 和 MOBI 格式的电子书转换为 PDF。

## ✨ 功能特性

- 🔄 **批量转换** - 一次上传多个文件，自动队列处理
- 📤 **拖拽上传** - 支持拖拽文件到上传区域
- 📥 **打包下载** - 转换完成后可单独下载或打包为 ZIP 下载
- 🎨 **现代 UI** - 渐变设计，响应式布局
- 🔒 **本地处理** - 所有文件在本地处理，不上传到外部服务器
- 📖 **中文支持** - 自动检测并使用系统中文字体

## 🚀 快速开始

### 1. 安装依赖

```bash
cd epub-mobi-to-pdf
pip install -r requirements.txt
```

### 2. 运行应用

```bash
python app.py
```

### 3. 打开浏览器

访问 http://localhost:5000

## 📋 使用说明

1. **上传文件** - 点击上传区域或拖拽 EPUB/MOBI 文件
2. **开始转换** - 点击 "Convert to PDF" 按钮
3. **下载结果** - 转换完成后，可单独下载或打包下载所有 PDF

## ⚙️ 配置选项

### 文件大小限制

默认最大上传文件大小为 100MB，可在 `app.py` 中修改：

```python
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
```

### 临时文件存储

转换后的 PDF 保存在系统临时目录，可通过修改 `UPLOAD_FOLDER` 指定：

```python
app.config['UPLOAD_FOLDER'] = '/path/to/your/folder'
```

## 🔧 技术栈

- **后端**: Flask
- **PDF 生成**: ReportLab, pypdf
- **EPUB 解析**: ebooklib
- **MOBI 解析**: mobi
- **前端**: 原生 HTML/CSS/JavaScript

## ⚠️ 注意事项

1. **字体依赖**: 中文转换需要系统安装中文字体
   - Linux: `apt install fonts-wqy-microhei` 或 `apt install fonts-noto-cjk`
   - macOS: 系统自带
   - Windows: 系统自带

2. **转换限制**: 
   - 复杂排版的 EPUB 可能会丢失部分格式
   - 加密的电子书无法转换
   - 图片密集型书籍可能转换效果不佳

3. **文件清理**: 转换后的 PDF 保存在临时目录，建议定期清理

## 📁 项目结构

```
epub-mobi-to-pdf/
├── app.py              # 主应用文件
├── requirements.txt    # Python 依赖
└── README.md          # 说明文档
```

## 🛠️ 开发

### 添加新格式支持

在 `convert_file()` 函数中添加新的转换逻辑：

```python
def convert_file(input_path, output_path, file_type):
    if file_type == 'new_format':
        # 添加转换逻辑
        pass
```

### 自定义 PDF 样式

修改 `create_pdf_from_chapters()` 函数中的样式定义：

```python
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontName=FONT_NAME,
    fontSize=24,  # 修改字号
    # ... 其他样式
)
```

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

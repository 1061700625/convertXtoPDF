#!/usr/bin/env python3
"""
EPUB/MOBI to PDF Batch Converter
A Flask web application for converting ebook formats to PDF
"""

import os
import sys
import tempfile
import zipfile
from pathlib import Path
from flask import Flask, request, render_template_string, send_file
from werkzeug.utils import secure_filename

# Import conversion libraries
try:
    from pypdf import PdfWriter, PdfReader
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Install with: pip install flask pypdf reportlab")
    sys.exit(1)

# For EPUB parsing
try:
    import ebooklib
    from ebooklib import epub
except ImportError:
    ebooklib = None

# For MOBI parsing
try:
    import mobi
except ImportError:
    mobi = None

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# ============== 全局配置参数 ==============
# 并发转换线程数 - 同时处理多少个文件的转换
MAX_CONVERSION_WORKERS = 4

# 单次转换最大文件数 - 一次上传最多多少个文件
MAX_FILES_PER_CONVERSION = 20
# ========================================

ALLOWED_EXTENSIONS = {'epub', 'mobi'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def register_fonts():
    """Register CJK fonts for ReportLab"""
    font_paths = [
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simsun.ttc",
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('CJK', font_path))
                return 'CJK'
            except:
                continue
    
    # Fallback to default fonts
    return 'Helvetica'

FONT_NAME = register_fonts()

def extract_epub_content(epub_path):
    """Extract text content from EPUB file"""
    chapters = []
    
    if ebooklib is None:
        raise ImportError("ebooklib not installed. Install with: pip install ebooklib")
    
    book = epub.read_epub(epub_path)
    
    # Get book metadata
    title = book.get_metadata('DC', 'title')
    title = title[0][0] if title else Path(epub_path).stem
    
    author = book.get_metadata('DC', 'creator')
    author = author[0][0] if author else 'Unknown'
    
    # Extract chapters - iterate through all items
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            content = item.get_content().decode('utf-8', errors='ignore')
            
            # Simple HTML tag stripping
            import re
            text = re.sub(r'<[^>]+>', ' ', content)
            text = re.sub(r'\s+', ' ', text).strip()
            
            if text:
                chapters.append(text)
    
    return {'title': title, 'author': author, 'chapters': chapters}

def extract_mobi_content(mobi_path):
    """Extract text content from MOBI file"""
    chapters = []
    
    if mobi is None:
        raise ImportError("mobi not installed. Install with: pip install mobi")
    
    try:
        text, metadata = mobi.extract(mobi_path)
        
        title = metadata.get('Title', Path(mobi_path).stem)
        author = metadata.get('Author', 'Unknown')
        
        # Split by common chapter markers
        chapter_markers = ['\n\nChapter ', '\n\nCHAPTER ', '\n\nPart ', '\n\nPART ']
        
        current_chapter = ""
        for line in text.split('\n'):
            line = line.strip()
            if any(line.startswith(marker) for marker in chapter_markers):
                if current_chapter:
                    chapters.append(current_chapter)
                current_chapter = line
            elif line:
                current_chapter += ' ' + line
        
        if current_chapter:
            chapters.append(current_chapter)
        
        if not chapters:
            chapters = [text[:50000]]  # Limit size if no chapters found
        
        return {'title': title, 'author': author, 'chapters': chapters}
    
    except Exception as e:
        # Fallback: treat entire file as single chapter
        with open(mobi_path, 'rb') as f:
            content = f.read().decode('utf-8', errors='ignore')
        return {
            'title': Path(mobi_path).stem,
            'author': 'Unknown',
            'chapters': [content[:100000]]
        }

def create_pdf_from_chapters(chapters_data, output_path):
    """Create PDF from extracted chapters"""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=FONT_NAME,
        fontSize=24,
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    author_style = ParagraphStyle(
        'Author',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    heading_style = ParagraphStyle(
        'ChapterHeading',
        parent=styles['Heading2'],
        fontName=FONT_NAME,
        fontSize=16,
        spaceAfter=12,
        spaceBefore=12
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=11,
        leading=14,
        alignment=TA_LEFT
    )
    
    story = []
    
    # Title page
    story.append(Paragraph(chapters_data['title'], title_style))
    story.append(Paragraph(f"by {chapters_data['author']}", author_style))
    story.append(PageBreak())
    
    # Chapters
    for i, chapter in enumerate(chapters_data['chapters']):
        if i > 0:
            story.append(PageBreak())
        
        # Chapter heading
        story.append(Paragraph(f"Chapter {i + 1}", heading_style))
        
        # Split chapter into paragraphs
        paragraphs = chapter.split('\n')
        for para in paragraphs:
            para = para.strip()
            if para and len(para) > 2:  # Skip very short lines
                try:
                    story.append(Paragraph(para, normal_style))
                except:
                    # Skip problematic text
                    pass
    
    doc.build(story)
    return True

def convert_file(input_path, output_path, file_type):
    """Convert a single file to PDF"""
    try:
        if file_type == 'epub':
            content = extract_epub_content(input_path)
        elif file_type == 'mobi':
            content = extract_mobi_content(input_path)
        else:
            return False, f"Unsupported file type: {file_type}"
        
        create_pdf_from_chapters(content, output_path)
        return True, "Success"
    
    except Exception as e:
        return False, str(e)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EPUB/MOBI to PDF Converter</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            background: #f8f9ff;
            transition: all 0.3s ease;
            cursor: pointer;
            margin-bottom: 20px;
        }
        
        .upload-area:hover, .upload-area.dragover {
            border-color: #764ba2;
            background: #f0f2ff;
        }
        
        .upload-area i {
            font-size: 48px;
            color: #667eea;
            margin-bottom: 15px;
        }
        
        .upload-area p {
            color: #666;
            margin-bottom: 10px;
        }
        
        .upload-area .formats {
            font-size: 12px;
            color: #999;
        }
        
        #fileInput {
            display: none;
        }
        
        .file-list {
            margin: 20px 0;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background: #f8f9ff;
            border-radius: 8px;
            margin-bottom: 8px;
        }
        
        .file-item .name {
            flex: 1;
            color: #333;
        }
        
        .file-item .status {
            font-size: 12px;
            padding: 4px 12px;
            border-radius: 12px;
        }
        
        .status.pending {
            background: #ffeaa7;
            color: #d63031;
        }
        
        .status.processing {
            background: #74b9ff;
            color: #0984e3;
        }
        
        .status.success {
            background: #55efc4;
            color: #00b894;
        }
        
        .status.error {
            background: #fab1a0;
            color: #d63031;
        }
        
        .file-item .remove {
            background: none;
            border: none;
            color: #ff7675;
            cursor: pointer;
            font-size: 18px;
            margin-left: 10px;
        }
        
        .delete-btn {
            background: #ff4757;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s ease;
            white-space: nowrap;
        }
        
        .delete-btn:hover {
            background: #ff6b81;
            transform: translateY(-1px);
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 32px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .progress-container {
            margin-top: 20px;
            display: none;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.3s ease;
        }
        
        .progress-text {
            text-align: center;
            margin-top: 10px;
            color: #666;
            font-size: 14px;
        }
        
        .download-section {
            margin-top: 30px;
            padding: 20px;
            background: #f0fff4;
            border-radius: 8px;
            border: 1px solid #55efc4;
            display: none;
        }
        
        .download-section h3 {
            color: #00b894;
            margin-bottom: 15px;
        }
        
        .download-btn {
            display: inline-block;
            background: #00b894;
            color: white;
            padding: 10px 20px;
            border-radius: 6px;
            text-decoration: none;
            margin-right: 10px;
            margin-bottom: 10px;
        }
        
        .info-box {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9ff;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .info-box h3 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 16px;
        }
        
        .info-box ul {
            margin-left: 20px;
            color: #666;
            font-size: 14px;
        }
        
        .info-box li {
            margin-bottom: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 EPUB/MOBI to PDF Converter</h1>
        <p class="subtitle">Batch convert your ebooks to PDF format</p>
        
        <!-- 配置信息显示 -->
        <div class="info-box" style="margin-bottom: 20px;">
            <h3>⚙️ 当前配置</h3>
            <ul style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                <li><strong>🔄 并发转换数:</strong> {{ max_workers }} 线程</li>
                <li><strong>📦 单次最大文件数:</strong> {{ max_files }} 个文件</li>
                <li><strong>📊 文件大小限制:</strong> {{ max_size }} MB</li>
                <li><strong>📂 临时目录:</strong> {{ upload_folder }}</li>
            </ul>
        </div>
        
        <div class="upload-area" id="uploadArea">
            <div style="font-size: 48px; margin-bottom: 15px;">📁</div>
            <p><strong>Drag & drop files here</strong></p>
            <p>or click to select files</p>
            <p class="formats">Supported formats: EPUB, MOBI</p>
            <input type="file" id="fileInput" multiple accept=".epub,.mobi">
        </div>
        
        <div class="file-list" id="fileList"></div>
        
        <button class="btn" id="convertBtn" disabled>
            🚀 Convert to PDF
        </button>
        
        <div class="progress-container" id="progressContainer">
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="progress-text" id="progressText">Converting... 0/0</div>
        </div>
        
        <div class="download-section" id="downloadSection">
            <h3>✅ Conversion Complete!</h3>
            <div id="downloadLinks"></div>
        </div>
        
        <div class="info-box">
            <h3>ℹ️ How it works</h3>
            <ul>
                <li>Upload EPUB or MOBI files (max 100MB each)</li>
                <li>Click "Convert to PDF" to start batch conversion</li>
                <li>Download converted PDF files individually or as a ZIP</li>
                <li>All files are processed locally and deleted after conversion</li>
            </ul>
        </div>
    </div>
    
    <script>
        let files = [];
        
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const fileList = document.getElementById('fileList');
        const convertBtn = document.getElementById('convertBtn');
        const progressContainer = document.getElementById('progressContainer');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const downloadSection = document.getElementById('downloadSection');
        const downloadLinks = document.getElementById('downloadLinks');
        
        uploadArea.addEventListener('click', () => fileInput.click());
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            handleFiles(e.dataTransfer.files);
        });
        
        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
        });
        
        function handleFiles(fileList) {
            const newFiles = Array.from(fileList).filter(file => {
                const ext = file.name.split('.').pop().toLowerCase();
                return ['epub', 'mobi'].includes(ext);
            });
            
            // Check max files limit
            if (files.length + newFiles.length > {{ max_files }}) {
                alert(`⚠️ 文件数量超限！最多支持 {{ max_files }} 个文件，当前已选择 ${files.length} 个，还能添加 {{ max_files }} 个。`);
                // Add only up to the limit
                const canAdd = {{ max_files }} - files.length;
                if (canAdd > 0) {
                    newFiles.splice(0, newFiles.length - canAdd);
                } else {
                    return;
                }
            }
            
            newFiles.forEach(file => {
                files.push({
                    file: file,
                    id: Date.now() + Math.random(),
                    status: 'pending'
                });
            });
            
            updateFileList();
        }
        
        function updateFileList() {
            fileList.innerHTML = files.map(item => `
                <div class="file-item" data-id="${item.id}">
                    <span class="name">${item.file.name}</span>
                    <span class="status ${item.status}">${item.status}</span>
                    ${item.status === 'pending' ? `<button class="remove" onclick="removeFile(${item.id})">×</button>` : ''}
                </div>
            `).join('');
            
            convertBtn.disabled = files.length === 0 || files.some(f => f.status === 'processing');
        }
        
        function removeFile(id) {
            files = files.filter(f => f.id !== id);
            updateFileList();
        }
        
        convertBtn.addEventListener('click', async () => {
            const pendingFiles = files.filter(f => f.status === 'pending');
            if (pendingFiles.length === 0) return;
            
            // Check total file size before upload (use server config value)
            const totalSize = pendingFiles.reduce((sum, f) => sum + f.file.size, 0);
            const maxSize = {{ max_size }} * 1024 * 1024; // From server config
            if (totalSize > maxSize) {
                const sizeMB = (totalSize / 1024 / 1024).toFixed(2);
                alert(`⚠️ 文件总大小超限！\n\n当前大小：${sizeMB} MB\n最大限制：{{ max_size }} MB\n\n请减少文件数量或使用更小的文件。`);
                convertBtn.disabled = false;
                return;
            }
            
            progressContainer.style.display = 'block';
            downloadSection.style.display = 'none';
            convertBtn.disabled = true;
            
            const totalFiles = pendingFiles.length;
            
            const formData = new FormData();
            pendingFiles.forEach(item => {
                formData.append('files', item.file);
            });
            
            // Show loading state with animation
            progressFill.style.width = '30%';
            progressFill.style.transition = 'width 2s ease-in-out';
            progressText.textContent = `🔄 正在转换 ${totalFiles} 个文件，请稍候...`;
            
            try {
                const response = await fetch('/convert', {
                    method: 'POST',
                    body: formData
                });
                
                // Check if response is JSON
                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    // Server returned HTML error (likely 413 Request Entity Too Large)
                    const currentSizeMB = (totalSize / 1024 / 1024).toFixed(2);
                    throw new Error(`服务器返回错误 (HTTP ${response.status})\n\n文件总大小 (${currentSizeMB} MB) 可能超过限制 ({{ max_size }} MB)。\n\n请减少文件数量后重试。`);
                }
                
                const result = await response.json();
                
                // Conversion complete
                progressFill.style.width = '100%';
                
                if (result.success) {
                    if (result.converted.length === 0) {
                        alert('转换失败：没有成功转换的文件');
                        progressContainer.style.display = 'none';
                        convertBtn.disabled = false;
                        return;
                    }
                    
                    progressText.textContent = `✅ 转换完成！成功 ${result.converted.length}/${totalFiles} 个`;
                    
                    // Update file statuses
                    files = files.map(f => {
                        const converted = result.converted.find(c => c.original === f.file.name);
                        if (converted) {
                            return { ...f, status: 'success', pdfPath: converted.pdf };
                        }
                        return f;
                    });
                    
                    // Show download links with delete buttons
                    const pdfFiles = result.converted.map(c => c.pdf);
                    downloadLinks.innerHTML = result.converted.map(c => `
                        <div class="file-item" style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                            <a href="/download/${encodeURIComponent(c.pdf)}" class="download-btn" style="flex: 1;">
                                📥 ${c.original} → ${c.pdf}
                            </a>
                            <button class="delete-btn" onclick="deleteFile('${encodeURIComponent(c.original)}', '${encodeURIComponent(c.pdf)}', this)" style="background: #ff4757; color: white; border: none; padding: 10px 16px; border-radius: 6px; cursor: pointer; font-size: 14px;">
                                🗑️ 删除
                            </button>
                        </div>
                    `).join('') + `
                        <div style="display: flex; gap: 10px; margin-top: 15px;">
                            <a href="/download-all?files=${encodeURIComponent(pdfFiles.join(','))}" class="download-btn" style="flex: 1; background: #667eea; text-align: center;">
                                📦 Download All (ZIP)
                            </a>
                            <button onclick="deleteAllFiles()" style="flex: 1; background: #ff4757; color: white; border: none; padding: 14px 20px; border-radius: 6px; cursor: pointer; font-size: 14px;">
                                🗑️ 删除全部
                            </button>
                        </div>
                    `;
                    
                    downloadSection.style.display = 'block';
                    
                    // Hide progress after delay
                    setTimeout(() => {
                        progressContainer.style.display = 'none';
                        progressFill.style.width = '0%';
                        progressFill.style.transition = 'width 0.3s ease';
                    }, 2000);
                } else {
                    alert('❌ 转换失败：' + result.error);
                    progressContainer.style.display = 'none';
                    progressFill.style.width = '0%';
                    convertBtn.disabled = false;
                }
            } catch (error) {
                // Format error message
                let errorMsg = error.message;
                if (errorMsg.includes('Unexpected token') || errorMsg.includes('not valid JSON')) {
                    errorMsg = `❌ 服务器错误\n\n可能是文件总大小超过 100MB 限制。\n\n请减少文件数量后重试。`;
                } else if (!errorMsg.startsWith('❌')) {
                    errorMsg = `❌ ${errorMsg}`;
                }
                alert(errorMsg);
                progressContainer.style.display = 'none';
                progressFill.style.width = '0%';
                convertBtn.disabled = false;
            }
            
            updateFileList();
        });
        
        // Delete single file (both original and PDF)
        async function deleteFile(encodedOriginal, encodedPdf, btnElement) {
            const original = decodeURIComponent(encodedOriginal);
            const pdf = decodeURIComponent(encodedPdf);
            if (!confirm(`确定要删除 ${original} 和 ${pdf} 吗？`)) return;
            
            try {
                const response = await fetch(`/delete-pair?original=${encodedOriginal}&pdf=${encodedPdf}`, {
                    method: 'DELETE'
                });
                const result = await response.json();
                
                if (result.success) {
                    // Remove the file item from UI
                    btnElement.parentElement.remove();
                    
                    // Check if no files left
                    const remainingFiles = downloadLinks.querySelectorAll('.file-item');
                    if (remainingFiles.length === 0) {
                        downloadSection.style.display = 'none';
                    }
                    const deleted = result.deleted.filter(f => f.exists).map(f => f.name).join(', ');
                    alert(`✅ 已删除：${deleted || '无文件'}`);
                } else {
                    alert(`❌ 删除失败：${result.error}`);
                }
            } catch (error) {
                alert(`❌ 删除错误：${error.message}`);
            }
        }
        
        // Delete all files
        async function deleteAllFiles() {
            const fileCount = downloadLinks.querySelectorAll('.file-item').length;
            if (fileCount === 0) {
                alert('没有可删除的文件');
                return;
            }
            
            if (!confirm(`确定要删除所有 ${fileCount} 个 PDF 文件吗？`)) return;
            
            try {
                const response = await fetch('/delete-all', {
                    method: 'DELETE'
                });
                const result = await response.json();
                
                if (result.success) {
                    downloadLinks.innerHTML = '';
                    downloadSection.style.display = 'none';
                    alert(`✅ 已删除所有 ${result.deleted} 个文件`);
                } else {
                    alert(`❌ 删除失败：${result.error}`);
                }
            } catch (error) {
                alert(`❌ 删除错误：${error.message}`);
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE,
        max_workers=MAX_CONVERSION_WORKERS,
        max_files=MAX_FILES_PER_CONVERSION,
        max_size=app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024),
        upload_folder=app.config['UPLOAD_FOLDER']
    )

@app.route('/convert', methods=['POST'])
def convert():
    import uuid
    import traceback
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    if 'files' not in request.files:
        return {'success': False, 'error': 'No files uploaded'}, 400
    
    uploaded_files = request.files.getlist('files')
    
    # Check max files limit
    if len(uploaded_files) > MAX_FILES_PER_CONVERSION:
        return {
            'success': False, 
            'error': f'文件数量超限！最多支持 {MAX_FILES_PER_CONVERSION} 个文件，当前上传了 {len(uploaded_files)} 个。'
        }, 400
    
    converted = []
    conversion_tasks = []
    
    # Helper function for single file conversion
    def convert_single_file(file):
        try:
            if file and file.filename and allowed_file(file.filename):
                original_filename = file.filename
                if '.' not in original_filename:
                    return None
                
                file_type = original_filename.rsplit('.', 1)[1].lower()
                safe_name = f"{uuid.uuid4().hex}.{file_type}"
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_type}') as tmp_input:
                    file.save(tmp_input.name)
                    input_path = tmp_input.name
                
                original_stem = Path(original_filename).stem
                safe_stem = ''.join(c if c.isalnum() or c in '-_' else '_' for c in original_stem)
                output_filename = f"{safe_stem}.pdf"
                safe_original = f"{uuid.uuid4().hex}_{original_filename}"
                original_save_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_original)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_output:
                    output_path = tmp_output.name
                
                success, message = convert_file(input_path, output_path, file_type)
                
                if success:
                    final_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
                    
                    # Cross-platform file move (Windows doesn't allow rename over existing file)
                    try:
                        if os.path.exists(final_path):
                            os.remove(final_path)
                        os.rename(output_path, final_path)
                    except OSError:
                        # Fallback: copy then delete
                        import shutil
                        shutil.copy2(output_path, final_path)
                        os.remove(output_path)
                    
                    # Move original file
                    try:
                        if os.path.exists(original_save_path):
                            os.remove(original_save_path)
                        os.rename(input_path, original_save_path)
                    except OSError:
                        import shutil
                        shutil.copy2(input_path, original_save_path)
                        os.remove(input_path)
                    
                    return {
                        'original': original_filename,
                        'original_safe': safe_original,
                        'pdf': output_filename
                    }
                else:
                    try:
                        os.unlink(input_path)
                    except:
                        pass
            return None
        except Exception as e:
            print(f"Error converting {file.filename}: {e}")
            print(traceback.format_exc())
            return None
    
    # Use thread pool for concurrent conversion
    with ThreadPoolExecutor(max_workers=MAX_CONVERSION_WORKERS) as executor:
        # Submit all conversion tasks
        future_to_file = {executor.submit(convert_single_file, file): file 
                         for file in uploaded_files}
        
        # Collect results as they complete
        for future in as_completed(future_to_file):
            result = future.result()
            if result:
                converted.append(result)
    
    return {
        'success': True,
        'converted': converted
    }

@app.route('/download/<path:filename>')
def download(filename):
    from urllib.parse import unquote
    # Decode URL-encoded filename (for non-ASCII chars)
    filename = unquote(filename)
    # Don't use secure_filename here as it breaks non-ASCII filenames
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name=filename)
    print(f"File not found: {filepath}")
    print(f"Available files: {os.listdir(app.config['UPLOAD_FOLDER'])}")
    return {'error': 'File not found', 'path': filepath}, 404

@app.route('/download-all')
def download_all():
    import zipfile
    import io
    from urllib.parse import unquote
    
    files_raw = request.args.get('files', '')
    files = [unquote(f.strip()) for f in files_raw.split(',')]
    if not files or files == ['']:
        return {'error': 'No files specified'}, 400
    
    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename in files:
            if not filename:
                continue
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(filepath):
                zf.write(filepath, filename)
            else:
                print(f"Warning: File not found: {filepath}")
                print(f"Available: {os.listdir(app.config['UPLOAD_FOLDER'])}")
    
    # Seek to beginning
    zip_buffer.seek(0)
    
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='books.zip'
    )

@app.route('/delete-pair', methods=['DELETE'])
def delete_file_pair():
    """Delete both original file (epub/mobi) and converted PDF"""
    from urllib.parse import unquote
    
    original = unquote(request.args.get('original', ''))
    pdf = unquote(request.args.get('pdf', ''))
    
    if not original or not pdf:
        return {'success': False, 'error': 'Missing original or pdf parameter'}, 400
    
    deleted = []
    
    try:
        # Delete PDF
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            deleted.append({'name': pdf, 'exists': True})
            print(f"Deleted PDF: {pdf_path}")
        else:
            deleted.append({'name': pdf, 'exists': False})
        
        # Delete original file (search for file with original name)
        upload_folder = app.config['UPLOAD_FOLDER']
        for filename in os.listdir(upload_folder):
            # Check if this file ends with the original filename
            if filename.endswith(f'_{original}'):
                original_path = os.path.join(upload_folder, filename)
                if os.path.exists(original_path):
                    os.remove(original_path)
                    deleted.append({'name': original, 'exists': True})
                    print(f"Deleted original: {original_path}")
                else:
                    deleted.append({'name': original, 'exists': False})
                break
        else:
            # File not found
            deleted.append({'name': original, 'exists': False})
        
        return {'success': True, 'deleted': deleted}
    except Exception as e:
        print(f"Error deleting file pair: {e}")
        return {'success': False, 'error': str(e)}, 500

@app.route('/delete-all', methods=['DELETE'])
def delete_all_files():
    """Delete all PDF files and original files"""
    try:
        upload_folder = app.config['UPLOAD_FOLDER']
        deleted_count = 0
        
        # Delete all PDF files
        for filename in os.listdir(upload_folder):
            if filename.endswith('.pdf'):
                filepath = os.path.join(upload_folder, filename)
                try:
                    os.remove(filepath)
                    deleted_count += 1
                    print(f"Deleted PDF: {filepath}")
                except Exception as e:
                    print(f"Error deleting {filepath}: {e}")
        
        # Delete all original files (pattern: uuid_originalname)
        for filename in os.listdir(upload_folder):
            if '_' in filename and (filename.endswith('.epub') or filename.endswith('.mobi')):
                filepath = os.path.join(upload_folder, filename)
                try:
                    os.remove(filepath)
                    deleted_count += 1
                    print(f"Deleted original: {filepath}")
                except Exception as e:
                    print(f"Error deleting {filepath}: {e}")
        
        return {'success': True, 'deleted': deleted_count}
    except Exception as e:
        print(f"Error in delete-all: {e}")
        return {'success': False, 'error': str(e)}, 500

if __name__ == '__main__':
    import argparse
    import threading
    import time
    
    # Ensure UTF-8 output on Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    parser = argparse.ArgumentParser(description='EPUB/MOBI to PDF Converter')
    parser.add_argument('--mode', choices=['web', 'desktop'], default='web',
                       help='运行模式：web=网页版，desktop=桌面版')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址 (仅 web 模式)')
    parser.add_argument('--port', type=int, default=5000, help='监听端口')
    args = parser.parse_args()
    
    print("=" * 60)
    print("EPUB/MOBI to PDF Converter")
    print("=" * 60)
    
    if args.mode == 'web':
        # Web mode: run Flask server
        print(f"[INFO] Starting web server on http://{args.host}:{args.port}")
        print("[INFO] Opening browser...")
        print("[INFO] Press Ctrl+C to stop")
        print("=" * 60)
        
        # Open browser after a short delay
        def open_browser():
            time.sleep(1.5)
            import webbrowser
            webbrowser.open(f'http://{args.host}:{args.port}')
        
        threading.Thread(target=open_browser, daemon=True).start()
        app.run(host=args.host, port=args.port, debug=False)
    
    else:
        # Desktop mode: run Flask in background + WebView window
        print("[INFO] Starting desktop application...")
        print(f"[INFO] Conversion Workers: {MAX_CONVERSION_WORKERS}")
        print(f"[INFO] Max Files: {MAX_FILES_PER_CONVERSION}")
        print("=" * 60)
        
        # Start Flask in background thread
        flask_thread = threading.Thread(
            target=lambda: app.run(host='127.0.0.1', port=args.port, debug=False, use_reloader=False),
            daemon=True
        )
        flask_thread.start()
        
        # Wait for Flask to start
        print("[INFO] Waiting for Flask to start...")
        time.sleep(2)
        
        try:
            import webview
            
            # Create WebView window
            window_kwargs = {
                'title': 'EPUB/MOBI to PDF Converter',
                'url': f'http://127.0.0.1:{args.port}',
                'width': 1200,
                'height': 800,
                'min_size': (800, 600),
                'resizable': True,
                'fullscreen': False,
                'text_select': True,
                'background_color': '#FFFFFF',
            }
            
            # Try to add icon if it exists
            if os.path.exists('icon.ico') and sys.platform == 'win32':
                try:
                    window_kwargs['icon'] = 'icon.ico'
                except:
                    pass
            
            print("[INFO] Creating WebView window...")
            window = webview.create_window(**window_kwargs)
            
            print("[INFO] Opening desktop window...")
            webview.start(
                debug=False,
                gui='edgechromium' if sys.platform == 'win32' else None,
            )
        
        except ImportError:
            print("[ERROR] pywebview not installed!")
            print("[INFO] Install with: pip install pywebview")
            print("[INFO] Or run in web mode: python app.py --mode web")
            sys.exit(1)

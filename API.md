# 📡 API 文档

## 端点概览

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | `/` | 主页（Web UI） | 无 |
| POST | `/convert` | 批量转换文件 | 无 |
| GET | `/download/<filename>` | 下载单个 PDF | 无 |
| GET | `/download-all` | 打包下载所有 PDF | 无 |

---

## 详细接口说明

### GET `/`

返回 Web 界面 HTML 页面。

**响应**: `text/html`

```bash
curl http://localhost:5000/
```

---

### POST `/convert`

批量转换 EPUB/MOBI 文件为 PDF。

**请求类型**: `multipart/form-data`

**参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `files` | File[] | 是 | EPUB/MOBI 文件列表（可多选） |

**请求示例**:
```bash
curl -X POST http://localhost:5000/convert \
  -F "files=@book1.epub" \
  -F "files=@book2.mobi"
```

**成功响应** (200 OK):
```json
{
  "success": true,
  "converted": [
    {
      "original": "book1.epub",
      "pdf": "book1.pdf"
    },
    {
      "original": "book2.mobi",
      "pdf": "book2.pdf"
    }
  ]
}
```

**失败响应** (400 Bad Request):
```json
{
  "success": false,
  "error": "No files uploaded"
}
```

**错误码**:
| 状态码 | 说明 |
|--------|------|
| 400 | 没有上传文件或文件格式不支持 |
| 413 | 文件超过大小限制（默认 100MB） |
| 500 | 转换过程出错 |

---

### GET `/download/<filename>`

下载转换后的单个 PDF 文件。

**参数**:
| 参数 | 类型 | 位置 | 描述 |
|------|------|------|------|
| `filename` | string | path | PDF 文件名（如 `book1.pdf`） |

**请求示例**:
```bash
curl -O http://localhost:5000/download/book1.pdf
```

**响应**: `application/pdf` (文件下载)

**错误响应** (404 Not Found):
```json
{
  "error": "File not found"
}
```

---

### GET `/download-all`

打包下载所有转换后的 PDF 文件为 ZIP。

**参数**:
| 参数 | 类型 | 位置 | 必填 | 描述 |
|------|------|------|------|------|
| `files` | string | query | 是 | PDF 文件名列表，逗号分隔 |

**请求示例**:
```bash
curl -O -J http://localhost:5000/download-all?files=book1.pdf,book2.pdf
```

**响应**: `application/zip` (文件下载)

**错误响应** (400 Bad Request):
```json
{
  "error": "No files specified"
}
```

---

## Python 客户端示例

### 基本使用

```python
import requests

# 上传并转换
files = [
    ('files', ('book1.epub', open('book1.epub', 'rb'))),
    ('files', ('book2.mobi', open('book2.mobi', 'rb'))),
]

response = requests.post('http://localhost:5000/convert', files=files)
result = response.json()

if result['success']:
    print("转换成功！")
    
    # 下载单个文件
    for converted in result['converted']:
        pdf_url = f"http://localhost:5000/download/{converted['pdf']}"
        pdf_response = requests.get(pdf_url)
        
        with open(converted['pdf'], 'wb') as f:
            f.write(pdf_response.content)
    
    # 或打包下载
    filenames = ','.join(c['pdf'] for c in result['converted'])
    zip_url = f"http://localhost:5000/download-all?files={filenames}"
    zip_response = requests.get(zip_url)
    
    with open('all_books.zip', 'wb') as f:
        f.write(zip_response.content)
```

### 带进度显示

```python
import requests
from tqdm import tqdm

def convert_with_progress(file_paths):
    """批量转换并显示进度"""
    
    files = []
    for path in file_paths:
        files.append(('files', (path.split('/')[-1], open(path, 'rb'))))
    
    print("上传文件中...")
    response = requests.post('http://localhost:5000/convert', files=files)
    result = response.json()
    
    if not result['success']:
        raise Exception(f"转换失败：{result['error']}")
    
    print(f"✓ 转换完成 {len(result['converted'])} 个文件")
    
    # 下载
    for converted in tqdm(result['converted'], desc="下载 PDF"):
        pdf_url = f"http://localhost:5000/download/{converted['pdf']}"
        pdf_response = requests.get(pdf_url)
        
        with open(converted['pdf'], 'wb') as f:
            f.write(pdf_response.content)
    
    print("✅ 全部完成！")

# 使用
convert_with_progress(['book1.epub', 'book2.mobi', 'book3.epub'])
```

---

## JavaScript 客户端示例

### 浏览器端上传

```javascript
async function convertFiles(fileList) {
    const formData = new FormData();
    
    for (let file of fileList) {
        formData.append('files', file);
    }
    
    try {
        const response = await fetch('/convert', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('转换成功:', result.converted);
            
            // 下载单个文件
            result.converted.forEach(item => {
                const link = document.createElement('a');
                link.href = `/download/${item.pdf}`;
                link.download = item.pdf;
                link.click();
            });
            
            // 或打包下载
            const filenames = result.converted.map(c => c.pdf).join(',');
            const zipLink = document.createElement('a');
            zipLink.href = `/download-all?files=${filenames}`;
            zipLink.download = 'books.zip';
            zipLink.click();
        }
    } catch (error) {
        console.error('转换失败:', error);
    }
}

// 使用
const fileInput = document.getElementById('fileInput');
fileInput.addEventListener('change', (e) => {
    convertFiles(e.target.files);
});
```

---

## cURL 命令集合

### 上传单个文件
```bash
curl -X POST http://localhost:5000/convert \
  -F "files=@mybook.epub"
```

### 上传多个文件
```bash
curl -X POST http://localhost:5000/convert \
  -F "files=@book1.epub" \
  -F "files=@book2.mobi" \
  -F "files=@book3.epub"
```

### 下载转换后的文件
```bash
# 单个文件
curl -O http://localhost:5000/download/mybook.pdf

# 打包下载
curl -O -J "http://localhost:5000/download-all?files=book1.pdf,book2.pdf"
```

### 完整流程（一行命令）
```bash
# 上传 → 转换 → 下载
RESULT=$(curl -s -X POST http://localhost:5000/convert -F "files=@book.epub") && \
PDF=$(echo $RESULT | jq -r '.converted[0].pdf') && \
curl -O http://localhost:5000/download/$PDF
```

---

## 错误处理

### 常见错误及解决方案

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| `No files uploaded` | 请求中没有文件 | 检查 `files` 参数 |
| `Unsupported file type` | 文件格式不支持 | 仅支持 .epub 和 .mobi |
| `File not found` | 文件不存在或已清理 | 转换后立即下载 |
| `Request Entity Too Large` | 文件超过 100MB | 修改 `MAX_CONTENT_LENGTH` |

### 错误响应格式

```json
{
  "success": false,
  "error": "错误描述信息"
}
```

---

## 性能优化建议

### 批量上传
- 推荐单次上传 < 20 个文件
- 总大小 < 500MB
- 超大文件分批上传

### 并发控制
```python
# 使用 requests.Session 复用连接
session = requests.Session()

# 批量上传
files = [...]
response = session.post('http://localhost:5000/convert', files=files)

# 批量下载
for pdf in result['converted']:
    response = session.get(f'http://localhost:5000/download/{pdf["pdf"]}')
```

### 超时设置
```python
requests.post(
    'http://localhost:5000/convert',
    files=files,
    timeout=300  # 5 分钟超时
)
```

---

## 安全建议

1. **生产环境** 添加认证机制
2. **文件验证** 检查文件魔数（magic number）
3. **速率限制** 防止滥用
4. **HTTPS** 加密传输
5. **CORS** 配置跨域策略

示例认证中间件：
```python
from functools import wraps
from flask import request, abort

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token != 'Bearer YOUR_SECRET_TOKEN':
            abort(401)
        return f(*args, **kwargs)
    return decorated

@app.route('/convert', methods=['POST'])
@require_auth
def convert():
    # ... 转换逻辑
```

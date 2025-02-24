import sys
import webbrowser
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import time

def highlight_differences(str1, str2):
    def highlight(char):
        return f'<span style="color: red">{char}</span>'
    result1 = []
    result2 = []
    max_len = max(len(str1), len(str2))
    for i in range(max_len):
        char1 = str1[i] if i < len(str1) else ''
        char2 = str2[i] if i < len(str2) else ''
        if i < len(str1) and i < len(str2) and char1 != char2:
            result1.append(highlight(char1))
            result2.append(highlight(char2))
        elif i >= len(str1):
            result2.append(highlight(char2))
        elif i >= len(str2):
            result1.append(highlight(char1))
        else:
            result1.append(char1)
            result2.append(char2)
    return ''.join(result1), ''.join(result2)

def calculate_percentage_difference(num1, num2):
    if num1 == 0:
        if num2 == 0:
            return 0.0
        else:
            return float('inf')
    else:
        return ((num2 / num1) - 1) * 100

def main(file1=None, file2=None, output_file='output.html'):
    if file1 is None or file2 is None:
        # 创建输入页面
        input_html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Input Numbers</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }
                textarea {
                    width: 100%;
                    height: 200px;
                    margin: 10px 0;
                    padding: 10px;
                }
                button {
                    padding: 10px 20px;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    cursor: pointer;
                }
                button:hover {
                    background-color: #45a049;
                }
                .container {
                    margin-bottom: 20px;
                }
            </style>
            <script>
                function submitNumbers() {
                    const file1Content = document.getElementById('file1').value;
                    const file2Content = document.getElementById('file2').value;
                    
                    fetch('http://localhost:8000/compare', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            file1: file1Content,
                            file2: file2Content
                        })
                    })
                    .then(response => {
                        // 获取新的URL并重定向
                        const newUrl = response.headers.get('Location');
                        if (newUrl) {
                            window.location.href = 'http://localhost:8000' + newUrl;
                        }
                    });
                }
            </script>
        </head>
        <body>
            <h1>输入数字进行比较</h1>
            <div class="container">
                <h3>文件1内容：</h3>
                <textarea id="file1" placeholder="请输入第一组数字，每行一个"></textarea>
            </div>
            <div class="container">
                <h3>文件2内容：</h3>
                <textarea id="file2" placeholder="请输入第二组数字，每行一个"></textarea>
            </div>
            <button onclick="submitNumbers()">比较</button>
        </body>
        </html>
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(input_html)
        
        # 构造绝对路径并打开浏览器
        output_path = os.path.abspath(output_file)
        print(f"HTML 文件生成路径: {output_path}")
        
        # 启动简单的HTTP服务器来处理提交的数据
        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.startswith('/compare_files'):
                    # 解析文件路径参数
                    query = urllib.parse.urlparse(self.path).query
                    params = urllib.parse.parse_qs(query)
                    file1 = params.get('file1', [''])[0]
                    file2 = params.get('file2', [''])[0]
                    
                    if file1 and file2:
                        # 调用文件对比模式
                        output_file = f'output_{int(time.time())}.html'
                        main(file1, file2, output_file)
                        
                        # 重定向到结果页面
                        self.send_response(302)
                        self.send_header('Location', f'/diff_output/{output_file}')
                        self.end_headers()
                        return
                
                elif self.path.endswith('.html'):
                    try:
                        with open('.' + self.path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        self.wfile.write(content.encode())
                    except:
                        self.send_error(404, 'File not found')

            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()

            def do_POST(self):
                if self.path == '/compare':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    
                    # 生成唯一的输出文件名
                    output_file = f'output_{int(time.time())}.html'
                    
                    # 将提交的内容保存到临时文件
                    with open('temp1.txt', 'w') as f1, open('temp2.txt', 'w') as f2:
                        f1.write(data['file1'])
                        f2.write(data['file2'])
                    
                    # 生成比较结果
                    main('temp1.txt', 'temp2.txt', output_file)
                    
                    # 返回重定向响应
                    self.send_response(302)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Location', f'/{output_file}')
                    self.end_headers()
        
        # 启动服务器
        server = HTTPServer(('localhost', 8000), RequestHandler)
        print("服务器启动在 http://localhost:8000")
        
        # 打开浏览器
        webbrowser.open('http://localhost:8000/output.html')
        
        # 开始服务器循环
        server.serve_forever()
        
    else:
        with open(file1, 'r') as f1, open(file2, 'r') as f2:
            html_content = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Number Comparison</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f4f4f4;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                    }
                    .content-wrapper {
                        width: 95%;
                        max-width: 1200px;
                        margin: 0 auto;
                    }
                    h1 {
                        color: #333;
                        text-align: center;
                        margin-bottom: 30px;
                    }
                    table {
                        width: 90%;
                        border-collapse: collapse;
                        table-layout: auto;
                        margin: 20px auto;
                        background-color: #fff;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                        border-radius: 8px;
                        overflow: hidden;
                    }
                    th, td {
                        border: 1px solid #ddd;
                        padding: 8px 12px;
                        text-align: center;
                        white-space: nowrap;
                    }
                    th {
                        background-color: #f0f7f0;
                        color: #2c5530;
                        font-weight: bold;
                    }
                    td {
                        max-width: 200px;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    }
                    td:first-child {
                        width: 60px;
                        min-width: 60px;
                    }
                    td:nth-child(2), td:nth-child(3) {
                        min-width: 100px;
                        max-width: 150px;
                    }
                    td:last-child {
                        width: 100px;
                        min-width: 100px;
                    }
                    tr:nth-child(even) {
                        background-color: #f9f9f9;
                    }
                    tr:hover {
                        background-color: #f5f5f5;
                    }
                    .highlight {
                        color: red;
                        font-weight: bold;
                    }
                    .page {
                        display: none;
                        width: 100%;
                    }
                    .page.active {
                        display: block;
                    }
                    .pagination {
                        margin: 20px 0;
                        text-align: center;
                    }
                    .pagination button, #pageInput {
                        padding: 8px 15px;
                        margin: 0 5px;
                        border: 1px solid #4CAF50;
                        background-color: white;
                        color: #4CAF50;
                        cursor: pointer;
                        border-radius: 4px;
                        transition: all 0.3s ease;
                    }
                    .pagination button:hover {
                        background-color: #4CAF50;
                        color: white;
                    }
                    #pageInput {
                        width: 60px;
                        text-align: center;
                    }
                    #filterControl {
                        background-color: white;
                        padding: 15px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                        margin-bottom: 20px;
                        text-align: center;
                    }
                    #filterControl label {
                        margin: 0 10px;
                        color: #333;
                    }
                    #thresholdInput {
                        padding: 5px;
                        width: 60px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        margin: 0 5px;
                    }
                    .hidden {
                        display: none;
                    }
                    #totalPages {
                        color: #666;
                        margin-left: 10px;
                    }
                </style>
                <script>
                    function showPage(pageNum) {
                        document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
                        document.getElementById('page' + pageNum).classList.add('active');
                    }
                    
                    function goToPage() {
                        const input = document.getElementById('pageInput');
                        const pageNum = parseInt(input.value);
                        const maxPage = parseInt(input.getAttribute('max'));
                        if (pageNum >= 1 && pageNum <= maxPage) {
                            showPage(pageNum);
                        } else {
                            alert('请输入有效的页码！');
                        }
                    }
                    
                    // 页面加载完成后执行初始化
                    window.onload = function() {
                        updateThreshold(); // 执行初始阈值检查
                    };
                    
                    function updateThreshold() {
                        const threshold = parseFloat(document.getElementById('thresholdInput').value);
                        const rows = document.querySelectorAll('table tr:not(:first-child)');
                        
                        rows.forEach(row => {
                            const percentageCell = row.querySelector('td:last-child');
                            const percentageText = percentageCell.textContent.replace('%', '');
                            const percentageValue = parseFloat(percentageText);
                            
                            if (Math.abs(percentageValue) > threshold) {
                                percentageCell.classList.add('highlight');
                            } else {
                                percentageCell.classList.remove('highlight');
                            }
                        });
                        
                        if (document.getElementById('filterHighlighted').checked) {
                            filterHighlightedRows();
                        }
                    }
                    
                    function filterHighlightedRows() {
                        const showOnlyHighlighted = document.getElementById('filterHighlighted').checked;
                        const threshold = parseFloat(document.getElementById('thresholdInput').value);
                        const pages = document.querySelectorAll('.page');
                        
                        pages.forEach(page => {
                            const rows = page.querySelectorAll('table tr:not(:first-child)');
                            let visibleRowCount = 0;
                            
                            rows.forEach(row => {
                                const diffCell = row.querySelector('td:last-child');
                                const diffText = diffCell.textContent;
                                const diffValue = diffText === 'Infinity' ? 
                                    Infinity : 
                                    parseFloat(diffText.replace('%', ''));
                                const hasHighlight = Math.abs(diffValue) > threshold;
                                
                                if (showOnlyHighlighted && !hasHighlight) {
                                    row.classList.add('hidden');
                                } else {
                                    row.classList.remove('hidden');
                                    visibleRowCount++;
                                }
                            });
                            
                            if (visibleRowCount === 0) {
                                page.classList.add('hidden');
                            } else {
                                page.classList.remove('hidden');
                            }
                        });
                    }
                </script>
            </head>
            <body>
                <div class="content-wrapper">
                    <h1>数值比较结果</h1>
                    <div id="filterControl">
                        <label>
                            差异阈值：<input type="number" id="thresholdInput" value="1" step="0.1" min="0" onchange="compareNumbers()">%
                        </label>
                        <label>
                            <input type="checkbox" id="filterHighlighted" onchange="compareNumbers()">
                            只显示差异大于阈值的行
                        </label>
                    </div>
                    <div class="pagination">
                        跳转到页码：<input type="number" id="pageInput" min="1" value="1">
                        <button onclick="goToPage()">跳转</button>
                        <span id="totalPages"></span>
                    </div>
                    """
            
            # 收集所有行
            all_rows = []
            line_num = 0
            for line1, line2 in zip(f1, f2):
                line_num += 1
                line1 = line1.strip()
                line2 = line2.strip()
                try:
                    num1 = float(line1)
                    num2 = float(line2)
                except ValueError:
                    print(f"Error: Invalid number in line {line_num}: {line1} or {line2}")
                    continue
                    
                highlighted1, highlighted2 = highlight_differences(line1, line2)
                percentage_diff = calculate_percentage_difference(num1, num2)
                if percentage_diff == float('inf'):
                    percentage_str = "Infinity"
                else:
                    percentage_str = f"{percentage_diff:.2f}%"
                
                row_html = f"""
                <tr>
                    <td>{line_num}</td>
                    <td>{highlighted1}</td>
                    <td>{highlighted2}</td>
                    <td>{percentage_str}</td>
                </tr>
                """
                all_rows.append(row_html)
                
            # 分页处理
            rows_per_page = 100
            total_pages = (len(all_rows) + rows_per_page - 1) // rows_per_page
            
            # 更新页码输入框的最大值和显示总页数
            html_content = html_content.replace('id="pageInput"', f'id="pageInput" max="{total_pages}"')
            html_content = html_content.replace('<span id="totalPages"></span>', f'<span id="totalPages">（共 {total_pages} 页）</span>')
            
            # 为每一页创建表格
            for page in range(total_pages):
                start_idx = page * rows_per_page
                end_idx = min((page + 1) * rows_per_page, len(all_rows))
                
                page_style = 'active' if page == 0 else ''
                html_content += f"""
                <div id="page{page + 1}" class="page {page_style}">
                <table>
                    <tr><th>Line</th><th>File 1</th><th>File 2</th><th>Percentage Difference</th></tr>
                    {''.join(all_rows[start_idx:end_idx])}
                </table>
                </div>
                """
                
            html_content += "</body></html>"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 构造绝对路径
        output_path = os.path.abspath(output_file)
        print(f"HTML 文件生成路径: {output_path}")
        
        # 尝试用 Chrome 浏览器打开
        chrome_path = 'open -a /Applications/Google\\ Chrome.app %s'  # macOS
        webbrowser.get(chrome_path).open_new_tab(output_path)

def paste_mode():
    print("Paste content for file 1, then press Ctrl-D to save:")
    file1_content = []
    while True:
        try:
            line = input()
            file1_content.append(line)
        except EOFError:
            break
    
    print("Paste content for file 2, then press Ctrl-D to save:")
    file2_content = []
    while True:
        try:
            line = input()
            file2_content.append(line)
        except EOFError:
            break
    
    # 保存内容到当前目录的临时文件
    current_dir = os.getcwd()
    with open(os.path.join(current_dir, "temp1.txt"), 'w') as f1, open(os.path.join(current_dir, "temp2.txt"), 'w') as f2:
        f1.write('\n'.join(file1_content))
        f2.write('\n'.join(file2_content))
    
    return os.path.join(current_dir, "temp1.txt"), os.path.join(current_dir, "temp2.txt")

# 定义动态模式的 HTML 内容
input_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Numbers Diff</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .content-wrapper {
            width: 95%;
            max-width: 1200px;
            margin: 0 auto;
        }
        .input-container {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }
        .input-section {
            flex: 1;
        }
        textarea {
            width: 100%;
            height: 300px;
            padding: 10px;
            font-family: monospace;
            border: 1px solid #ddd;
            border-radius: 4px;
            resize: vertical;
        }
        table {
            width: 90%;
            border-collapse: collapse;
            margin: 20px auto;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            overflow: hidden;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: center;
            white-space: nowrap;
        }
        th {
            background-color: #f0f4f8;
            color: #2c4058;
            font-weight: bold;
        }
        td {
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        td:first-child {
            width: 60px;
            min-width: 60px;
        }
        td:nth-child(2), td:nth-child(3) {
            min-width: 100px;
            max-width: 150px;
        }
        td:last-child {
            width: 100px;
            min-width: 100px;
        }
        .highlight {
            color: red;
            font-weight: bold;
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        h3 {
            color: #444;
            margin-bottom: 10px;
        }
        .page {
            display: none;
        }
        .page.active {
            display: block;
        }
        .pagination {
            margin: 20px 0;
            text-align: center;
        }
        .pagination button, #pageInput {
            padding: 8px 15px;
            margin: 0 5px;
            border: 1px solid #4CAF50;
            background-color: white;
            color: #4CAF50;
            cursor: pointer;
            border-radius: 4px;
            transition: all 0.3s ease;
        }
        .pagination button:hover {
            background-color: #4CAF50;
            color: white;
        }
        #pageInput {
            width: 60px;
            text-align: center;
        }
        #filterControl {
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            text-align: center;
        }
        #filterControl label {
            margin: 0 10px;
            color: #333;
        }
        #thresholdInput {
            padding: 5px;
            width: 60px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin: 0 5px;
        }
        .hidden {
            display: none;
        }
        #totalPages {
            color: #666;
            margin-left: 10px;
        }
    </style>
    <script>
        const ROWS_PER_PAGE = 100;
        
        function highlightDifferences(str1, str2) {
            if (str1 === str2) return [str1, str2];
            
            // 将数字转换为字符串并按小数点分割
            const parts1 = str1.toString().split('.');
            const parts2 = str2.toString().split('.');
            
            // 处理整数部分
            const int1 = parts1[0];
            const int2 = parts2[0];
            let highlightedInt1 = '';
            let highlightedInt2 = '';
            
            // 从右向左比较每个字符
            for (let i = 0; i < Math.max(int1.length, int2.length); i++) {
                const char1 = int1[int1.length - 1 - i] || '';
                const char2 = int2[int2.length - 1 - i] || '';
                
                if (char1 !== char2) {
                    highlightedInt1 = '<span class="highlight">' + char1 + '</span>' + highlightedInt1;
                    highlightedInt2 = '<span class="highlight">' + char2 + '</span>' + highlightedInt2;
                } else {
                    highlightedInt1 = char1 + highlightedInt1;
                    highlightedInt2 = char2 + highlightedInt2;
                }
            }
            
            // 处理小数部分
            let highlightedDec1 = '';
            let highlightedDec2 = '';
            if (parts1[1] || parts2[1]) {
                const dec1 = parts1[1] || '';
                const dec2 = parts2[1] || '';
                
                for (let i = 0; i < Math.max(dec1.length, dec2.length); i++) {
                    const char1 = dec1[i] || '';
                    const char2 = dec2[i] || '';
                    
                    if (char1 !== char2) {
                        highlightedDec1 += '<span class="highlight">' + char1 + '</span>';
                        highlightedDec2 += '<span class="highlight">' + char2 + '</span>';
                    } else {
                        highlightedDec1 += char1;
                        highlightedDec2 += char2;
                    }
                }
            }
            
            // 组合整数和小数部分
            const result1 = highlightedInt1 + (highlightedDec1 ? '.' + highlightedDec1 : '');
            const result2 = highlightedInt2 + (highlightedDec2 ? '.' + highlightedDec2 : '');
            
            return [result1, result2];
        }
        
        function compareNumbers() {
            const text1 = document.getElementById('input1').value;
            const text2 = document.getElementById('input2').value;
            const showOnlyHighlighted = document.getElementById('filterHighlighted').checked;
            const threshold = parseFloat(document.getElementById('thresholdInput').value);
            
            const lines1 = text1.split('\\n').filter(line => line.trim());
            const lines2 = text2.split('\\n').filter(line => line.trim());
            
            const maxLines = Math.max(lines1.length, lines2.length);
            let allRows = [];
            let visibleRows = 0;
            
            for (let i = 0; i < maxLines; i++) {
                const str1 = lines1[i] || '';
                const str2 = lines2[i] || '';
                const num1 = parseFloat(str1 || '0');
                const num2 = parseFloat(str2 || '0');
                
                let diff;
                if (num1 === 0 && num2 === 0) {
                    diff = 0;
                } else if (num1 === 0) {
                    diff = Infinity;
                } else {
                    diff = ((num2 - num1) / Math.abs(num1)) * 100;
                }
                
                const isDifferent = Math.abs(diff) > threshold;
                const diffClass = isDifferent ? 'highlight' : '';
                const diffText = isFinite(diff) ? diff.toFixed(2) + '%' : 'Infinity';
                
                // 如果只显示差异行且当前行无差异，则跳过
                if (showOnlyHighlighted && !isDifferent) {
                    continue;
                }
                
                const [highlighted1, highlighted2] = highlightDifferences(str1, str2);
                
                allRows.push(`
                    <tr>
                        <td>${i + 1}</td>
                        <td>${highlighted1}</td>
                        <td>${highlighted2}</td>
                        <td class="${diffClass}">${diffText}</td>
                    </tr>
                `);
                visibleRows++;
            }
            
            const totalPages = Math.ceil(visibleRows / ROWS_PER_PAGE);
            document.getElementById('totalPages').textContent = `（共 ${totalPages} 页）`;
            document.getElementById('pageInput').max = totalPages;
            
            // 创建分页
            let resultHtml = '';
            for (let page = 0; page < totalPages; page++) {
                const pageStyle = page === 0 ? 'active' : '';
                resultHtml += `
                    <div id="page${page + 1}" class="page ${pageStyle}">
                        <table>
                            <tr>
                                <th>行号</th>
                                <th>File 1</th>
                                <th>File 2</th>
                                <th>差异 (%)</th>
                            </tr>
                            ${allRows.slice(page * ROWS_PER_PAGE, (page + 1) * ROWS_PER_PAGE).join('')}
                        </table>
                    </div>
                `;
            }
            
            document.getElementById('result').innerHTML = resultHtml;
        }
        
        function showPage(pageNum) {
            document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
            document.getElementById('page' + pageNum).classList.add('active');
        }
        
        function goToPage() {
            const input = document.getElementById('pageInput');
            const pageNum = parseInt(input.value);
            const maxPage = parseInt(input.getAttribute('max'));
            if (pageNum >= 1 && pageNum <= maxPage) {
                showPage(pageNum);
            } else {
                alert('请输入有效的页码！');
            }
        }
    </script>
</head>
<body>
    <div class="content-wrapper">
        <h1>Numbers</h1>
        <div class="input-container">
            <div class="input-section">
                <h3>File 1：</h3>
                <textarea id="input1" 
                    placeholder="请输入第一个文件的数字，每行一个" 
                    oninput="compareNumbers()"></textarea>
            </div>
            <div class="input-section">
                <h3>File 2：</h3>
                <textarea id="input2" 
                    placeholder="请输入第二个文件的数字，每行一个" 
                    oninput="compareNumbers()"></textarea>
            </div>
        </div>
        
        <div id="filterControl">
            <label>
                差异阈值：<input type="number" id="thresholdInput" value="1" step="0.1" min="0" onchange="compareNumbers()">%
            </label>
            <label>
                <input type="checkbox" id="filterHighlighted" onchange="compareNumbers()">
                只显示差异大于阈值的行
            </label>
        </div>
        
        <div class="pagination">
            跳转到页码：<input type="number" id="pageInput" min="1" value="1">
            <button onclick="goToPage()">跳转</button>
            <span id="totalPages">（共 0 页）</span>
        </div>
        
        <div id="result"></div>
    </div>
</body>
</html>
"""

# 定义请求处理器
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/compare_files'):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            file1 = params.get('file1', [''])[0]
            file2 = params.get('file2', [''])[0]
            
            if file1 and file2:
                output_file = os.path.join(script_dir, 'diff_output', f'output_{int(time.time())}.html')
                main(file1, file2, output_file)
                
                self.send_response(302)
                self.send_header('Location', f'/diff_output/{os.path.basename(output_file)}')
                self.end_headers()
                return
        
        elif self.path.endswith('.html'):
            try:
                # 使用script_dir来构建完整的文件路径
                file_path = os.path.join(script_dir, self.path.lstrip('/'))
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(content.encode())
            except:
                self.send_error(404, 'File not found')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path == '/compare':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # 使用script_dir来存储临时文件和输出文件
            temp1_path = os.path.join(script_dir, 'temp1.txt')
            temp2_path = os.path.join(script_dir, 'temp2.txt')
            output_file = os.path.join(script_dir, 'diff_output', f'output_{int(time.time())}.html')
            
            with open(temp1_path, 'w') as f1, open(temp2_path, 'w') as f2:
                f1.write(data['file1'])
                f2.write(data['file2'])
            
            main(temp1_path, temp2_path, output_file)
            
            self.send_response(302)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Location', f'/diff_output/{os.path.basename(output_file)}')
            self.end_headers()

if __name__ == "__main__":
    # 获取当前Python文件所在的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if '--file' in sys.argv or '-f' in sys.argv:
        if len(sys.argv) < 4:
            file1 = input("Please enter the path for the first file: ")
            file2 = input("Please enter the path for the second file: ")
            output_file = os.path.join(script_dir, 'output.html')
        else:
            file1 = sys.argv[2]
            file2 = sys.argv[3]
            output_file = sys.argv[4] if len(sys.argv) == 5 else os.path.join(script_dir, 'output.html')
        main(file1, file2, output_file)
    elif '--paste' in sys.argv or '-p' in sys.argv:
        file1, file2 = paste_mode()
        main(file1, file2)
    else:
        # 在Python文件所在目录下创建diff_output文件夹
        diff_output_dir = os.path.join(script_dir, 'diff_output')
        os.makedirs(diff_output_dir, exist_ok=True)
        
        dynamic_html_path = os.path.join(diff_output_dir, 'dynamic.html')
        with open(dynamic_html_path, 'w', encoding='utf-8') as f:
            f.write(input_html)
        
        # 启动服务器
        server = HTTPServer(('localhost', 8000), RequestHandler)
        print("服务器启动在 http://localhost:8000")
        
        # 打开浏览器
        webbrowser.open('http://localhost:8000/diff_output/dynamic.html')
        
        # 开始服务器循环
        server.serve_forever()
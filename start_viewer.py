"""
本地HTTP服务器 - 用于查看viewer.html，避免CORS问题
"""
import http.server
import socketserver
import webbrowser
import os
import threading
import time

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # 添加CORS头
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def log_message(self, format, *args):
        # 简化日志输出
        if args[1] == '200':
            return
        super().log_message(format, *args)


def open_browser():
    """延迟打开浏览器"""
    time.sleep(1)
    webbrowser.open(f'http://localhost:{PORT}/viewer.html')


def start_server():
    """启动服务器"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    Handler = MyHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("=" * 60)
        print(f"🌐 论文查看器服务器已启动")
        print(f"📍 访问地址: http://localhost:{PORT}/viewer.html")
        print("=" * 60)
        print("\n浏览器将自动打开...")
        print("按 Ctrl+C 停止服务器\n")
        
        # 在新线程中打开浏览器
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n服务器已停止")


if __name__ == "__main__":
    start_server()

import os

import socket
import hashlib
import uuid
import threading
import time
from werkzeug.utils import secure_filename
from flask import Flask, request, session, jsonify, send_file, render_template, send_from_directory

from .SenderConfig import sender_config

app = Flask(__name__)
app.secret_key = uuid.uuid4().hex
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024 * 1024 

os.makedirs(sender_config.upload_folder, exist_ok=True)
os.makedirs(sender_config.speed_test_folder, exist_ok=True)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {
        'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 
        'mp4', 'doc', 'docx', 'mp3', 'avi', 'mov', 'ppt', 'pptx',
        'xls', 'xlsx', 'rar', '7z', 'tar', 'gz'
    }
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def verify_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest() == sender_config.password

@app.route('/')
def index():
    local_ip = get_local_ip()
    return render_template("index.html", local_ip=local_ip)

@app.route('/favicon.ico')
def favicon():
    print(os.path.abspath(r"src\Sender\static"))
    return send_from_directory(os.path.abspath(r"src\Sender\static"), 'favicon.ico')

@app.route('/upload_chunk', methods=['POST'])
def upload_chunk():
    try:
        file_id = request.form.get('file_id')
        if not file_id:
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数: file_id'
                }), 400
        chunk_index = request.form.get('chunk_index')
        if not chunk_index:
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数: chunk_index'
                }), 400
        if not chunk_index.isdigit():
            return jsonify({
                'status': 'error',
                'message': '参数 chunk_index 必须是整数'
                }), 400
        chunk_index = int(chunk_index)
        total_chunks = request.form.get('total_chunks')
        if not total_chunks:
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数: total_chunks'
                }), 400
        if not total_chunks.isdigit():
            return jsonify({
                'status': 'error',
                'message': '参数 total_chunks 必须是整数'
                }), 400
        filename = request.form.get('file_name')
        if not filename:
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数: file_name'
                }), 400
        file_name = secure_filename(filename)
        chunk_file = request.files['chunk']
        
        temp_dir = os.path.join(sender_config.upload_folder, 'temp', file_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        chunk_path = os.path.join(temp_dir, f'chunk_{chunk_index:06d}')
        chunk_file.save(chunk_path)
        
        return jsonify({
            'status': 'success',
            'chunk_index': chunk_index,
            'message': f'分块 {chunk_index + 1}/{total_chunks} 上传成功'
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'分块上传失败: {str(e)}'
        }), 500

@app.route('/complete_upload', methods=['POST'])
def complete_upload():
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        file_name = secure_filename(data.get('file_name'))
        
        temp_dir = os.path.join(sender_config.upload_folder, 'temp', file_id)
        final_path = os.path.join(sender_config.upload_folder, file_name)
        
        if os.path.exists(final_path):
            name, ext = os.path.splitext(file_name)
            file_name = f"{name}_{int(time.time())}{ext}"
            final_path = os.path.join(sender_config.upload_folder, file_name)
        
        chunk_files = []
        for f in os.listdir(temp_dir):
            if f.startswith('chunk_'):
                chunk_files.append(f)
        chunk_files.sort()
        
        with open(final_path, 'wb') as output_file:
            for chunk_file in chunk_files:
                chunk_path = os.path.join(temp_dir, chunk_file)
                with open(chunk_path, 'rb') as chunk:
                    output_file.write(chunk.read())
        
        import shutil
        shutil.rmtree(temp_dir)
        
        file_size = os.path.getsize(final_path)
        
        return jsonify({
            'status': 'success',
            'file_name': file_name,
            'file_size': file_size,
            'message': '文件上传并合并完成'
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'文件合并失败: {str(e)}'
        }), 500

@app.route('/speed_test', methods=['POST'])
def speed_test():
    try:
        data = request.get_data()
        return jsonify({
            'status': 'success',
            'data_received': len(data)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/check_test_file', methods=['GET'])
def check_test_file():
    try:
        filename = "押尾光太郎 - 風の詩.flac"
        test_filepath = os.path.join(sender_config.speed_test_folder, filename)
        if os.path.exists(test_filepath):
            file_size = os.path.getsize(test_filepath)
            return jsonify({
                'exists': True,
                'filename': filename,
                'size': file_size,
                'size_formatted': format_file_size(file_size)
            })
        else:
            return jsonify({
                'exists': False,
                'message': '测试文件不存在,请先上传20MB的测试文件'
            })
    except Exception as e:
        return jsonify({'error': f'检查测试文件失败: {e}'}), 500

@app.route('/download_test', methods=['GET'])
def download_test():
    try:
        filename = "押尾光太郎 - 風の詩.flac"
        test_filepath = os.path.join(sender_config.speed_test_folder, filename)
        if os.path.exists(test_filepath):
            return send_file(os.path.abspath(test_filepath), as_attachment=True)
        else:
            return jsonify({'error': '测试文件不存在'}), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500    

def format_file_size(bytes):
    if bytes == 0:
        return "0 B"
    sizes = ["B", "KB", "MB", "GB"]
    i = 0
    while bytes >= 1024 and i < len(sizes) - 1:
        bytes /= 1024.0
        i += 1
    return f"{bytes:.2f} {sizes[i]}"

@app.route('/files')
def list_files():
    try:
        files = []
        for filename in os.listdir(sender_config.upload_folder):
            file_path = os.path.join(sender_config.upload_folder, filename)
            if os.path.isfile(file_path):
                files.append({
                    'name': filename,
                    'size': os.path.getsize(file_path),
                    'modified': os.path.getmtime(file_path)
                })
        
        files.sort(key=lambda x: x['modified'], reverse=True)
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': f'获取文件列表失败: {e}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(sender_config.upload_folder, filename)
        file_path = os.path.abspath(file_path)
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404
        
        return send_file(file_path, as_attachment=True)
    
    except Exception as e:
        return jsonify({'error': f'下载失败: {e}'}), 500

@app.route('/verify-password', methods=['POST'])
def verify_password_route():
    try:
        data = request.get_json()
        password = data.get('password', '')
        if verify_password(password):
            session['authenticated'] = True
            return jsonify({'success': True, 'message' : '密码正确'})
        else:
            return jsonify({'success': False, 'error': '密码错误'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': f'验证失败: {e}'}), 500

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    if not session.get('authenticated', False):
        return jsonify({'success': False, 'error': '请先登录'}), 401
    try:
        file_path = os.path.join(sender_config.upload_folder, filename)
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        os.remove(file_path)
        return jsonify({'success': True, 'message': '文件已删除'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'删除失败: {e}'}), 500

def start_server(host='0.0.0.0', port=sender_config.port):
    local_ip = get_local_ip()
    print(f"{'='*60}")
    print("🚀 文件传输系统")
    print(f"{'='*60}")
    print(f"📧 本机访问: http://localhost:{port}")
    print(f"🌐 局域网访问: http://{local_ip}:{port}")
    print(f"💾 上传目录: {os.path.abspath(sender_config.upload_folder)}")
    print(f"{'='*60}")
    print("按 Ctrl+C 停止服务器\n")
    try:
        from waitress import serve
        serve(app, host=host, port=port, threads=8)
    except ImportError:
        app.run(host=host, port=port, debug=False, threaded=True)
    # app.run(host=host, port=port, debug=True, threaded=True)

if __name__ == '__main__':
    start_server()
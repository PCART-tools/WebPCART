from flask import Blueprint, jsonify, request, send_from_directory, send_file
import os
import json
import zipfile
from io import BytesIO

project_bp = Blueprint('project', __name__)

PROJECTS_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'projects')
project = None

if not os.path.exists(PROJECTS_ROOT):
    os.makedirs(PROJECTS_ROOT)

# 获取项目
@project_bp.route('/project', methods=['GET'])
def get_projects():
    return jsonify({
        "project": project,
        "status": "success"
    })

# 添加新项目
@project_bp.route('/project', methods=['POST'])
def set_project():
    global project
    data = request.get_json()
    path = data.get('path')

    if not path:
        return jsonify({
            "message": "Path is required",
            "status": "error"
        }), 400
    
    project = path
    project_dir = os.path.join(PROJECTS_ROOT, path)

    # 清空原项目
    if os.path.exists(PROJECTS_ROOT):
        for item in os.listdir(PROJECTS_ROOT):
            item_path = os.path.join(PROJECTS_ROOT, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                import shutil
                shutil.rmtree(item_path)

    if not os.path.exists(project_dir):
        os.makedirs(project_dir)

    return jsonify({
        "message": "Project added successfully",
        "status": "success",
        "path": project
    })

@project_bp.route('/project/upload', methods=['POST'])
def upload_file():
    try:
        project_name = request.form.get('projectName')
        files = request.files.getlist('files')

        project_dir = os.path.join(PROJECTS_ROOT, project_name)
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)

        for i, file in enumerate(files):
            if file and file.filename:
                relative_path = request.form.get(f'paths[{i}]')

                if relative_path:
                    if relative_path.startswith(project_name + '/'):
                        relative_path = relative_path[len(project_name) + 1:]

                    file_dir = os.path.join(project_dir, os.path.dirname(relative_path))
                    if not os.path.exists(file_dir):
                        os.makedirs(file_dir)
                    
                    file_path = os.path.join(project_dir, relative_path)
                    file.save(file_path)
                else:
                    file_path = os.path.join(project_dir, file.filename)
                    file.save(file_path)

        return jsonify({
            "message": f"{len(files)} Files uploaded successfully",
            "status": "success"
        })
    
    except Exception as e:
        return jsonify({
            "message": f"upload failed {str(e)}",
            "status": "error"
            }), 400

# 获取项目树
@project_bp.route('/project/tree', methods=['POST'])
def get_project_tree():
    data = request.get_json()
    project_name = data.get('name')

    if not project_name:
        return jsonify({
            "message": "project_name is required", 
            "status": "error"
        }), 400
    
    root_path = os.path.join(PROJECTS_ROOT, project_name)

    if not os.path.exists(root_path):
        return jsonify({
            "message": "Project does not exist", 
            "status": "error"
        }), 400

    # 递归构建项目树
    def build_tree(path):
        if not os.path.exists(path):
            return None
    
        name = os.path.basename(path)
        if os.path.isfile(path):
            return {"name": name, "type": "file"}
        elif os.path.isdir(path):
            children = []

            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    child = build_tree(item_path)
                    if child:
                        children.append(child)
            except PermissionError:
                pass

            return {"name": name, "type": "directory", "children": children}
        
        return None
    
    tree = build_tree(root_path)
    return jsonify({
        "tree": tree,
        "status": "success"
    })

# 下载项目
@project_bp.route('/project/download', methods=['POST'])
def download_file():
    try:
        data = request.get_json()
        project_name = data.get('projectName')
        path = data.get('path')
        item_type = data.get('type')

        if not project_name or not path:
            return jsonify({
                "message": "projectName and path are required",
                "status": "error"
            }), 400
        
        project_dir = os.path.join(PROJECTS_ROOT, project_name)
        target_path = os.path.join(project_dir, path)

        if not os.path.exists(target_path):
            return jsonify({
                "message": "File does not exist",
                "status": "error"
            }), 400
        
        if item_type == "file":
            directory = os.path.dirname(target_path)
            filename = os.path.basename(target_path)
            return send_from_directory(directory, filename, as_attachment=True)
        else:
            memory_file = BytesIO()
            with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(target_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, project_dir)
                        zipf.write(file_path, relative_path)

            memory_file.seek(0)

            return send_file(memory_file,
                            mimetype='application/zip',
                            as_attachment=True,
                            download_name=f'{os.path.basename(path)}.zip')
    except Exception as e:
        return jsonify({
            "message": "Download failed:" + str(e),
            "status": "error"
        }), 400    


# 加载代码文件
@project_bp.route('/project/load_file', methods=['POST'])
def get_file_content():
    try:
        data = request.get_json()
        project_name = data.get('projectName')
        file_path = data.get('filePath')
        
        if not project_name or not file_path:
            return jsonify({
                "message": "projectName and filePath are required",
                "status": "error"
            }), 400
        
        project_dir = os.path.join(PROJECTS_ROOT, project_name)
        target_path = os.path.join(project_dir, file_path)

        if not os.path.exists(target_path):
            return jsonify({
                "message": "file does not exist",
                "status": "error"
            }), 404
        
        with open(target_path, 'r', encoding='utf-8') as file:
            content = file.read()

        return jsonify({
            "content": content,
            "status": "success"
        })
    except UnicodeDecodeError:
        return jsonify({
            "message": "file is not utf-8 encoded",
            "status": "error"
        }), 400
    except Exception as e:
        return jsonify({
            "message": "Failed to read file: " + str(e),
            "status": "error"
        }), 500
    
# 保存代码文件
@project_bp.route('/project/save_file', methods=['POST'])
def save_file():
    try:
        data = request.get_json()
        project_name = data.get('projectName')
        file_path = data.get('filePath')
        content = data.get('content')

        if not project_name or not file_path:
            return jsonify({
                "message": "projectName and filePath are required",
                "status": "error"
            }), 400
        
        project_dir = os.path.join(PROJECTS_ROOT, project_name)
        target_path = os.path.join(project_dir, file_path)
        target_dir = os.path.dirname(target_path)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        with open(target_path, 'w', encoding='utf-8') as file:
            file.write(content)

        return jsonify({
            "message": "file saved successfully",
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "message": "Failed to save file: " + str(e),
            "status": "error"
        }), 500

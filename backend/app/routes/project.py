from flask import Blueprint, jsonify, request
import os
import json

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
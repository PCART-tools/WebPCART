from flask import Blueprint, jsonify, request, send_from_directory, send_file
import os
import re
from typing import Dict, List, Any

from ..common import get_logger

logger = get_logger('report')
report_bp = Blueprint('report', __name__)

# 解析兼容性报告
class ReportParser:
    def __init__(self, report_path: str):
        self.report_path = report_path
        self.data = {}

    # 解析报告
    def parse_report(self) -> Dict[str, Any]:

        with open(self.report_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析总体统计信息
        stat_info = self._parse_stat_info(content)

        # 解析具体API调用信息
        api_details = self._parse_api_details(content)

        return{
            "stat_info": stat_info,
            "api_details": api_details
        }
    
    # 解析总体统计信息
    def _parse_stat_info(self, content: str) -> Dict[str, Any]:
        stats = {}

        # 正则匹配获取数据
        total_files_match = re.search(r'Total File Number: (\d+)', content)
        if total_files_match:
            stats['total_file_number'] = int(total_files_match.group(1))
        
        total_api_match = re.search(r'Total \w+ Invoked API Number: (\d+)', content)
        if total_api_match:
            stats['total_api_number'] = int(total_api_match.group(1))
        
        not_covered_match = re.search(r'Not Covered \w+ Invoked API Number: (\d+)/(\d+)', content)
        if not_covered_match:
            stats['not_covered_number'] = int(not_covered_match.group(1))
        
        covered_match = re.search(r'Covered \w+ Invoked API Number: (\d+)/(\d+)', content)
        if covered_match:
            stats['covered_number'] = int(covered_match.group(1))
        
        compatible_match = re.search(r'Compatible \w+ Invoked API Number: (\d+)/(\d+)', content)
        if compatible_match:
            stats['compatible_number'] = int(compatible_match.group(1))
        
        unknown_compatible_match = re.search(r'Unknown Compatible \w+ Invoked API Number: (\d+)/(\d+)')
        if unknown_compatible_match:
            stats['unknown_compatible_number'] = int(unknown_compatible_match.group(1))

        incompatible_match = re.search(r'Incompatible \w+ Invoked API Number: (\d+)/(\d+)', content)
        if incompatible_match:
            stats['incompatible_number'] = int(incompatible_match.group(1))

        successfully_repaired_match = re.search(r'-> Successfully Repaired \w+ Invoked API number: (\d+)/(\d+)', content)
        if successfully_repaired_match:
            stats['successfully_repaired_number'] = int(successfully_repaired_match.group(1))
        
        failed_repair_match = re.search(r'-> Failed to Repair \w+ Invoked API Number: (\d+)/(\d+)', content)
        if failed_repair_match:
            stats['failed_repair_number'] = int(failed_repair_match.group(1))
        
        unknown_repair_match = re.search(r'-> Unknown Repair Status \w+ Invoked API Number: (\d+)/(\d+)', content)
        if unknown_repair_match:
            stats['unknown_repair_status_number'] = int(unknown_repair_match.group(1))
        
        return stats       
    
    # 解析API详细信息
    def _parse_api_details(self, content:str) -> List[Dict[str, Any]]:
        api_details = []

        # 提取库名
        lib_name = "library"  
        
        total_api_match = re.search(r'Total (\w+) Invoked API Number:', content)
        if total_api_match:
            lib_name = total_api_match.group(1)

        file_pattern = r'=+\n\|.*?File #(\d+): (.*?) has (\d+) \w+ Invoked API\(s\)\s*\|\n=+((?:.|\n)*?)\n(?======================================================|=+\n|$)'
        file_matches = re.findall(file_pattern, content, re.MULTILINE)

        for file_num, file_path, api_count_str, file_content in file_matches:
            # 获取api调用信息
            api_calls = self._extract_api_calls(file_content, lib_name) 

            for j, api_call in enumerate(api_calls):
                api_details.append({
                    'file_id': f"{file_num}-{j+1}",
                    'file_path': file_path.strip(),
                    'api_index': j+1,
                    'invoked_api': api_call.get('invoked_api'),
                    'location': api_call.get('location'),
                    'coverage': api_call.get('coverage'),
                    'definition_v1': api_call.get('definition_v1'),
                    'definition_v2': api_call.get('definition_v2'),
                    'compatible': api_call.get('compatible'),
                    'compatibility_status': api_call.get('compatibility_status')
                }) 

        return api_details
    
    # 提取一个文件中的调用信息
    def _extract_api_calls(self, content: str, lib_name: str) -> List[Dict[str, Any]]:
        api_calls = []

        api_pattern = r'\| Invoked API #\d+: ([^\n\r]+?)\s*\|\s*\|\s*Location: (.*?)\s*\|\s*\|\s*Coverage: (.*?)\s*\|\s*\|\s*Definition @(.*?) <static>: {(.*?)}\s*\|\s*\|\s*Definition @(.*?) <static>: {(.*?)}\s*\|\s*\|\s*Compatible: (.*?)\s*\|'
        matches = re.findall(api_pattern, content, re.DOTALL)
        
        for match in matches:
            invoked_api, location, coverage, ver1, def1, ver2, def2, compatible_str = match
            
            # 清理数据
            invoked_api = invoked_api.strip().replace('\n', '').replace('|', '').strip()
            location = location.replace('At Line', '').replace('in', '').strip()
            coverage = coverage.strip()
            compatible = compatible_str.strip().lower() == 'yes'
            compatibility_status = "compatible" if compatible else "incompatible"
            definition_v1 = def1.strip().replace("'", "").replace('"', '')
            definition_v2 = def2.strip().replace("'", "").replace('"', '')
            
            api_calls.append({
                'invoked_api': invoked_api,
                'location': location,
                'coverage': coverage,
                'definition_v1': definition_v1,
                'definition_v2': definition_v2,
                'compatible': compatible,
                'compatibility_status': compatibility_status
            })

    # 根据条件过滤数据
    def filter_data(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        parsed_data = self.parse_report()
        
        filtered_details = parsed_data['api_details']
        
        # 按兼容性状态过滤
        if 'compatibility_status' in filters:
            status = filters['compatibility_status']
            if status in ['compatible', 'incompatible', 'unknown']:
                filtered_details = [
                    detail for detail in filtered_details
                    if detail['compatibility_status'] == status
                ]
        
        # 按文件路径过滤
        if 'file_path' in filters and filters['file_path']:
            file_path = filters['file_path']
            filtered_details = [
                detail for detail in filtered_details
                if file_path.lower() in detail['file_path'].lower()
            ]

        return {
            "stat_info": parsed_data['stat_info'],
            "api_details": filtered_details
        }
    
# 获取项目报告
@report_bp.route('/report/<project_name>', methods=['GET'])
def get_project_report(project_name):
    try:
        # 构建报告路径
        project_reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'pcart', 'Report')
        report_filename = f"{project_name}.txt"
        report_path = os.path.join(project_reports_dir, report_filename)
        
        if not os.path.exists(report_path):
            return jsonify({
                "message": f"Report {project_name}.txt does not exist",
                "status": "error"
            }), 404
        
        # 解析报告
        parser = ReportParser(report_path)
        data = parser.parse_report()
        
        return jsonify({
            "data": data,
            "status": "success",
            "report_name": report_filename
        })
    except Exception as e:
        return jsonify({
            "message": f"Failed to parse report: {str(e)}",
            "status": "error"
        }), 500



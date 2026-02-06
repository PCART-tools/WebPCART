from flask import Blueprint, jsonify, request, send_from_directory, send_file
import os
import re
from typing import Dict, List, Any

from ..common import get_logger, get_work_dir

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
        api_details = self._parse_api_calls(content)

        return{
            "stat_info": stat_info,
            "api_details": api_details
        }
    
    # 解析总体统计信息
    def _parse_stat_info(self, content: str) -> Dict[str, Any]:
        stats = {}
        
        try:
            if not content:
                return stats
            
            logger.info("start parse_stat_info")
                
            # 逐个测试每个正则表达式
            patterns = {
                'total_file_number': r'Total File Number: (\d+)',
                'total_api_number': r'Total [^:]+ Invoked API Number: (\d+)',
                'not_covered_number': r'Not Covered [^:]+ Invoked API Number: (\d+)/(\d+)',
                'covered_number': r'Covered [^:]+ Invoked API Number: (\d+)/(\d+)',
                'compatible_number': r'Compatible [^:]+ Invoked API Number: (\d+)/(\d+)',
                'unknown_compatible_number': r'Unknown Compatible [^:]+ Invoked API Number: (\d+)/(\d+)',
                'incompatible_number': r'Incompatible [^:]+ Invoked API Number: (\d+)/(\d+)',
                'successfully_repaired_number': r'-> Successfully Repaired [^:]+ Invoked API number: (\d+)/(\d+)',
                'failed_repair_number': r'-> Failed to Repair [^:]+ Invoked API Number: (\d+)/(\d+)',
                'unknown_repair_status_number': r'-> Unknown Repair Status [^:]+ Invoked API Number: (\d+)/(\d+)'
            }
            
            for key, pattern in patterns.items():
                try:
                    match = re.search(pattern, content)
                    if match:
                        stats[key] = int(match.group(1))
                        logger.debug(f"Matched {key}: {match.group(1)}")
                except Exception as e:
                    logger.error(f"Error parsing {key} with pattern {pattern}: {e}")

            logger.info("end parse_stat_info")     
        except Exception as e:
            logger.error(f"Error in _parse_stat_info: {e}")
            raise
            
        return stats       
    
    # 解析API详细信息
    def _parse_api_calls(self, content: str) -> List[Dict[str, Any]]:
        api_calls = []

        # 分割每个API调用块
        api_blocks = re.split(r'\n(?=\| Invoked API #)', content)

        logger.info(f"api_blocks size: {len(api_blocks)}")
        
        for block in api_blocks[1:]:
            # 查找API调用行
            invoked_api_match = re.search(r'\| Invoked API #\d+: ([^\n\r]+)', block)
            if not invoked_api_match:
                continue
                
            invoked_api = invoked_api_match.group(1).strip().replace('|', '').strip()
            
            # 查找位置信息
            location_match = re.search(r'Location: At Line (.+?) in (.+)', block)
            location = ""
            if location_match:
                line_num = location_match.group(1).strip()
                file_path = location_match.group(2).strip()
                file_path = file_path.rstrip('|').strip()
                location = f"{line_num} in {file_path}"
            
            # 查找覆盖
            coverage_match = re.search(r'Coverage: (.+)', block)
            coverage = coverage_match.group(1).strip()
            coverage = coverage.rstrip('|').strip()

            api_call_dict = {
                'invoked_api': invoked_api,
                'location': location,
                'coverage': coverage,
            }

            if coverage == 'Yes':  
                # 查找版本定义
                def_matches = re.findall(r'Definition @[^<]+ <\w+>: (\{.*?\}|\(.*?\))', block, re.DOTALL)
                def1 = def_matches[0].strip()
                def1 = re.sub(r'\s*\|\s*\n\s*\|\s*', '', def1).rstrip('|').strip()
                def2 = def_matches[1].strip()
                def2 = re.sub(r'\s*\|\s*\n\s*\|\s*', '', def2).rstrip('|').strip()
                
                # 查找兼容性状态
                compatible_match = re.search(r'Compatible: (.+)', block)
                compatible_str = compatible_match.group(1).strip()
                compatible_str = compatible_str.rstrip('|').strip()

                logger.info(compatible_str)

                compatible = compatible_str.lower() == 'yes'
                
                # 查找修复信息
                if compatible == False:
                    repair_match = re.search(r'Repair <(Successful|Failed|Unknown)>: (.+)', block)
                    repair_status = None
                    repair_result = ""
                    if repair_match:
                        repair_status = repair_match.group(1).lower()
                        repair_result = repair_match.group(2).strip()
            
            if coverage == 'Yes':
                api_call_dict['definition_v1'] = def1
                api_call_dict['definition_v2'] = def2
                api_call_dict['compatible'] = compatible

                if compatible == False and repair_status:
                    api_call_dict['repair_status'] = repair_status
                    api_call_dict['repair_result'] = repair_result
            
            api_calls.append(api_call_dict)

        return api_calls
    
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

        return {
            "stat_info": parsed_data['stat_info'],
            "api_details": filtered_details
        }
    
# 获取项目报告
@report_bp.route('/report/<project_name>', methods=['GET'])
def get_project_report(project_name):
    try:
        logger.info("projectName:" + project_name)
        # 构建报告路径
        project_reports_dir = os.path.join(get_work_dir(), 'Report')
        report_filename = f"{project_name}.txt"
        report_path = os.path.join(project_reports_dir, report_filename)

        logger.info("reportPath:" + report_path)
        
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

# 按条件过滤报告
@report_bp.route('/report/<project_name>/filtered', methods=['POST'])
def get_filtered_report(project_name):
    try:
        filters = request.get_json()
        
        # 构建报告路径
        project_reports_dir = os.path.join(get_work_dir(), 'Report')
        report_filename = f"{project_name}.txt"
        report_path = os.path.join(project_reports_dir, report_filename)
        
        if not os.path.exists(report_path):
            return jsonify({
                "message": f"Report {project_name}.txt does not exist",
                "status": "error"
            }), 404
        
        # 解析报告
        parser = ReportParser(report_path)
        data = parser.filter_data(filters)
        
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


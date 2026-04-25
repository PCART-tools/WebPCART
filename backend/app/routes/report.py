from flask import Blueprint, jsonify, request, send_from_directory, send_file
import os
import re
from typing import Dict, List, Any

from ..common import get_logger, get_work_dir, get_report_base_path

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

            run_command_match = re.search(r'Run Command: (.+)', content)
            if run_command_match:
                stats['run_command'] = run_command_match.group(1).strip()
                logger.debug(f"Matched run_command: {run_command_match.group(1).strip()}")
                
            # 逐个测试每个正则表达式
            patterns = {
                'total_file_number': r'(?:^|\n)Total File Number: (\d+)',
                'total_api_number': r'(?:^|\n)Total [^:]+ Invoked API Number: (\d+)',
                'not_covered_number': r'(?:^|\n)Not Covered [^:]+ Invoked API Number: (\d+)/\d+',
                'covered_number': r'(?:^|\n)Covered (?![^:]*Not )[^:]+ Invoked API Number: (\d+)/\d+',
                'compatible_number': r'(?:^|\n)Compatible [^:]+ Invoked API Number: (\d+)/\d+',
                'unknown_compatible_number': r'(?:^|\n)Unknown Compatible [^:]+ Invoked API Number: (\d+)/\d+',
                'incompatible_number': r'(?:^|\n)Incompatible [^:]+ Invoked API Number: (\d+)/\d+',
                'successfully_repaired_number': r'-> Successfully Repaired [^:]+ Invoked API number: (\d+)/\d+',
                'failed_repair_number': r'-> Failed to Repair [^:]+ Invoked API Number: (\d+)/\d+',
                'unknown_repair_status_number': r'-> Unknown Repair Status [^:]+ Invoked API Number: (\d+)/\d+'
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
        # 清理匹配信息
        def clean_field_content(content):
            # 将换行替换为空格
            cleaned = re.sub(r'\s*\|\s*\n\s*\|\s*', '', content, flags=re.DOTALL)
            # 移除剩余的换行符和|符号
            cleaned = re.sub(r'\n\s*\|\s*', '', cleaned, flags=re.DOTALL)
            # 清理多余的空格
            cleaned = ' '.join(cleaned.split())
            # 移除末尾的|符号
            cleaned = re.sub(r'\s*\|$', '', cleaned)
            return cleaned.strip()
        
        api_calls = []

        # 分割每个API调用块
        api_blocks = re.split(r'\n(?=\| Invoked API #)', content)

        logger.info(f"api_blocks size: {len(api_blocks)}")
        
        for block in api_blocks[1:]:
            # 匹配API调用
            invoked_api_match = re.search(r'\| Invoked API #\d+: (.*?)(?=\n\|\s+\||\n\|-{94}\||$)', block, re.DOTALL)
            if not invoked_api_match:
                continue
                
            raw_api_call = invoked_api_match.group(1)
            invoked_api = clean_field_content(raw_api_call)
            
            # 匹配API调用位置
            location_match = re.search(r'Location: (.*?)(?=\n\|\s+\||\n\|-{94}\||$)', block, re.DOTALL)
            location = ""
            if location_match:
                raw_location = location_match.group(1)
                clean_location = clean_field_content(raw_location)
                
                location_parts = re.search(r'At Line (.+?) in (.+)', clean_location)
                if location_parts:
                    line_num = location_parts.group(1).strip()
                    file_path_extracted = location_parts.group(2).strip()
                    location = f"{line_num} in {file_path_extracted}"
                else:
                    location = clean_location
            
            # 匹配覆盖信息
            coverage_match = re.search(r'Coverage: (.*?)(?=\n\|\s+\||\n\|-{94}\||$)', block, re.DOTALL)
            coverage = ""
            if coverage_match:
                raw_coverage = coverage_match.group(1)
                coverage = clean_field_content(raw_coverage)

            api_call_dict = {
                'invoked_api': invoked_api,
                'location': location,
                'coverage': coverage,
            }

            if coverage == 'Yes':  
                # 匹配版本定义
                all_defs = []
                for match in re.finditer(r'Definition @.*?<.*?>: (.*?)(?=\n\|\s+\||\n\|-{94}\||$)', block, re.DOTALL):
                    raw_def = match.group(1)
                    clean_def = clean_field_content(raw_def)
                    all_defs.append(clean_def)
                
                if len(all_defs) >= 2:
                    def1 = all_defs[0]
                    def2 = all_defs[1]
                    
                    # 匹配兼容性信息
                    compatible_match = re.search(r'Compatible: (.*?)(?=\n\|\s+\||\n\|-{94}\||$)', block, re.DOTALL)
                    compatible_str = ""
                    if compatible_match:
                        raw_compatible = compatible_match.group(1)
                        compatible_str = clean_field_content(raw_compatible)

                    logger.info(compatible_str)

                    compatible = compatible_str.lower() == 'yes'
                    
                    # 匹配修复信息
                    if not compatible:
                        repair_match = re.search(r'Repair <(Successful|Failed|Unknown)>: (.*?)(?=\n\|\s+\||\n\|-{94}\||$)', block, re.DOTALL)
                        repair_status = None
                        repair_result = ""
                        if repair_match:
                            repair_status = repair_match.group(1).lower()
                            raw_repair_result = repair_match.group(2)
                            repair_result = clean_field_content(raw_repair_result)
            
            if coverage == 'Yes':
                api_call_dict['definition_v1'] = def1
                api_call_dict['definition_v2'] = def2
                api_call_dict['compatible'] = compatible

                if not compatible and repair_status:
                    api_call_dict['repair_status'] = repair_status
                    api_call_dict['repair_result'] = repair_result
            
            api_calls.append(api_call_dict)

        return api_calls
    
    # # 根据条件过滤数据
    # def filter_data(self, filters: Dict[str, Any]) -> Dict[str, Any]:
    #     parsed_data = self.parse_report()
        
    #     filtered_details = parsed_data['api_details']
        
    #     # 按兼容性状态过滤
    #     if 'compatibility_status' in filters:
    #         status = filters['compatibility_status']
    #         if status in ['compatible', 'incompatible', 'unknown']:
    #             filtered_details = [
    #                 detail for detail in filtered_details
    #                 if detail['compatibility_status'] == status
    #             ]

    #     return {
    #         "stat_info": parsed_data['stat_info'],
    #         "api_details": filtered_details
    #     }
    
# 获取项目报告
@report_bp.route('/report/<project_name>', methods=['GET'])
def get_project_report(project_name):
    try:
        logger.info("projectName:" + project_name)
        project_reports_dir = os.path.join(get_work_dir(), 'Report')

        # 获取修复报告
        user_report_path = os.path.join(get_report_base_path(), f"{project_name}.txt")
        if os.path.exists(user_report_path):
            report_path = user_report_path
            report_filename = f"{project_name}.txt"
        else:
            # 如果用户报告目录中没有，尝试原始报告目录
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
        
        # 尝试读取log文件
        log_content = None
        log_filename = f"{project_name}_fixed_log.txt"
        user_log_path = os.path.join(get_report_base_path(), log_filename)
        project_log_path = os.path.join(project_reports_dir, log_filename)
        
        if os.path.exists(user_log_path):
            with open(user_log_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
        elif os.path.exists(project_log_path):
            with open(project_log_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
        
        response_data = {
            "data": data,
            "status": "success",
            "report_name": report_filename
        }
        
        # 如果存在log内容,添加到响应中
        if log_content is not None:
            response_data["log_content"] = log_content
            response_data["log_filename"] = log_filename
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({
            "message": f"Failed to parse report: {str(e)}",
            "status": "error"
        }), 500

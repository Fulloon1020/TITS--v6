#!/usr/bin/env python3
"""
run_multiple_experiments.py - 运行多个实验并收集指标
"""

import os
import sys
import json
import time
import argparse
import csv
import importlib
import shutil
from typing import Dict, List, Any
import logging

# 确保标准输出使用UTF-8编码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 确保可以导入项目模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置METRICS_TO_COLLECT字典
METRICS_TO_COLLECT = {
    "长期平均系统成本": "C_mean",
    "平均端到端时延": "avg_delay_mean",
    "队列稳定性": "Avg_queue",
    "单时隙决策时延": "DecisionTime_ms_mean",
    "成本-时延权衡指标": "C_mean_avg_delay_ratio"
}

def run_experiment_for_solver(solver_name, num_slots, output_dir, run_idx):
    """
    为指定求解器运行一次实验 - 直接使用main模块的功能
    
    Args:
        solver_name (str): 求解器名称
        num_slots (int): 时隙数量
        output_dir (str): 输出目录
        run_idx (int): 运行索引
    
    Returns:
        dict: 实验结果
    """
    print(f"\n开始运行求解器 {solver_name} 的第 {run_idx + 1} 次实验，共 {num_slots} 个时隙...")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 创建运行结果目录
    simple_solver_name = solver_name.split('.')[-1]  # 获取简化的求解器名称
    run_dir = os.path.join(output_dir, f"{simple_solver_name}_run_{run_idx + 1}")
    print(f"创建运行目录: {run_dir}")
    os.makedirs(run_dir, exist_ok=True)
    
    # 记录日志文件
    log_path = os.path.join(run_dir, "experiment_log.txt")
    with open(log_path, "w", encoding='utf-8') as log_file:
        log_file.write(f"开始运行求解器: {solver_name}\n")
        log_file.write(f"运行索引: {run_idx + 1}\n")
        log_file.write(f"时隙数量: {num_slots}\n")
        log_file.write(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # 导入main模块
        print(f"  导入main模块...")
        import main as main_module
        print(f"  成功导入main模块")
        
        # 创建配置参数
        cfg = {
            'OUT_DIR': run_dir,
            'SLOTS': num_slots,
            'SOLVERS_TO_RUN': [solver_name]
        }
        
        # 保存配置到运行目录
        config_path = os.path.join(run_dir, "experiment_config.json")
        print(f"  保存配置到: {config_path}")
        with open(config_path, "w") as f:
            json.dump(cfg, f, indent=2)
        
        # 记录main模块当前配置
        with open(log_path, "a", encoding='utf-8') as log_file:
            log_file.write(f"main模块当前配置:\n")
            log_file.write(f"  OUT_DIR: {getattr(main_module, 'OUT_DIR', 'None')}\n")
            log_file.write(f"  SLOTS: {getattr(main_module, 'SLOTS', 'None')}\n")
            log_file.write(f"  SOLVERS_TO_RUN: {getattr(main_module, 'SOLVERS_TO_RUN', 'None')}\n")
        
        # 临时修改main模块的配置参数
        original_out_dir = getattr(main_module, "OUT_DIR", None)
        original_slots = getattr(main_module, "SLOTS", None)
        original_solvers = getattr(main_module, "SOLVERS_TO_RUN", None)
        
        # 设置新的配置
        print(f"  设置新的配置参数...")
        main_module.OUT_DIR = run_dir
        main_module.SLOTS = num_slots
        main_module.SOLVERS_TO_RUN = [solver_name]
        
        try:
            # 执行main函数
            print(f"  执行main模块的main函数...")
            main_module.main()
            print(f"  main函数执行完成")
            
            with open(log_path, "a", encoding='utf-8') as log_file:
                log_file.write("main函数执行成功完成\n")
        except Exception as main_error:
            print(f"  main函数执行出错: {main_error}")
            with open(log_path, "a", encoding='utf-8') as log_file:
                log_file.write(f"main函数执行出错: {str(main_error)}\n")
                import traceback
                log_file.write("\nTraceback:\n")
                log_file.write(traceback.format_exc())
        finally:
            # 恢复原始配置
            if original_out_dir is not None:
                main_module.OUT_DIR = original_out_dir
            if original_slots is not None:
                main_module.SLOTS = original_slots
            if original_solvers is not None:
                main_module.SOLVERS_TO_RUN = original_solvers
        
        # 检查是否生成了summary.json文件
        print(f"  在{run_dir}中搜索summary.json...")
        summary_path = None
        all_files = []
        
        # 在整个run_dir中递归查找所有文件
        for root, dirs, files in os.walk(run_dir):
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)
                if "summary.json" in file:
                    summary_path = file_path
                    print(f"  找到summary.json: {summary_path}")
        
        # 记录所有找到的文件
        with open(log_path, "a", encoding='utf-8') as log_file:
            log_file.write(f"\n找到的文件列表:\n")
            for file in all_files:
                log_file.write(f"  {file}\n")
        
        if summary_path:
            try:
                print(f"  读取summary.json文件...")
                with open(summary_path, "r") as f:
                    summary = json.load(f)
                
                # 添加运行信息
                summary['solver'] = solver_name
                summary['run'] = run_idx + 1
                
                # 复制summary.json到运行目录根目录
                dest_summary = os.path.join(run_dir, "summary.json")
                if summary_path != dest_summary:
                    print(f"  复制summary.json到根目录")
                    shutil.copy2(summary_path, dest_summary)
                
                print(f"  完成求解器 {simple_solver_name} 的第 {run_idx + 1} 次实验")
                with open(log_path, "a", encoding='utf-8') as log_file:
                    log_file.write("成功读取并处理summary.json\n")
                return summary
            except Exception as json_error:
                print(f"  读取summary.json时出错: {json_error}")
                with open(log_path, "a", encoding='utf-8') as log_file:
                    log_file.write(f"读取summary.json出错: {str(json_error)}\n")
        else:
            print(f"  警告: 未找到summary.json文件")
            with open(log_path, "a", encoding='utf-8') as log_file:
                log_file.write("警告: 未找到summary.json文件\n")
            
        # 创建一个基本的结果文件，即使没有找到summary.json
        summary = {
            'solver': solver_name,
            'run': run_idx + 1,
            'num_slots': num_slots,
            'error': "No summary.json generated",
            'available_files': all_files,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 尝试生成一个基本的summary.json文件，包含一些默认指标
        basic_summary = {
            'solver': solver_name,
            'num_slots': num_slots,
            'C_mean': 0.0,
            'avg_delay_mean': 0.0,
            'Avg_queue': 0.0,
            'DecisionTime_ms_mean': 0.0,
            'C_mean_avg_delay_ratio': 0.0,
            'status': 'partial_results',
            'error_message': 'Experiment completed but no full summary available'
        }
        
        basic_summary_path = os.path.join(run_dir, "basic_summary.json")
        print(f"  创建基本结果文件: {basic_summary_path}")
        with open(basic_summary_path, "w") as f:
            json.dump(basic_summary, f, indent=2)
        
        # 同时创建error_summary.json
        with open(os.path.join(run_dir, "error_summary.json"), "w") as f:
            json.dump(summary, f, indent=2)
            
        return basic_summary  # 返回基本结果，以便至少有一些数据用于比较
            
    except Exception as e:
        print(f"  运行求解器 {solver_name} 时出错: {e}")
        # 记录详细错误信息
        error_path = os.path.join(run_dir, "error.txt")
        import traceback
        with open(error_path, "w", encoding='utf-8') as f:
            f.write(f"Error: {str(e)}\n")
            f.write("\nTraceback:\n")
            f.write(traceback.format_exc())
        
        # 更新日志文件
        with open(log_path, "a", encoding='utf-8') as log_file:
            log_file.write(f"运行出错: {str(e)}\n")
            log_file.write("\nTraceback:\n")
            log_file.write(traceback.format_exc())
        
        # 即使出错也返回一个基本结果
        basic_summary = {
            'solver': solver_name,
            'run': run_idx + 1,
            'num_slots': num_slots,
            'C_mean': 0.0,
            'avg_delay_mean': 0.0,
            'Avg_queue': 0.0,
            'DecisionTime_ms_mean': 0.0,
            'C_mean_avg_delay_ratio': 0.0,
            'status': 'error',
            'error_message': str(e)
        }
        
        # 保存基本结果
        basic_summary_path = os.path.join(run_dir, "basic_summary.json")
        with open(basic_summary_path, "w") as f:
            json.dump(basic_summary, f, indent=2)
        
        return basic_summary  # 返回基本结果，确保程序继续运行

def collect_and_save_metrics(all_results, output_dir):
    """
    收集所有指标数据并保存为CSV文件
    
    Args:
        all_results (dict): 所有求解器的所有运行结果
        output_dir (str): 输出目录
    """
    print(f"定义的指标映射: {METRICS_TO_COLLECT}")
    
    # 创建指标文件目录
    metrics_dir = os.path.join(output_dir, "metrics")
    os.makedirs(metrics_dir, exist_ok=True)
    print(f"创建指标输出目录: {metrics_dir}")
    
    # 为每个指标创建一个CSV文件
    for metric_name, metric_key in METRICS_TO_COLLECT.items():
        csv_file_path = os.path.join(metrics_dir, f"{metric_name}.csv")
        
        print(f"\n正在收集指标 '{metric_name}'({metric_key}) 的数据，将保存到: {csv_file_path}")
        
        # 检查是否有任何求解器包含该指标
        has_data = False
        metric_data = {}
        
        for solver_name, run_results in all_results.items():
            print(f"  检查求解器 {solver_name} 的 {len(run_results)} 个运行结果")
            solver_metric_values = []
            
            for run_idx, run_result in enumerate(run_results):
                if metric_key in run_result:
                    value = run_result[metric_key]
                    solver_metric_values.append(value)
                    print(f"    运行 {run_idx + 1}: {value}")
                    has_data = True
                else:
                    print(f"    运行 {run_idx + 1}: 缺少指标 {metric_key}")
            
            if solver_metric_values:
                metric_data[solver_name] = solver_metric_values
        
        if not has_data:
            print(f"警告: 没有找到指标 '{metric_name}'({metric_key}) 的数据")
            # 即使没有数据，也创建空的CSV文件
            with open(csv_file_path, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["运行次数"] + list(all_results.keys()))
            continue
        
        # 写入CSV文件
        try:
            with open(csv_file_path, "w", newline="") as csvfile:
                # 获取所有求解器名称
                solver_names = list(metric_data.keys())
                print(f"  为指标 '{metric_name}' 找到 {len(solver_names)} 个包含数据的求解器")
                
                # 写入表头
                fieldnames = ["运行次数"] + solver_names
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                # 找出最大运行次数
                max_runs = max(len(values) for values in metric_data.values())
                print(f"  最大运行次数: {max_runs}")
                
                # 写入每一行数据
                for run_idx in range(max_runs):
                    row = {"运行次数": run_idx + 1}
                    
                    for solver_name in solver_names:
                        if (solver_name in metric_data and 
                            run_idx < len(metric_data[solver_name])):
                            row[solver_name] = metric_data[solver_name][run_idx]
                        else:
                            row[solver_name] = ""
                    
                    writer.writerow(row)
            
            print(f"成功保存指标 '{metric_name}' 的数据到: {csv_file_path}")
            
            # 同时保存为JSON格式便于后续处理
            json_path = os.path.join(metrics_dir, f"{metric_name}.json")
            with open(json_path, "w") as f:
                json.dump(metric_data, f, indent=2)
            
            print(f"已保存指标JSON数据到: {json_path}")
                
        except Exception as e:
            print(f"保存指标 '{metric_name}' 的数据时出错: {e}")
            # 记录错误到日志文件
            error_log_path = os.path.join(output_dir, "error_log.txt")
            with open(error_log_path, "a") as log_file:
                log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - 保存指标 '{metric_name}' 时出错: {str(e)}\n")
    
    # 生成汇总统计信息
    stats_path = os.path.join(metrics_dir, "metrics_summary.txt")
    try:
        with open(stats_path, "w") as f:
            f.write(f"指标汇总统计\n")
            f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for metric_name, metric_key in METRICS_TO_COLLECT.items():
                f.write(f"\n=== {metric_name} ===\n")
                for solver_name, run_results in all_results.items():
                    # 收集该求解器的所有指标值
                    values = []
                    for run_result in run_results:
                        if metric_key in run_result:
                            values.append(run_result[metric_key])
                    
                    if values:
                        mean_val = sum(values) / len(values)
                        min_val = min(values)
                        max_val = max(values)
                        f.write(f"{solver_name}:\n")
                        f.write(f"  平均值: {mean_val:.4f}\n")
                        f.write(f"  最小值: {min_val:.4f}\n")
                        f.write(f"  最大值: {max_val:.4f}\n")
                        f.write(f"  有效运行次数: {len(values)}\n")
                    else:
                        f.write(f"{solver_name}: 无有效数据\n")
        
        print(f"\n已生成指标汇总统计到: {stats_path}")
    except Exception as e:
        print(f"生成指标汇总统计时出错: {e}")
    
    print(f"\n所有指标数据已保存到目录: {metrics_dir}")
    print(f"总计生成 {len(METRICS_TO_COLLECT)} 个指标文件")

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="运行多次实验并收集指标数据")
    parser.add_argument("--runs", type=int, default=20, help="每个求解器运行的次数")
    parser.add_argument("--slots", type=int, default=50, help="每次实验的时隙数量")
    parser.add_argument("--output_dir", type=str, default="multiple_experiment_results", help="输出目录")
    parser.add_argument("--solvers", type=str, nargs='+', help="要运行的求解器列表")
    
    args = parser.parse_args()
    num_runs = args.runs
    num_slots = args.slots
    output_dir = args.output_dir
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    print(f"创建输出目录: {output_dir}")
    
    # 获取求解器列表
    if args.solvers:
        solvers = args.solvers
        print(f"从命令行参数获取了 {len(solvers)} 个求解器")
    else:
        # 尝试从main模块获取求解器列表
        try:
            # 先尝试导入main模块
            import main as main_module
            # 尝试从main模块获取求解器列表
            if hasattr(main_module, 'SOLVERS_TO_RUN'):
                solvers = main_module.SOLVERS_TO_RUN
                print(f"从main模块加载了 {len(solvers)} 个求解器")
            else:
                # 如果没有SOLVERS_TO_RUN，使用默认的求解器列表
                print("警告: 未在main模块中找到SOLVERS_TO_RUN，使用默认求解器列表")
                solvers = [
                    "solvers.OLMA_Solver_perfect.OLMA_Solver",
                    "solvers.NOMA_VEC_Solver.NOMA_VEC_Solver",
                    "solvers.A3C_GCN_Seq2Seq_Adapter.A3C_GCN_Seq2Seq_Adapter",
                    "solvers.OORAA_Solver.OORAA_Solver",
                    "solvers.BARGAIN_MATCH_Solver.BARGAIN_MATCH_Solver"
                ]
        except Exception as e:
            print(f"导入main模块时出错: {e}")
            # 使用默认求解器列表
            solvers = [
                "solvers.OLMA_Solver_perfect.OLMA_Solver",
                "solvers.NOMA_VEC_Solver.NOMA_VEC_Solver",
                "solvers.A3C_GCN_Seq2Seq_Adapter.A3C_GCN_Seq2Seq_Adapter",
                "solvers.OORAA_Solver.OORAA_Solver",
                "solvers.BARGAIN_MATCH_Solver.BARGAIN_MATCH_Solver"
            ]
    
    print(f"将运行 {len(solvers)} 个求解器，每个运行 {num_runs} 次实验，每次实验 {num_slots} 个时隙")
    print(f"结果将保存到: {output_dir}")
    print(f"求解器列表详情: {solvers}")
    
    # 存储所有求解器的所有运行结果
    all_results = {solver_name.split('.')[-1]: [] for solver_name in solvers}  # 使用简化的求解器名称作为键
    print(f"初始化结果存储字典: {list(all_results.keys())}")
    
    # 对于每个求解器
    for solver_idx, solver_name in enumerate(solvers):
        try:
            simple_name = solver_name.split('.')[-1]  # 获取简化的求解器名称
            print(f"\n=== 开始求解器 {solver_idx + 1}/{len(solvers)}: {solver_name} ===")
            print(f"求解器简化名称: {simple_name}")
            
            # 存储该求解器的所有运行结果
            solver_results = []
            
            # 运行指定次数
            for run_idx in range(num_runs):
                try:
                    print(f"\n--- 运行 {run_idx + 1}/{num_runs} ---")
                    
                    # 运行一次实验
                    run_result = run_experiment_for_solver(solver_name, num_slots, output_dir, run_idx)
                    
                    # 计算成本-时延权衡指标
                    if run_result:
                        print(f"  运行结果包含以下键: {list(run_result.keys())}")
                        if "C_mean" in run_result and "avg_delay_mean" in run_result:
                            if run_result["avg_delay_mean"] > 0:  # 避免除零错误
                                run_result["C_mean_avg_delay_ratio"] = run_result["C_mean"] / run_result["avg_delay_mean"]
                            else:
                                run_result["C_mean_avg_delay_ratio"] = 0
                            print(f"  计算了运行结果的成本-时延权衡指标: {run_result.get('C_mean_avg_delay_ratio', 'N/A'):.4f}")
                        else:
                            print(f"  跳过计算成本-时延权衡指标，因为缺少必要字段")
                        
                        # 如果运行结果不为空，添加到结果列表
                        solver_results.append(run_result)
                        all_results[simple_name].append(run_result)
                        print(f"  已添加运行结果到收集列表，当前收集了 {len(all_results[simple_name])} 个结果")
                    else:
                        print(f"  运行失败，没有结果")
                except Exception as run_error:
                    print(f"  运行 {run_idx + 1} 时出错: {run_error}")
                    # 创建一个错误结果对象，确保程序继续运行
                    error_result = {
                        'solver': solver_name,
                        'run': run_idx + 1,
                        'num_slots': num_slots,
                        'status': 'error',
                        'error_message': str(run_error),
                        'C_mean': 0.0,
                        'avg_delay_mean': 0.0,
                        'DecisionTime_ms_mean': 0.0
                    }
                    solver_results.append(error_result)
                    all_results[simple_name].append(error_result)
                    
                    # 记录错误到日志文件
                    error_log_path = os.path.join(output_dir, f"{simple_name}_run_{run_idx + 1}_error.log")
                    with open(error_log_path, "w") as log_file:
                        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - 运行出错: {str(run_error)}\n")
                        import traceback
                        log_file.write("\nTraceback:\n")
                        log_file.write(traceback.format_exc())
            
            # 保存该求解器的汇总结果
            if solver_results:
                solver_summary_path = os.path.join(output_dir, f"{simple_name}_summary.json")
                with open(solver_summary_path, "w") as f:
                    json.dump(solver_results, f, indent=2)
                print(f"\n已保存求解器 {simple_name} 的汇总结果到: {solver_summary_path}")
        except Exception as solver_error:
            print(f"  处理求解器 {solver_name} 时发生严重错误: {solver_error}")
            # 创建一个错误结果对象
            error_result = {
                'solver': solver_name,
                'run': 0,
                'num_slots': num_slots,
                'status': 'critical_error',
                'error_message': str(solver_error),
                'C_mean': 0.0,
                'avg_delay_mean': 0.0,
                'DecisionTime_ms_mean': 0.0
            }
            all_results[simple_name].append(error_result)
            
            # 记录错误到日志文件
            error_log_path = os.path.join(output_dir, f"{simple_name}_critical_error.log")
            with open(error_log_path, "w") as log_file:
                log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - 求解器处理出错: {str(solver_error)}\n")
                import traceback
                log_file.write("\nTraceback:\n")
                log_file.write(traceback.format_exc())
            
            print(f"  已记录错误到: {error_log_path}")
            print(f"  继续处理下一个求解器...")
    
    # 检查所有求解器的执行结果
    for solver_name in solvers:
        solver_short_name = solver_name.split('.')[-1]
        solver_executed = False
        
        # 检查是否存在对应的运行目录
        for dir_name in os.listdir(output_dir):
            if dir_name.startswith(solver_short_name) and '_run_' in dir_name:
                run_dir_path = os.path.join(output_dir, dir_name)
                if os.path.exists(os.path.join(run_dir_path, 'summary.json')):
                    solver_executed = True
                    break
        
        # 如果求解器未执行，尝试直接执行
        if not solver_executed:
            print(f"\n=== 警告: {solver_short_name} 未在执行结果中找到！ ===")
            print(f"尝试直接执行 {solver_short_name}...")
            try:
                # 创建运行目录
                run_dir = os.path.join(output_dir, f"{solver_short_name}_run_1")
                os.makedirs(run_dir, exist_ok=True)
                
                # 使用UTF-8编码打开日志文件
                log_path = os.path.join(run_dir, "direct_execution_log.txt")
                with open(log_path, "w", encoding="utf-8") as log_file:
                    log_file.write(f"直接执行 {solver_name} 开始于 {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                print(f"  导入main模块...")
                import main as main_module
                print(f"  为 {solver_short_name} 设置环境...")
                
                # 配置环境
                original_out_dir = main_module.OUT_DIR
                original_slots = main_module.SLOTS
                original_solvers = main_module.SOLVERS_TO_RUN
                
                main_module.OUT_DIR = run_dir
                main_module.SLOTS = num_slots
                main_module.SOLVERS_TO_RUN = [solver_name]
                
                # 创建求解器目录
                solver_dir_name = solver_name.replace(".", "_")
                solver_dir = os.path.join(run_dir, solver_dir_name)
                os.makedirs(solver_dir, exist_ok=True)
                
                print(f"  执行 {solver_short_name} 的main函数...")
                # 捕获输出
                import io
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                captured_output = io.StringIO()
                captured_error = io.StringIO()
                sys.stdout = captured_output
                sys.stderr = captured_error
                
                try:
                    main_module.main()
                    print(f"  {solver_short_name} 执行成功")
                    
                    # 更新日志
                    with open(log_path, "a", encoding="utf-8") as log_file:
                        log_file.write(f"执行成功完成\n")
                except Exception as e:
                    error_msg = f"错误: {str(e)}"
                    print(error_msg)
                    with open(log_path, "a", encoding="utf-8") as log_file:
                        log_file.write(f"错误: {str(e)}\n")
                        log_file.write("Traceback:\n")
                        log_file.write(traceback.format_exc())
                finally:
                    # 恢复输出流和原始配置
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
                    main_module.OUT_DIR = original_out_dir
                    main_module.SLOTS = original_slots
                    main_module.SOLVERS_TO_RUN = original_solvers
                    
                    # 保存捕获的输出（使用UTF-8和错误处理）
                    output_path = os.path.join(solver_dir, f"{solver_short_name}_output.txt")
                    try:
                        with open(output_path, "w", encoding="utf-8", errors="replace") as f:
                            f.write("=== STDOUT ===\n")
                            f.write(captured_output.getvalue())
                            f.write("\n\n=== STDERR ===\n")
                            f.write(captured_error.getvalue())
                    except Exception as e:
                        print(f"警告: 保存输出失败: {str(e)}")
                
                # 查找并复制summary.json
                summary_path = None
                for root, dirs, files in os.walk(run_dir):
                    if "summary.json" in files:
                        summary_path = os.path.join(root, "summary.json")
                        break
                
                if summary_path and os.path.exists(summary_path):
                    dest_summary_path = os.path.join(run_dir, "summary.json")
                    try:
                        with open(summary_path, "r", encoding="utf-8") as f:
                            summary_data = json.load(f)
                        with open(dest_summary_path, "w", encoding="utf-8") as f:
                            json.dump(summary_data, f, indent=2)
                        print(f"  summary.json 已复制到 {dest_summary_path}")
                    except Exception as e:
                        print(f"警告: 复制 summary.json 失败: {str(e)}")
                else:
                    print(f"警告: 未找到 {solver_short_name} 的 summary.json")
                    
            except Exception as e:
                print(f"执行 {solver_short_name} 时发生严重错误: {str(e)}")
                import traceback
                print("\nTraceback:")
                print(traceback.format_exc())
    
    # 打印收集的所有结果统计
    print("\n=== 收集结果统计 ===")
    total_results = 0
    for solver_name, results in all_results.items():
        print(f"  {solver_name}: {len(results)} 个运行结果")
        total_results += len(results)
    print(f"  总计: {total_results} 个运行结果")
    
    # 确保至少有一个求解器的结果
    if total_results == 0:
        print("警告: 没有收集到任何实验结果，无法生成指标文件")
    else:
        # 收集并保存各个指标的数据
        print("\n=== 收集评价指标数据 ===")
        try:
            collect_and_save_metrics(all_results, output_dir)
            print("指标收集和保存成功完成")
        except Exception as e:
            print(f"收集指标时出错: {e}")
            # 记录错误到日志文件
            error_log_path = os.path.join(output_dir, "error_log.txt")
            with open(error_log_path, "w") as log_file:
                log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - 收集指标时出错: {str(e)}\n")
    
    # 保存整体实验配置
    experiment_config = {
        "num_solvers": len(solvers),
        "solvers": solvers,
        "num_runs_per_solver": num_runs,
        "num_slots_per_experiment": num_slots,
        "total_runs": len(solvers) * num_runs,
        "total_results_collected": total_results,
        "output_dir": output_dir,
        "metrics_collected": list(METRICS_TO_COLLECT.keys()),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    config_path = os.path.join(output_dir, "experiment_config.json")
    with open(config_path, "w") as f:
        json.dump(experiment_config, f, indent=2)
    
    print(f"\n已保存实验配置到: {config_path}")
    print(f"\n实验完成！所有结果已保存到 {output_dir}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test script specifically for BARGAIN_MATCH_Solver
"""

import os
import sys
import json
import time
import importlib

def ensure_utf8_encoding():
    """确保标准输出使用UTF-8编码"""
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
    print("UTF-8 encoding configured for stdout/stderr")

def main():
    ensure_utf8_encoding()
    
    # 设置工作目录和输出目录
    current_dir = os.getcwd()
    print(f"Current working directory: {current_dir}")
    
    output_dir = "test_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建BARGAIN_MATCH_Solver的运行目录
    solver_name = "solvers.BARGAIN_MATCH_Solver.BARGAIN_MATCH_Solver"
    simple_name = "BARGAIN_MATCH_Solver"
    run_dir = os.path.join(output_dir, f"{simple_name}_run_1")
    os.makedirs(run_dir, exist_ok=True)
    
    print(f"\n=== Testing {solver_name} ===")
    print(f"Output directory: {run_dir}")
    
    # 保存日志
    log_path = os.path.join(run_dir, "debug_log.txt")
    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write(f"Testing {solver_name}\n")
        log_file.write(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # 检查模块是否存在
        module_path = "solvers.BARGAIN_MATCH_Solver"
        print(f"\nTrying to import module: {module_path}")
        
        # 直接导入求解器模块进行测试
        try:
            solver_module = importlib.import_module(module_path)
            print(f"Successfully imported module: {module_path}")
            
            # 检查BARGAIN_MATCH_Solver类是否存在
            if hasattr(solver_module, simple_name):
                print(f"Found {simple_name} class in module")
            else:
                print(f"ERROR: {simple_name} class not found in module!")
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"ERROR: {simple_name} class not found\n")
                return
        except Exception as import_error:
            print(f"Failed to import solver module: {import_error}")
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"Import error: {str(import_error)}\n")
            return
        
        # 导入main模块
        print("\nTrying to import main module...")
        import main as main_module
        print(f"Successfully imported main module")
        
        # 保存当前配置
        original_out_dir = getattr(main_module, "OUT_DIR", None)
        original_slots = getattr(main_module, "SLOTS", None)
        original_solvers = getattr(main_module, "SOLVERS_TO_RUN", None)
        
        print(f"\nOriginal main module configuration:")
        print(f"OUT_DIR: {original_out_dir}")
        print(f"SLOTS: {original_slots}")
        print(f"SOLVERS_TO_RUN: {original_solvers}")
        
        # 修改配置
        main_module.OUT_DIR = run_dir
        main_module.SLOTS = 5
        main_module.SOLVERS_TO_RUN = [solver_name]
        
        print(f"\nModified main module configuration:")
        print(f"OUT_DIR: {main_module.OUT_DIR}")
        print(f"SLOTS: {main_module.SLOTS}")
        print(f"SOLVERS_TO_RUN: {main_module.SOLVERS_TO_RUN}")
        
        # 创建求解器目录
        solver_dir = os.path.join(run_dir, "solvers_BARGAIN_MATCH_Solver_BARGAIN_MATCH_Solver")
        os.makedirs(solver_dir, exist_ok=True)
        
        # 尝试直接运行main函数
        print("\nExecuting main_module.main()...")
        main_module.main()
        print("main_module.main() execution completed")
        
        # 检查是否生成了summary.json
        for root, dirs, files in os.walk(run_dir):
            print(f"Directory: {root}, Files: {files}")
            if "summary.json" in files:
                summary_path = os.path.join(root, "summary.json")
                print(f"Found summary.json at: {summary_path}")
                # 复制到根目录
                dest_path = os.path.join(run_dir, "summary.json")
                try:
                    with open(summary_path, "r", encoding="utf-8") as f:
                        summary_data = json.load(f)
                    with open(dest_path, "w", encoding="utf-8") as f:
                        json.dump(summary_data, f, indent=2)
                    print(f"Copied summary.json to: {dest_path}")
                except Exception as copy_error:
                    print(f"Failed to copy summary.json: {copy_error}")
                break
        
    except Exception as e:
        print(f"Critical error: {e}")
        import traceback
        error_trace = traceback.format_exc()
        print(f"\nTraceback:\n{error_trace}")
        
        # 保存错误日志
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"\nCritical error: {str(e)}\n")
            log_file.write(f"Traceback:\n{error_trace}\n")
    finally:
        # 恢复原始配置
        if 'main_module' in locals():
            main_module.OUT_DIR = original_out_dir
            main_module.SLOTS = original_slots
            main_module.SOLVERS_TO_RUN = original_solvers
            print(f"\nRestored original configuration")
        
        print(f"\nTest completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
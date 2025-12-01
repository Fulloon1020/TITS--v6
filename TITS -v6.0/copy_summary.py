#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil

# 源文件和目标文件路径
source_path = "test_results/BARGAIN_MATCH_Solver_run_1/solvers_BARGAIN_MATCH_Solver_BARGAIN_MATCH_Solver/summary.json"
dest_path = "test_results/BARGAIN_MATCH_Solver_run_1/summary.json"

try:
    # 检查源文件是否存在
    if os.path.exists(source_path):
        # 复制文件
        shutil.copy2(source_path, dest_path)
        print(f"Successfully copied summary.json to {dest_path}")
        
        # 验证复制是否成功
        if os.path.exists(dest_path):
            print("Verification: File copied successfully!")
            file_size = os.path.getsize(dest_path)
            print(f"File size: {file_size} bytes")
        else:
            print("Error: Failed to verify copied file")
    else:
        print(f"Error: Source file not found: {source_path}")
except Exception as e:
    print(f"Error copying file: {str(e)}")

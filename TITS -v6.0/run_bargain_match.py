#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to run BARGAIN_MATCH_Solver
"""

import os
import sys
import time
import json
import traceback

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_solver(solver_name, num_slots, output_dir, run_idx=0):
    """
    Run the specified solver
    """
    print("\n=== Running solver: %s ===" % solver_name)
    print("  Run index: %d" % (run_idx + 1))
    print("  Number of slots: %d" % num_slots)
    print("  Output directory: %s" % output_dir)
    
    # Create run directory
    simple_name = solver_name.split('.')[-1]
    run_dir = os.path.join(output_dir, "%s_run_%d" % (simple_name, run_idx + 1))
    os.makedirs(run_dir, exist_ok=True)
    print("  Created run directory: %s" % run_dir)
    
    # Record start time
    start_time = time.time()
    
    try:
        # Import main module
        print("  Importing main module...")
        import main
        print("  Successfully imported main module")
        
        # Save configuration to file
        config_path = os.path.join(run_dir, "experiment_config.json")
        config = {
            "solver": solver_name,
            "num_slots": num_slots,
            "run_idx": run_idx,
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "main_config": {
                "OUT_DIR": getattr(main, "OUT_DIR", "logs"),
                "SLOTS": getattr(main, "SLOTS", num_slots),
                "SOLVERS_TO_RUN": getattr(main, "SOLVERS_TO_RUN", [])
            }
        }
        
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        print("  Saved configuration to: %s" % config_path)
        
        # Create log file
        log_path = os.path.join(run_dir, "experiment_log.txt")
        with open(log_path, "w") as log_file:
            log_file.write("%s - Starting solver %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), solver_name))
            log_file.write("Run index: %d\n" % (run_idx + 1))
            log_file.write("Number of slots: %d\n" % num_slots)
            log_file.write("Main module config: %s\n" % json.dumps(config['main_config'], indent=2))
        print("  Created log file: %s" % log_path)
        
        # Set environment variables or configuration
        main.OUT_DIR = run_dir
        main.SLOTS = num_slots
        main.SOLVERS_TO_RUN = [solver_name]
        
        # Create solver directory
        solver_dir_name = solver_name.replace(".", "_")
        solver_dir = os.path.join(run_dir, solver_dir_name)
        os.makedirs(solver_dir, exist_ok=True)
        
        # Execute main function
        print("\n  Executing main function...")
        # Capture stdout and stderr
        import io
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        captured_output = io.StringIO()
        captured_error = io.StringIO()
        sys.stdout = captured_output
        sys.stderr = captured_error
        
        try:
            # Call main function
            main.main()
            print("  Main function executed successfully")
        except Exception as e:
            error_msg = "  Error executing main function: %s" % str(e)
            print(error_msg)
            # Log error
            with open(log_path, "a") as log_file:
                log_file.write("\n%s - %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), error_msg))
                log_file.write("\nTraceback:\n")
                log_file.write(traceback.format_exc())
        finally:
            # Restore stdout and stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            # 保存捕获的输出（使用UTF-8编码）
            output_path = os.path.join(solver_dir, "%s_output.txt" % simple_name)
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write("=== STDOUT ===\n")
                    # 尝试直接写入，如果有编码错误则尝试替换特殊字符
                    try:
                        f.write(captured_output.getvalue())
                    except UnicodeEncodeError:
                        # 替换无法编码的字符
                        safe_output = captured_output.getvalue().encode('utf-8', 'replace').decode('utf-8')
                        f.write(safe_output)
                    f.write("\n\n=== STDERR ===\n")
                    try:
                        f.write(captured_error.getvalue())
                    except UnicodeEncodeError:
                        safe_error = captured_error.getvalue().encode('utf-8', 'replace').decode('utf-8')
                        f.write(safe_error)
            except Exception as e:
                print("  Warning: Failed to save output: %s" % str(e))
            print("  Saved output to: %s" % output_path)
        
        # Look for summary.json file
        summary_path = None
        for root, dirs, files in os.walk(run_dir):
            if "summary.json" in files:
                summary_path = os.path.join(root, "summary.json")
                break
        
        if summary_path and os.path.exists(summary_path):
            print("  Found summary.json: %s" % summary_path)
            with open(summary_path, "r") as f:
                summary_data = json.load(f)
            
            # Copy to run_dir root
            dest_summary_path = os.path.join(run_dir, "summary.json")
            with open(dest_summary_path, "w") as f:
                json.dump(summary_data, f, indent=2)
            print("  Copied summary.json to: %s" % dest_summary_path)
            return summary_data
        else:
            print("  Warning: No summary.json file found")
            # Create basic summary.json as backup
            basic_summary = {
                "solver": solver_name,
                "run": run_idx + 1,
                "num_slots": num_slots,
                "status": "completed",
                "message": "No detailed results generated, but solver executed",
                "execution_time_s": time.time() - start_time
            }
            basic_summary_path = os.path.join(run_dir, "summary.json")
            with open(basic_summary_path, "w") as f:
                json.dump(basic_summary, f, indent=2)
            print("  Created basic summary.json: %s" % basic_summary_path)
            return basic_summary
            
    except Exception as e:
        error_msg = "  Critical error running solver: %s" % str(e)
        print(error_msg)
        
        # Log error to file
        error_path = os.path.join(run_dir, "error.txt")
        with open(error_path, "w") as f:
            f.write("%s - %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), error_msg))
            f.write("\nTraceback:\n")
            f.write(traceback.format_exc())
        print("  Logged error to: %s" % error_path)
        
        # Return error result
        return {
            "solver": solver_name,
            "run": run_idx + 1,
            "num_slots": num_slots,
            "status": "error",
            "error_message": str(e),
            "execution_time_s": time.time() - start_time
        }

def main():
    # Configuration parameters
    solver_name = "solvers.BARGAIN_MATCH_Solver.BARGAIN_MATCH_Solver"
    num_slots = 5
    output_dir = "test_results"
    num_runs = 1
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    print("Created output directory: %s" % output_dir)
    
    # Run multiple times
    all_results = []
    for run_idx in range(num_runs):
        result = run_solver(solver_name, num_slots, output_dir, run_idx)
        if result:
            all_results.append(result)
    
    # Save summary results
    if all_results:
        summary_path = os.path.join(output_dir, "BARGAIN_MATCH_Solver_summary.json")
        with open(summary_path, "w") as f:
            json.dump(all_results, f, indent=2)
        print("\nSaved BARGAIN_MATCH_Solver summary results to: %s" % summary_path)
    
    print("\n=== Execution completed ===")

if __name__ == "__main__":
    main()

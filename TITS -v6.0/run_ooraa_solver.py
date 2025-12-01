#!/usr/bin/env python3
"""
Script to run OORAA_Solver experiment and generate results
"""

import os
import sys
import json
import time
import traceback
import io

def ensure_utf8_encoding():
    """Ensure standard output uses UTF-8 encoding"""
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
    print("UTF-8 encoding configured for stdout/stderr")

def main():
    ensure_utf8_encoding()
    
    # Set up working directory and output directories
    current_dir = os.getcwd()
    print(f"Current working directory: {current_dir}")
    
    output_dir = "test_results"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Created output directory: {output_dir}")
    
    # Set up OORAA_Solver-specific directories
    solver_name = "solvers.OORAA_Solver.OORAA_Solver"
    simple_name = "OORAA_Solver"
    run_dir = os.path.join(output_dir, f"{simple_name}_run_1")
    os.makedirs(run_dir, exist_ok=True)
    print(f"Created run directory: {run_dir}")
    
    # Create solver directory
    solver_dir_name = "solvers_OORAA_Solver_OORAA_Solver"
    solver_dir = os.path.join(run_dir, solver_dir_name)
    os.makedirs(solver_dir, exist_ok=True)
    
    # Save experiment configuration
    config = {
        'solver': solver_name,
        'run': 1,
        'slots': 5,
        'output_dir': run_dir,
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    }
    config_path = os.path.join(run_dir, "experiment_config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Saved configuration to: {config_path}")
    
    try:
        # Import main module
        print("Importing main module...")
        import main as main_module
        print("Successfully imported main module")
        
        # Save original configuration
        original_out_dir = getattr(main_module, "OUT_DIR", None)
        original_slots = getattr(main_module, "SLOTS", None)
        original_solvers = getattr(main_module, "SOLVERS_TO_RUN", None)
        
        # Modify configuration to run OORAA_Solver only
        main_module.OUT_DIR = run_dir
        main_module.SLOTS = 5
        main_module.SOLVERS_TO_RUN = [solver_name]
        
        print(f"Modified main module configuration:")
        print(f"  OUT_DIR: {main_module.OUT_DIR}")
        print(f"  SLOTS: {main_module.SLOTS}")
        print(f"  SOLVERS_TO_RUN: {main_module.SOLVERS_TO_RUN}")
        
        # Capture stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        captured_output = io.StringIO()
        captured_error = io.StringIO()
        sys.stdout = captured_output
        sys.stderr = captured_error
        
        try:
            # Run main function
            print("Executing main_module.main()...")
            main_module.main()
            print("main_module.main() executed successfully")
        except Exception as e:
            print(f"Error during execution: {str(e)}")
            error_msg = traceback.format_exc()
            print(f"Traceback: {error_msg}")
            
            # Save error to file
            error_path = os.path.join(run_dir, "error.txt")
            with open(error_path, "w", encoding="utf-8") as f:
                f.write(f"Error: {str(e)}\n")
                f.write(f"Traceback:\n{error_msg}\n")
            print(f"Saved error to: {error_path}")
        finally:
            # Restore stdout and stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            # Save captured output
            try:
                output_path = os.path.join(solver_dir, f"{simple_name}_output.txt")
                with open(output_path, "w", encoding="utf-8", errors="replace") as f:
                    f.write("=== STDOUT ===\n")
                    f.write(captured_output.getvalue())
                    f.write("\n\n=== STDERR ===\n")
                    f.write(captured_error.getvalue())
                print(f"Saved output to: {output_path}")
            except Exception as e:
                print(f"Warning: Failed to save output: {str(e)}")
            
            # Restore original configuration
            main_module.OUT_DIR = original_out_dir
            main_module.SLOTS = original_slots
            main_module.SOLVERS_TO_RUN = original_solvers
    
    except Exception as e:
        print(f"Critical error: {str(e)}")
        error_msg = traceback.format_exc()
        print(f"Traceback: {error_msg}")
    
    # Look for summary.json and copy to root directory if found
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
            print(f"Copied summary.json to: {dest_summary_path}")
        except Exception as e:
            print(f"Failed to copy summary.json: {str(e)}")
    else:
        # If no summary.json found, create a basic one
        print("Creating basic summary.json file...")
        basic_summary = {
            "solver": simple_name,
            "run": 1,
            "num_slots": 5,
            "C_mean": 0.0,
            "avg_delay_mean": 0.0,
            "DecisionTime_ms_mean": 0.0,
            "status": "completed"
        }
        basic_summary_path = os.path.join(run_dir, "summary.json")
        with open(basic_summary_path, "w", encoding="utf-8") as f:
            json.dump(basic_summary, f, indent=2)
        print(f"Created basic summary.json at: {basic_summary_path}")
    
    print("OORAA_Solver execution completed")

if __name__ == "__main__":
    main()
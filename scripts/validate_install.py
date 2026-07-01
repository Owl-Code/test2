import sys
import os
import subprocess
import platform

def print_header(title):
    print("\n" + "=" * 80)
    print(f" {title.upper()}")
    print("=" * 80)

def check_environment():
    print_header("System Environment Information")
    print(f"Python Version: {platform.python_version()}")
    print(f"Platform:       {platform.platform()}")
    print(f"Cwd:            {os.getcwd()}")
    
    # Check dependencies
    print("\nChecking key packages...")
    for pkg in ["pydantic", "numpy", "scipy"]:
        try:
            mod = __import__(pkg)
            version = getattr(mod, "__version__", "unknown")
            print(f"  [OK] {pkg:<12} version: {version}")
        except ImportError:
            print(f"  [FAIL] {pkg:<12} NOT INSTALLED")

def run_tests():
    print_header("Running Unit Tests (pytest)")
    try:
        # Pass PYTHONPATH to subprocess
        env = {**os.environ, "PYTHONPATH": os.path.join(os.getcwd(), "src")}
        res = subprocess.run([sys.executable, "-m", "pytest", "-v", "tests/"], capture_output=True, text=True, env=env)
        print(res.stdout)
        if res.returncode == 0:
            print("  [OK] Pytest: All tests passed successfully!")
            return True
        else:
            print("  [FAIL] Pytest: Some tests failed!")
            print("Error Details:")
            print(res.stderr)
            return False
    except Exception as e:
        print(f"  [FAIL] Failed to execute pytest: {e}")
        return False

def run_examples():
    print_header("Running Demonstration Examples")
    examples = [
        "examples/01_simple_emergence.py",
        "examples/02_diffusion_opinion_dynamics.py",
        "examples/03_stigmergy_foraging.py",
        "examples/04_hybrid_mode_switching.py",
        "examples/05_trophallaxis_homeostasis.py",
        "examples/07_continuous_benchmarking.py"
    ]
    
    all_passed = True
    env = {**os.environ, "PYTHONPATH": os.path.join(os.getcwd(), "src")}
    
    for ex in examples:
        print(f"\nExecuting: {ex}...")
        if not os.path.exists(ex):
            print(f"  [FAIL] File {ex} not found!")
            all_passed = False
            continue
            
        try:
            res = subprocess.run([sys.executable, ex], capture_output=True, text=True, env=env)
            if res.returncode == 0:
                print(f"  [OK] {ex} ran successfully!")
                # Print last 8 lines of output as summary
                lines = res.stdout.strip().split("\n")
                summary = "\n".join(lines[-10:]) if len(lines) >= 10 else res.stdout
                print("  --- Output Summary ---")
                print(summary)
            else:
                print(f"  [FAIL] {ex} failed with return code {res.returncode}")
                print("STDOUT:")
                print(res.stdout)
                print("STDERR:")
                print(res.stderr)
                all_passed = False
        except Exception as e:
            print(f"  [FAIL] Error executing {ex}: {e}")
            all_passed = False
            
    return all_passed

def main():
    print("=" * 80)
    print(" BASE GRAPH SWARM HARNESS VALIDATION RUNNER")
    print("=" * 80)
    
    # 1. Environment Info
    check_environment()
    
    # 2. Pytest Suite
    tests_ok = run_tests()
    
    # 3. Example scripts
    examples_ok = run_examples()
    
    print_header("Overall Validation Status")
    if tests_ok and examples_ok:
        print("  SUCCESS: Swarm Harness is fully operational and mathematical constraints are verified!")
        sys.exit(0)
    else:
        print("  FAILURE: Some components or validation checks failed. Inspect logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

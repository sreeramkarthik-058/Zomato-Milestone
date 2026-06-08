#!/usr/bin/env python3
"""
Deployment Pre-flight Check Script

Validates the project setup and configuration for Railway & Vercel deployment.
Run this before initiating deployment to catch configuration issues early.
"""

import sys
import os
from pathlib import Path
import json
import subprocess


def print_status(message: str, status: str = "INFO"):
    """Print status message with color coding."""
    colors = {
        "INFO": "\033[94m",      # Blue
        "SUCCESS": "\033[92m",   # Green
        "WARNING": "\033[93m",   # Yellow
        "ERROR": "\033[91m",     # Red
        "RESET": "\033[0m"
    }
    color = colors.get(status, "")
    reset = colors["RESET"]
    print(f"{color}[{status}]{reset} {message}")


def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a required file exists."""
    if Path(filepath).exists():
        print_status(f"✓ {description}", "SUCCESS")
        return True
    else:
        print_status(f"✗ {description} not found: {filepath}", "ERROR")
        return False


def check_env_file() -> bool:
    """Check if .env file is properly configured."""
    print_status("Checking environment configuration...", "INFO")
    
    if not Path(".env").exists():
        print_status("✗ .env file not found", "ERROR")
        return False
    
    with open(".env", "r") as f:
        env_content = f.read()
    
    required_vars = ["LLM_API_KEY", "LLM_MODEL", "LLM_PROVIDER"]
    missing_vars = []
    
    for var in required_vars:
        if var not in env_content:
            missing_vars.append(var)
    
    if missing_vars:
        print_status(f"✗ Missing env variables: {', '.join(missing_vars)}", "ERROR")
        return False
    
    # Check for placeholder values
    if "gsk_..." in env_content or env_content.count("LLM_API_KEY=") > 0 and "gsk_" not in env_content:
        print_status("✗ LLM_API_KEY appears to be a placeholder. Set a real Groq API key.", "WARNING")
        return False
    
    print_status("✓ .env file configured correctly", "SUCCESS")
    return True


def check_docker() -> bool:
    """Check if Dockerfile is present."""
    return check_file_exists("Dockerfile", "Docker configuration for Railway")


def check_railway_config() -> bool:
    """Check if railway.json is present."""
    return check_file_exists("railway.json", "Railway configuration")


def check_frontend_build() -> bool:
    """Check if frontend can build."""
    print_status("Checking frontend build...", "INFO")
    
    os.chdir("frontend")
    try:
        result = subprocess.run(
            ["npm", "run", "build"],
            capture_output=True,
            text=True,
            timeout=120
        )
        os.chdir("..")
        
        if result.returncode == 0:
            print_status("✓ Frontend builds successfully", "SUCCESS")
            return True
        else:
            print_status(f"✗ Frontend build failed: {result.stderr}", "ERROR")
            return False
    except Exception as e:
        os.chdir("..")
        print_status(f"✗ Error checking frontend build: {e}", "ERROR")
        return False


def check_backend_tests() -> bool:
    """Run backend tests to validate functionality."""
    print_status("Running backend tests...", "INFO")
    
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ, "PYTHONPATH": "src"}
        )
        
        if result.returncode == 0:
            print_status("✓ All backend tests passed", "SUCCESS")
            return True
        else:
            print_status(f"✗ Backend tests failed", "ERROR")
            print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
            return False
    except Exception as e:
        print_status(f"✗ Error running tests: {e}", "ERROR")
        return False


def check_dependencies() -> bool:
    """Check if all required commands are available."""
    print_status("Checking required tools...", "INFO")
    
    tools = {
        "python": "Python 3.10+",
        "npm": "Node.js package manager",
        "docker": "Docker (for local testing)"
    }
    
    all_present = True
    for tool, description in tools.items():
        try:
            subprocess.run(
                [tool, "--version"],
                capture_output=True,
                timeout=5,
                check=True
            )
            print_status(f"✓ {description} installed", "SUCCESS")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_status(f"✗ {description} not found or not in PATH", "WARNING")
            all_present = False
    
    return all_present


def main():
    """Run all pre-flight checks."""
    print("\n" + "="*60)
    print("DEPLOYMENT PRE-FLIGHT CHECK")
    print("="*60 + "\n")
    
    checks = [
        ("Environment Configuration", check_env_file),
        ("Docker Configuration", check_docker),
        ("Railway Configuration", check_railway_config),
        ("Dependencies", check_dependencies),
        ("Backend Tests", check_backend_tests),
        ("Frontend Build", check_frontend_build),
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n--- {check_name} ---")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print_status(f"✗ Unexpected error: {e}", "ERROR")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {check_name}")
    
    print(f"\n{passed}/{total} checks passed")
    
    if passed == total:
        print_status("\n✓ All checks passed! Ready for deployment.", "SUCCESS")
        return 0
    else:
        print_status("\n✗ Some checks failed. Please review and fix before deploying.", "ERROR")
        return 1


if __name__ == "__main__":
    sys.exit(main())

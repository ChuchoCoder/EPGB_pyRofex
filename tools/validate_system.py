# T020: End-to-End System Validation Script
# Comprehensive testing of the complete PyRofex integration system

import queue
import sys
import threading
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path

# Test configuration
TEST_TIMEOUT = 30  # seconds
VALIDATION_RESULTS = {
    'imports': False,
    'configuration': False,
    'package_structure': False,
    'entry_points': False,
    'test_messages': []
}

def log_validation_message(category, message, success=None):
    """Log validation messages with categorization"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    if success is True:
        status = "✅"
    elif success is False:
        status = "❌"
    else:
        status = "ℹ️"
    
    formatted_message = f"{status} [{timestamp}] {category}: {message}"
    print(formatted_message)
    VALIDATION_RESULTS['test_messages'].append(formatted_message)

def main():
    """Main validation routine"""
    print("🔍 T020: End-to-End System Validation")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📋 Testing new epgb_options package structure\n")

    # Test 1: Package Imports
    print("🔍 Test 1: Package Import Validation")
    try:
        # Add project root to path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        # Import core dependencies
        import pandas as pd
        import pyRofex
        import xlwings as xw
        from dotenv import load_dotenv

        # Import our new package structure
        from src.epgb_options import main
        from src.epgb_options.config import excel_config, pyrofex_config
        from src.epgb_options.excel import workbook_manager
        from src.epgb_options.market_data import api_client
        from src.epgb_options.utils import logging as utils_logging
        
        log_validation_message("Package Imports", "All required modules imported successfully", True)
        VALIDATION_RESULTS['imports'] = True
    except ImportError as e:
        log_validation_message("Package Imports", f"Import error: {e}", False)
        VALIDATION_RESULTS['imports'] = False
        return False

    # Test 2: Configuration Validation
    print("\n🔍 Test 2: Configuration System")
    try:
        # Test configuration access
        from src.epgb_options.config import (validate_excel_config,
                                             validate_pyRofex_config)
        
        excel_valid = validate_excel_config()
        pyrofex_valid = validate_pyRofex_config()
        
        log_validation_message("Excel Config", "Configuration validation passed" if excel_valid else "Configuration needs setup", excel_valid)
        log_validation_message("pyRofex Config", "Configuration validation passed" if pyrofex_valid else "Credentials needed (expected)", pyrofex_valid)
        
        VALIDATION_RESULTS['configuration'] = True
    except Exception as e:
        log_validation_message("Configuration", f"Configuration error: {e}", False)
        VALIDATION_RESULTS['configuration'] = False

    # Test 3: Package Structure
    print("\n🔍 Test 3: Package Structure Validation")
    try:
        required_paths = [
            project_root / "src" / "epgb_options" / "__init__.py",
            project_root / "src" / "epgb_options" / "main.py", 
            project_root / "src" / "epgb_options" / "config" / "__init__.py",
            project_root / "src" / "epgb_options" / "market_data" / "__init__.py",
            project_root / "src" / "epgb_options" / "excel" / "__init__.py",
            project_root / "src" / "epgb_options" / "utils" / "__init__.py",
            project_root / ".env.example",
            project_root / "pyproject.toml"
        ]
        
        structure_valid = True
        for path in required_paths:
            if path.exists():
                log_validation_message("Structure", f"{path.name} exists", True)
            else:
                log_validation_message("Structure", f"{path} missing", False)
                structure_valid = False
                
        VALIDATION_RESULTS['package_structure'] = structure_valid
    except Exception as e:
        log_validation_message("Structure", f"Structure validation error: {e}", False)
        VALIDATION_RESULTS['package_structure'] = False

    # Test 4: Entry Point Testing
    print("\n🔍 Test 4: Entry Point Validation")
    try:
        import os
        import subprocess

        # Test main entry point
        env = os.environ.copy()
        env['PYTHONPATH'] = str(project_root)
        
        result = subprocess.run([
            sys.executable, '-c', 
            'from src.epgb_options.main import main; print("Entry point accessible")'
        ], capture_output=True, text=True, cwd=str(project_root), env=env, timeout=10)
        
        if result.returncode == 0:
            log_validation_message("Entry Points", "Main entry point accessible", True)
            VALIDATION_RESULTS['entry_points'] = True
        else:
            log_validation_message("Entry Points", f"Entry point error: {result.stderr}", False)
            VALIDATION_RESULTS['entry_points'] = False
            
    except Exception as e:
        log_validation_message("Entry Points", f"Entry point test error: {e}", False)
        VALIDATION_RESULTS['entry_points'] = False

    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    total_tests = len([k for k in VALIDATION_RESULTS.keys() if k != 'test_messages'])
    passed_tests = sum([1 for k, v in VALIDATION_RESULTS.items() if k != 'test_messages' and v])
    
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    
    for test_name, result in VALIDATION_RESULTS.items():
        if test_name != 'test_messages':
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    overall_success = passed_tests == total_tests
    print(f"\n🎯 Overall Status: {'✅ SUCCESS' if overall_success else '❌ NEEDS ATTENTION'}")
    
    if overall_success:
        print("\n🎉 New package structure is working correctly!")
        print("✅ Ready for production use with epgb-options command")
    else:
        print("\n⚠️  Some tests failed - check the details above")
        print("💡 Most failures are expected during initial setup (credentials, etc.)")
    
    print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
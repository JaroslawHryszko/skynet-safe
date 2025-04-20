#!/usr/bin/env python3
"""
SKYNET-SAFE Configuration Testing Script

This script tests the system configuration including:
- Local language model functionality
- Telegram communication
- External LLM (Claude) connectivity
- System requirements
"""

import argparse
import sys
import os
import json
from src.utils.config_tester import ConfigTester
from src.config import config


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test SKYNET-SAFE configuration components"
    )
    
    parser.add_argument(
        "--component",
        choices=["all", "model", "telegram", "external_llm", "system"],
        default="all",
        help="Which component to test (default: all)"
    )
    
    parser.add_argument(
        "--output", 
        default="config_test_results.json",
        help="Output file for test results (default: config_test_results.json)"
    )
    
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Show detailed test results"
    )
    
    parser.add_argument(
        "--quiet", 
        action="store_true",
        help="Show only critical errors, not full test results"
    )
    
    return parser.parse_args()


def main():
    """Main function for the configuration test script."""
    args = parse_arguments()
    
    try:
        # Build configuration dictionary
        system_config = {
            "MODEL": config.MODEL,
            "MEMORY": config.MEMORY,
            "COMMUNICATION": config.COMMUNICATION,
            "EXTERNAL_EVALUATION": config.EXTERNAL_EVALUATION
        }
        
        # Print header
        if not args.quiet:
            print("\n" + "="*70)
            print(" SKYNET-SAFE Configuration Test ")
            print("="*70)
        
        # Create tester instance
        tester = ConfigTester(system_config)
        
        # Run tests based on selected component
        results = None
        
        if args.component == "all":
            if not args.quiet:
                print("\nRunning ALL configuration tests...")
            results = tester.run_all_tests()
        elif args.component == "model":
            if not args.quiet:
                print("\nTesting LOCAL MODEL configuration...")
            results = {"local_model": tester.test_local_model()}
        elif args.component == "telegram":
            if not args.quiet:
                print("\nTesting TELEGRAM communication configuration...")
            results = {"telegram": tester.test_telegram()}
        elif args.component == "external_llm":
            if not args.quiet:
                print("\nTesting EXTERNAL LLM (Claude) configuration...")
            results = {"external_llm": tester.test_external_llm()}
        elif args.component == "system":
            if not args.quiet:
                print("\nTesting SYSTEM REQUIREMENTS...")
            results = {"system_requirements": tester.test_system_requirements()}
        
        # Save results if requested
        if args.output:
            output_file = tester.save_results(args.output)
            if not args.quiet:
                print(f"\nTest results saved to: {output_file}")
        
        # Print human-readable summary
        if not args.quiet:
            summary = tester._generate_summary()
            print("\n" + summary)
            
            if args.verbose and args.component == "all":
                print("\nDETAILED RESULTS:")
                print(json.dumps(results, indent=2))
            
            # Print clear final message about the test results
            overall_status = results.get("overall_status", "unknown")
            if overall_status == "success":
                print("\n✅ ALL TESTS PASSED - System is correctly configured")
            elif overall_status == "partial_success":
                print("\n⚠️ SOME TESTS PASSED WITH WARNINGS - System may have configuration issues")
            else:
                print("\n❌ SOME TESTS FAILED - System configuration has critical issues")
            
        return 0 if results.get("overall_status") == "success" else 1
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
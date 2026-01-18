#!/usr/bin/env python3
"""
Performance Code Checker - Pre-commit hook to prevent performance regressions.

This script checks for common performance anti-patterns:
- N+1 queries (loops with database queries)
- Missing caching in frontend
- Excessive default limits
- Sequential API calls

Usage:
    python scripts/check_performance.py
    # Or as pre-commit hook:
    ln -s ../../scripts/check_performance.py .git/hooks/pre-commit
"""

import os
import re
import sys
from pathlib import Path

# Color codes for output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

ERRORS = []
WARNINGS = []


def check_n1_queries():
    """Check for N+1 query anti-patterns in backend code."""
    print(f"{YELLOW}🔍 Checking for N+1 query patterns...{RESET}")
    
    api_dir = Path("src/api")
    if not api_dir.exists():
        return
    
    issues = []
    
    for py_file in api_dir.rglob("*.py"):
        with open(py_file, "r") as f:
            lines = f.readlines()
            in_loop = False
            loop_start = 0
            
            for i, line in enumerate(lines, 1):
                # Detect for loops
                if re.search(r"for\s+\w+\s+in\s+\w+:", line):
                    in_loop = True
                    loop_start = i
                    continue
                
                # Check if we're still in loop
                if in_loop:
                    # Check for indentation (still in loop)
                    if line.strip() and not line.startswith(" " * (lines[loop_start - 1].find("for") + 4)):
                        in_loop = False
                        continue
                    
                    # Check for database queries inside loop
                    if re.search(r"select\(|query\.where|db\.execute|session\.execute", line, re.IGNORECASE):
                        # Check if it's not a commented optimization
                        if not re.search(r"#.*(OPTIMIZED|GOOD|FIXED|JOIN)", line, re.IGNORECASE):
                            issues.append({
                                "file": str(py_file),
                                "line": i,
                                "issue": "Potential N+1 query: database query inside loop"
                            })
    
    if issues:
        ERRORS.extend(issues)
        print(f"{RED}❌ Found {len(issues)} potential N+1 query issues:{RESET}")
        for issue in issues[:5]:  # Show first 5
            print(f"  {issue['file']}:{issue['line']} - {issue['issue']}")
        if len(issues) > 5:
            print(f"  ... and {len(issues) - 5} more")
    else:
        print(f"{GREEN}✅ No N+1 query patterns detected{RESET}")


def check_frontend_caching():
    """Check that frontend uses caching for API calls."""
    print(f"{YELLOW}🔍 Checking frontend caching...{RESET}")
    
    index_html = Path("src/api/static/index.html")
    if not index_html.exists():
        return
    
    with open(index_html, "r") as f:
        content = f.read()
    
    # Count fetch() vs cachedFetch()
    fetch_calls = len(re.findall(r"await\s+fetch\(|fetch\(", content))
    cached_calls = len(re.findall(r"cachedFetch\(|DataCache\.", content))
    
    # Allow some fetch() calls for non-cached operations (health checks, etc.)
    if fetch_calls > cached_calls + 2:
        WARNINGS.append({
            "file": str(index_html),
            "issue": f"Found {fetch_calls} fetch() calls but only {cached_calls} cachedFetch() calls. "
                     "Most API calls should use cachedFetch() for performance."
        })
        print(f"{YELLOW}⚠️  Warning: {fetch_calls} fetch() vs {cached_calls} cachedFetch() calls{RESET}")
    else:
        print(f"{GREEN}✅ Frontend caching properly used{RESET}")


def check_default_limits():
    """Check for excessive default limits in API endpoints."""
    print(f"{YELLOW}🔍 Checking default limits...{RESET}")
    
    api_dir = Path("src/api")
    if not api_dir.exists():
        return
    
    issues = []
    
    for py_file in api_dir.rglob("*.py"):
        with open(py_file, "r") as f:
            for i, line in enumerate(f, 1):
                # Check for Query(default=...) with large values
                match = re.search(r"Query\(default=(\d+)", line)
                if match:
                    default_val = int(match.group(1))
                    if default_val > 20:
                        # Allow larger defaults with justification comment
                        next_line = f.readline() if i < len(f.readlines()) else ""
                        if not re.search(r"#.*(allow|justify|needed)", next_line, re.IGNORECASE):
                            issues.append({
                                "file": str(py_file),
                                "line": i,
                                "issue": f"Default limit {default_val} > 20 (should be ≤ 20 for performance)"
                            })
    
    if issues:
        WARNINGS.extend(issues)
        print(f"{YELLOW}⚠️  Found {len(issues)} large default limits:{RESET}")
        for issue in issues[:3]:
            print(f"  {issue['file']}:{issue['line']} - {issue['issue']}")
    else:
        print(f"{GREEN}✅ Default limits are reasonable{RESET}")


def check_performance_docs():
    """Check that performance documentation exists."""
    print(f"{YELLOW}🔍 Checking performance documentation...{RESET}")
    
    if not Path(".performance-rules.md").exists():
        ERRORS.append({
            "file": ".performance-rules.md",
            "issue": "Performance documentation missing"
        })
        print(f"{RED}❌ .performance-rules.md not found!{RESET}")
    else:
        print(f"{GREEN}✅ Performance documentation exists{RESET}")


def main():
    """Run all performance checks."""
    print("=" * 50)
    print("  PREDICTEDGE PERFORMANCE CHECK")
    print("=" * 50)
    print()
    
    # Run checks
    check_n1_queries()
    print()
    check_frontend_caching()
    print()
    check_default_limits()
    print()
    check_performance_docs()
    print()
    
    # Summary
    print("=" * 50)
    print("  SUMMARY")
    print("=" * 50)
    
    if ERRORS:
        print(f"{RED}❌ {len(ERRORS)} errors found{RESET}")
        print("\nPerformance errors must be fixed before committing!")
        print("See .performance-rules.md for optimization patterns.")
        return 1
    
    if WARNINGS:
        print(f"{YELLOW}⚠️  {len(WARNINGS)} warnings{RESET}")
        print("\nConsider addressing these warnings for better performance.")
        return 0
    
    print(f"{GREEN}✅ All performance checks passed!{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


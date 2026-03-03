#!/usr/bin/env python3
"""
SI3LN — Run All Tests
======================
Master test runner that executes all test suites and produces a unified report.

Usage:
    python Tests/run_all_tests.py
    
    # With custom endpoints:
    SI3LN_API_URL=http://localhost:8000 SI3LN_FRONTEND_URL=http://localhost python Tests/run_all_tests.py

    # Run specific suites only:
    python Tests/run_all_tests.py --auth --api
    python Tests/run_all_tests.py --frontend
    python Tests/run_all_tests.py --profile

Suites:
    --auth          Authentication tests (register, login, token, permissions)
    --api           Full API endpoint tests (public, protected, edge cases)
    --frontend      Frontend HTML/CSS/JS structure tests
    --profile       Profile CRUD, avatar upload, bio, settings tests
    --authorization IDOR / cross-user access tests
    --auth-edge     Auth edge cases (password change, token refresh)
    --session-edge  Session edge cases (re-complete, filters, boundaries)
    --game-units    Offline unit tests for Game_Python modules
    --facade        Facade sanitization & validation (offline)
    --avatar-edge   Avatar upload edge cases (SVG, format, size)
    --all           Run everything (default)
"""

import os
import sys
import time
import subprocess
import argparse

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
WARN = "\033[93m⚠\033[0m"
INFO = "\033[94mℹ\033[0m"
BOLD = "\033[1m"
RESET = "\033[0m"

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TESTS_DIR)

# Test suites
SUITES = {
    "auth":       {"file": "test_auth.py",             "label": "Authentication"},
    "api":        {"file": "test_api_full.py",          "label": "API Endpoints (Full)"},
    "frontend":   {"file": "test_frontend.py",          "label": "Frontend"},
    "profile":    {"file": "test_profile.py",           "label": "Profile & Avatar"},
    "security":   {"file": "test_security.py",          "label": "Security"},
    "perf":       {"file": "test_performance.py",       "label": "Performance"},
    "integrity":  {"file": "test_data_integrity.py",    "label": "Data Integrity"},
    "validation": {"file": "test_input_validation.py",  "label": "Input Validation"},
    "e2e":        {"file": "test_e2e_flow.py",          "label": "End-to-End Flow"},
    "ratelimit":      {"file": "test_rate_limiting.py",      "label": "Rate Limiting"},
    "authorization":  {"file": "test_authorization.py",      "label": "Authorization (IDOR)"},
    "auth_edge":      {"file": "test_auth_edge_cases.py",    "label": "Auth Edge Cases"},
    "session_edge":   {"file": "test_session_edge_cases.py",  "label": "Session Edge Cases"},
    "game_units":     {"file": "test_game_units.py",          "label": "Game Unit Tests"},
    "facade":         {"file": "test_facade.py",              "label": "Facade (Security)"},
    "avatar_edge":    {"file": "test_avatar_edge_cases.py",   "label": "Avatar Edge Cases"},
}


def run_suite(name: str, info: dict) -> tuple[bool, float]:
    """Run a single test suite, return (passed: bool, duration: float)"""
    script = os.path.join(TESTS_DIR, info["file"])
    
    if not os.path.isfile(script):
        print(f"  {FAIL} {info['label']}: file not found ({info['file']})")
        return False, 0.0
    
    print(f"\n{'▓' * 60}")
    print(f"  {BOLD}Running: {info['label']}{RESET}")
    print(f"  File:    {info['file']}")
    print(f"{'▓' * 60}")
    
    t0 = time.time()
    result = subprocess.run(
        [sys.executable, script],
        cwd=PROJECT_DIR,
        env={**os.environ},
        timeout=120,
    )
    duration = time.time() - t0
    
    passed = result.returncode == 0
    return passed, duration


def check_server_health():
    """Quick connectivity check before running tests."""
    import requests
    
    api_url = os.environ.get("SI3LN_API_URL", "http://localhost:8000")
    frontend_url = os.environ.get("SI3LN_FRONTEND_URL", "http://localhost")
    
    print(f"\n{'═' * 60}")
    print(f"  {BOLD}SI3LN Test Runner — Pre-flight Checks{RESET}")
    print(f"{'═' * 60}")
    
    # Check API
    try:
        r = requests.get(f"{api_url}/api/game/stats", timeout=5)
        if r.status_code == 200:
            print(f"  {PASS} API reachable at {api_url}")
            api_ok = True
        else:
            print(f"  {WARN} API returned HTTP {r.status_code} at {api_url}")
            api_ok = True  # Reachable but maybe not fully up
    except requests.exceptions.ConnectionError:
        print(f"  {FAIL} API not reachable at {api_url}")
        api_ok = False
    except Exception as e:
        print(f"  {FAIL} API check error: {e}")
        api_ok = False
    
    # Check Frontend
    try:
        r = requests.get(frontend_url, timeout=5)
        if r.status_code == 200:
            print(f"  {PASS} Frontend reachable at {frontend_url}")
            frontend_ok = True
        else:
            print(f"  {WARN} Frontend returned HTTP {r.status_code}")
            frontend_ok = True
    except requests.exceptions.ConnectionError:
        print(f"  {FAIL} Frontend not reachable at {frontend_url}")
        frontend_ok = False
    except Exception as e:
        print(f"  {FAIL} Frontend check error: {e}")
        frontend_ok = False
    
    return api_ok, frontend_ok


def main():
    parser = argparse.ArgumentParser(description="SI3LN Test Runner")
    parser.add_argument("--auth", action="store_true", help="Run auth tests")
    parser.add_argument("--api", action="store_true", help="Run API tests")
    parser.add_argument("--frontend", action="store_true", help="Run frontend tests")
    parser.add_argument("--profile", action="store_true", help="Run profile tests")
    parser.add_argument("--security", action="store_true", help="Run security tests")
    parser.add_argument("--perf", action="store_true", help="Run performance tests")
    parser.add_argument("--integrity", action="store_true", help="Run data integrity tests")
    parser.add_argument("--validation", action="store_true", help="Run input validation tests")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end flow tests")
    parser.add_argument("--ratelimit", action="store_true", help="Run rate limiting tests")
    parser.add_argument("--authorization", action="store_true", help="Run IDOR / authorization tests")
    parser.add_argument("--auth-edge", dest="auth_edge", action="store_true", help="Run auth edge-case tests")
    parser.add_argument("--session-edge", dest="session_edge", action="store_true", help="Run session edge-case tests")
    parser.add_argument("--game-units", dest="game_units", action="store_true", help="Run offline game unit tests")
    parser.add_argument("--facade", action="store_true", help="Run facade security tests")
    parser.add_argument("--avatar-edge", dest="avatar_edge", action="store_true", help="Run avatar edge-case tests")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    parser.add_argument("--skip-health", action="store_true", help="Skip server health check")
    args = parser.parse_args()
    
    # Determine which suites to run
    selected = []
    for key in SUITES:
        if getattr(args, key, False):
            selected.append(key)
    
    if not selected or args.all:
        selected = list(SUITES.keys())
    
    # Health check
    if not args.skip_health:
        try:
            api_ok, frontend_ok = check_server_health()
        except ImportError:
            print(f"  {WARN} 'requests' not installed — skipping health check")
            print(f"  {INFO} Install with: pip install requests")
            api_ok = True
            frontend_ok = True
        
        if not api_ok:
            print(f"\n  {FAIL} Cannot reach API server.")
            print(f"  {INFO} Start services with:")
            print(f"       docker compose -f Docker/docker-compose.yml up -d")
            print(f"       — or —")
            print(f"       cd api && python manage.py runserver\n")
            
            # Remove API-dependent tests if API is down
            if "auth" in selected:
                selected.remove("auth")
            if "api" in selected:
                selected.remove("api")
            if "profile" in selected:
                selected.remove("profile")
            
            if not selected:
                print(f"  {FAIL} No tests can run without the server.\n")
                return 1
        
        if not frontend_ok and "frontend" in selected:
            print(f"\n  {WARN} Frontend not reachable — skipping frontend tests.\n")
            selected.remove("frontend")
    
    # Run selected suites
    results = {}
    total_time = 0.0
    
    for name in selected:
        info = SUITES[name]
        try:
            passed, duration = run_suite(name, info)
            results[name] = {"passed": passed, "duration": duration}
            total_time += duration
        except subprocess.TimeoutExpired:
            print(f"\n  {FAIL} {info['label']}: TIMEOUT (>120s)")
            results[name] = {"passed": False, "duration": 120.0}
            total_time += 120.0
        except Exception as e:
            print(f"\n  {FAIL} {info['label']}: ERROR — {e}")
            results[name] = {"passed": False, "duration": 0.0}
    
    # ── Final Report ──────────────────────────────────────────────────────────
    print(f"\n{'═' * 60}")
    print(f"  {BOLD}SI3LN Test Results — Final Report{RESET}")
    print(f"{'═' * 60}")
    
    all_passed = True
    for name in selected:
        info = SUITES[name]
        r = results[name]
        status = PASS if r["passed"] else FAIL
        duration_str = f"{r['duration']:.1f}s"
        print(f"  {status} {info['label']:<30} {duration_str:>8}")
        if not r["passed"]:
            all_passed = False
    
    print(f"{'─' * 60}")
    print(f"  Total time: {total_time:.1f}s")
    
    if all_passed:
        print(f"\n  \033[92m{'═' * 50}\033[0m")
        print(f"  \033[92m  ALL {len(selected)} TEST SUITE(S) PASSED  \033[0m")
        print(f"  \033[92m{'═' * 50}\033[0m\n")
    else:
        failed_names = [SUITES[n]["label"] for n in selected if not results[n]["passed"]]
        print(f"\n  \033[91m{'═' * 50}\033[0m")
        print(f"  \033[91m  SOME TESTS FAILED:\033[0m")
        for fn in failed_names:
            print(f"  \033[91m    • {fn}\033[0m")
        print(f"  \033[91m{'═' * 50}\033[0m\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

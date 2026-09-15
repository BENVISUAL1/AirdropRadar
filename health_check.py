"""
AirdropRadar — V1 Health Check

Purpose:
    Verify that the major AirdropRadar components
    are available and functioning correctly.

Version:
    1.0.0
"""

import os
import importlib


def print_result(name, success, message=""):
    if success:
        print(f"✅ {name}: OK")
    else:
        print(f"❌ {name}: FAILED")

    if message:
        print(f"   {message}")


def check_database():
    try:
        import database

        database.create_database()

        total = database.get_total_airdrops()

        return True, f"{total} airdrops stored."

    except Exception as error:
        return False, str(error)


def check_classifier():
    try:
        filter_module = importlib.import_module(
            "filter"
        )

        required_function = getattr(
            filter_module,
            "run_live_classification",
            None
        )

        if required_function is None:
            return False, (
                "run_live_classification() "
                "not found in filter.py."
            )

        version = getattr(
            filter_module,
            "CLASSIFIER_VERSION",
            "unknown"
        )

        return True, (
            "Classifier available through "
            f"filter.py. Version: {version}"
        )

    except Exception as error:
        return False, str(error)


def check_verifier():
    try:
        verifier = importlib.import_module(
            "verifier"
        )

        required_function = getattr(
            verifier,
            "verify_candidate",
            None
        )

        if required_function is None:
            return False, (
                "verify_candidate() not found."
            )

        return True, (
            "Verifier module and "
            "verify_candidate() available."
        )

    except Exception as error:
        return False, str(error)


def check_api_sources():
    try:
        api_sources = importlib.import_module(
            "api_sources"
        )

        required_function = getattr(
            api_sources,
            "get_project_intelligence",
            None
        )

        if required_function is None:
            return False, (
                "get_project_intelligence() "
                "not found."
            )

        return True, (
            "API intelligence module available."
        )

    except Exception as error:
        return False, str(error)


def check_tracker():
    try:
        tracker = importlib.import_module(
            "tracker"
        )

        required_function = getattr(
            tracker,
            "run_tracking_cycle",
            None
        )

        if required_function is None:
            return False, (
                "run_tracking_cycle() not found."
            )

        return True, (
            "Tracking system available."
        )

    except Exception as error:
        return False, str(error)


def check_filter():
    try:
        filter_module = importlib.import_module(
            "filter"
        )

        required_function = getattr(
            filter_module,
            "run_scan",
            None
        )

        if required_function is None:
            return False, (
                "run_scan() not found."
            )

        return True, (
            "Discovery/scanner system available."
        )

    except Exception as error:
        return False, str(error)


def check_bot_config():
    try:
        import config

        token = config.require_bot_token()

        if not token:
            return False, (
                "Telegram bot token is empty."
            )

        return True, (
            "Telegram bot configuration available."
        )

    except Exception as error:
        return False, str(error)


def main():

    print()
    print("=" * 60)
    print("🩺 AirdropRadar V1 Health Check")
    print("=" * 60)

    checks = [
        (
            "Database",
            check_database,
        ),
        (
            "Classifier",
            check_classifier,
        ),
        (
            "Verifier",
            check_verifier,
        ),
        (
            "API intelligence",
            check_api_sources,
        ),
        (
            "Tracker",
            check_tracker,
        ),
        (
            "Discovery scanner",
            check_filter,
        ),
        (
            "Telegram configuration",
            check_bot_config,
        ),
    ]

    passed = 0
    failed = 0

    print()

    for name, check_function in checks:

        try:
            success, message = check_function()

        except Exception as error:
            success = False
            message = str(error)

        print_result(
            name,
            success,
            message,
        )

        if success:
            passed += 1
        else:
            failed += 1

    print()
    print("=" * 60)
    print("📊 HEALTH CHECK SUMMARY")
    print("=" * 60)

    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    print()

    if failed == 0:
        print(
            "🟢 AirdropRadar V1 system health: "
            "HEALTHY"
        )
    else:
        print(
            "🔴 AirdropRadar V1 system health: "
            "NEEDS ATTENTION"
        )

    print("=" * 60)


if __name__ == "__main__":
    main()
    
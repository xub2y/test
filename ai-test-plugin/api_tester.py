import copy
import time

import requests


def run_api_tests(config, cases):
    base_url = config["base_url"]
    timeout = config.get("request_timeout", 30)
    context = build_runtime_context()
    results = []

    for case in cases:
        setup_results = []
        for setup_step in case.get("setup", []):
            setup_results.append(send_case_request(base_url, setup_step, context, timeout))

        actual = send_case_request(base_url, case, context, timeout)
        body_text = str(actual["body"])

        passed = (
            actual["status_code"] == case["expected_status"]
            and case["expected_text"] in body_text
        )

        resolved_payload = resolve_placeholders(case.get("payload", {}), context)

        results.append({
            "case_id": case["case_id"],
            "module": case.get("module", ""),
            "name": case["name"],
            "request": {
                "method": case.get("method", "POST"),
                "api": case["path"],
                "payload": resolved_payload
            },
            "expected": {
                "status_code": case["expected_status"],
                "text": case["expected_text"]
            },
            "actual": actual,
            "setup_results": setup_results,
            "result": "PASS" if passed else "FAIL"
        })

    return results


def build_runtime_context():
    suffix = str(int(time.time()))
    return {
        "valid_password": "123456",
        "short_username": "u" + suffix[-4:],
        "six_char_username": "u" + suffix[-5:],
        "valid_username_a": "ua" + suffix[-8:],
        "valid_username_b": "ub" + suffix[-8:],
        "valid_username_c": "uc" + suffix[-8:],
        "duplicate_username": "dup" + suffix[-7:],
        "login_username": "login" + suffix[-6:],
        "wrong_password_username": "wrong" + suffix[-6:],
        "unregistered_username": "none" + suffix[-6:]
    }


def send_case_request(base_url, case, context, timeout):
    method = case.get("method", "POST").upper()
    url = base_url + case["path"]
    payload = resolve_placeholders(case.get("payload"), context)
    params = resolve_placeholders(case.get("params"), context)
    headers = resolve_placeholders(case.get("headers"), context) or {}

    try:
        session = requests.Session()
        session.trust_env = False
        response = session.request(
            method,
            url,
            json=payload if payload is not None else None,
            params=params if params is not None else None,
            headers=headers,
            timeout=timeout
        )
        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text}

        return {
            "status_code": response.status_code,
            "body": body
        }
    except requests.RequestException as error:
        return {
            "status_code": None,
            "body": {"error": str(error)}
        }


def resolve_placeholders(value, context):
    resolved = copy.deepcopy(value)

    if isinstance(resolved, str):
        for key, replacement in context.items():
            resolved = resolved.replace("{{" + key + "}}", replacement)
        return resolved

    if isinstance(resolved, list):
        return [resolve_placeholders(item, context) for item in resolved]

    if isinstance(resolved, dict):
        return {
            key: resolve_placeholders(item, context)
            for key, item in resolved.items()
        }

    return resolved

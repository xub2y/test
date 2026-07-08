import time

import requests


def post_json(base_url, path, payload):
    url = base_url + path

    try:
        response = requests.post(url, json=payload, timeout=5)
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


def run_api_tests(config):
    base_url = config["base_url"]
    register_path = config["api"]["register"]

    suffix = str(int(time.time()))
    short_username = "u" + suffix[-4:]
    valid_username = "user" + suffix[-6:]

    cases = [
        {
            "case_id": "TC-001",
            "name": "用户名为空时注册失败",
            "api": register_path,
            "payload": {"username": "", "password": "123456"},
            "expected_status": 400,
            "expected_text": "用户名不能为空"
        },
        {
            "case_id": "TC-002",
            "name": "用户名小于6位时注册失败",
            "api": register_path,
            "payload": {"username": short_username, "password": "123456"},
            "expected_status": 400,
            "expected_text": "用户名长度不能少于6位"
        },
        {
            "case_id": "TC-003",
            "name": "用户名等于6位以上时注册成功",
            "api": register_path,
            "payload": {"username": valid_username, "password": "123456"},
            "expected_status": 200,
            "expected_text": "注册成功"
        }
    ]

    results = []

    for case in cases:
        actual = post_json(base_url, case["api"], case["payload"])
        body_text = str(actual["body"])

        passed = (
            actual["status_code"] == case["expected_status"]
            and case["expected_text"] in body_text
        )

        results.append({
            "case_id": case["case_id"],
            "name": case["name"],
            "request": {
                "api": case["api"],
                "payload": case["payload"]
            },
            "expected": {
                "status_code": case["expected_status"],
                "text": case["expected_text"]
            },
            "actual": actual,
            "result": "PASS" if passed else "FAIL"
        })

    return results

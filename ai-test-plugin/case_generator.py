import json


def generate_test_cases(prd_text, config, base_dir):
    cases = build_cases_from_prd(prd_text, config)
    output_path = base_dir / config["generated"]["test_cases"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(cases, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    return cases, output_path


def build_cases_from_prd(prd_text, config):
    register_path = config["api"].get("register")
    login_path = config["api"].get("login")

    cases = []

    if register_path:
        if "用户名不能为空" in prd_text:
            cases.append({
                "case_id": "TC-001",
                "module": "用户注册",
                "name": "用户名为空时注册失败",
                "method": "POST",
                "path": register_path,
                "payload": {"username": "", "password": "{{valid_password}}"},
                "expected_status": 400,
                "expected_text": "用户名不能为空"
            })

        if "用户名长度" in prd_text and "6-20" in prd_text:
            cases.extend([
                {
                    "case_id": "TC-002",
                    "module": "用户注册",
                    "name": "用户名小于6位时注册失败",
                    "method": "POST",
                    "path": register_path,
                    "payload": {"username": "{{short_username}}", "password": "{{valid_password}}"},
                    "expected_status": 400,
                    "expected_text": "用户名长度不能少于6位"
                },
                {
                    "case_id": "TC-003",
                    "module": "用户注册",
                    "name": "用户名等于6位时注册成功",
                    "method": "POST",
                    "path": register_path,
                    "payload": {"username": "{{six_char_username}}", "password": "{{valid_password}}"},
                    "expected_status": 200,
                    "expected_text": "注册成功"
                },
                {
                    "case_id": "TC-004",
                    "module": "用户注册",
                    "name": "用户名超过20位时注册失败",
                    "method": "POST",
                    "path": register_path,
                    "payload": {"username": "abcdefghijklmnopqrstu", "password": "{{valid_password}}"},
                    "expected_status": 400,
                    "expected_text": "用户名长度不能超过20位"
                }
            ])

        if "密码不能为空" in prd_text:
            cases.append({
                "case_id": "TC-005",
                "module": "用户注册",
                "name": "密码为空时注册失败",
                "method": "POST",
                "path": register_path,
                "payload": {"username": "{{valid_username_a}}", "password": ""},
                "expected_status": 400,
                "expected_text": "密码不能为空"
            })

        if "密码长度不能少于 6 位" in prd_text or "密码长度不能少于6位" in prd_text:
            cases.append({
                "case_id": "TC-006",
                "module": "用户注册",
                "name": "密码小于6位时注册失败",
                "method": "POST",
                "path": register_path,
                "payload": {"username": "{{valid_username_b}}", "password": "123"},
                "expected_status": 400,
                "expected_text": "密码长度不能少于6位"
            })

        if "用户名不能重复" in prd_text:
            duplicate_payload = {"username": "{{duplicate_username}}", "password": "{{valid_password}}"}
            cases.append({
                "case_id": "TC-007",
                "module": "用户注册",
                "name": "重复用户名注册失败",
                "method": "POST",
                "path": register_path,
                "setup": [
                    {
                        "method": "POST",
                        "path": register_path,
                        "payload": duplicate_payload
                    }
                ],
                "payload": duplicate_payload,
                "expected_status": 400,
                "expected_text": "该用户名已被注册"
            })

    if login_path:
        if "正确密码" in prd_text or "正确账号密码" in prd_text:
            login_payload = {"username": "{{login_username}}", "password": "{{valid_password}}"}
            cases.append({
                "case_id": "TC-008",
                "module": "用户登录",
                "name": "正确账号密码登录成功",
                "method": "POST",
                "path": login_path,
                "setup": [
                    {
                        "method": "POST",
                        "path": register_path,
                        "payload": login_payload
                    }
                ],
                "payload": login_payload,
                "expected_status": 200,
                "expected_text": "登录成功"
            })

        if "密码错误" in prd_text:
            cases.append({
                "case_id": "TC-009",
                "module": "用户登录",
                "name": "密码错误时登录失败",
                "method": "POST",
                "path": login_path,
                "setup": [
                    {
                        "method": "POST",
                        "path": register_path,
                        "payload": {"username": "{{wrong_password_username}}", "password": "{{valid_password}}"}
                    }
                ],
                "payload": {"username": "{{wrong_password_username}}", "password": "wrong-password"},
                "expected_status": 401,
                "expected_text": "用户名或密码错误"
            })

        if "未注册用户" in prd_text:
            cases.append({
                "case_id": "TC-010",
                "module": "用户登录",
                "name": "未注册用户登录失败",
                "method": "POST",
                "path": login_path,
                "payload": {"username": "{{unregistered_username}}", "password": "{{valid_password}}"},
                "expected_status": 401,
                "expected_text": "用户名或密码错误"
            })

        if "用户名不能为空" in prd_text:
            cases.append({
                "case_id": "TC-011",
                "module": "用户登录",
                "name": "登录用户名为空时失败",
                "method": "POST",
                "path": login_path,
                "payload": {"username": "", "password": "{{valid_password}}"},
                "expected_status": 400,
                "expected_text": "用户名不能为空"
            })

        if "密码不能为空" in prd_text:
            cases.append({
                "case_id": "TC-012",
                "module": "用户登录",
                "name": "登录密码为空时失败",
                "method": "POST",
                "path": login_path,
                "payload": {"username": "{{valid_username_c}}", "password": ""},
                "expected_status": 400,
                "expected_text": "密码不能为空"
            })

    return cases

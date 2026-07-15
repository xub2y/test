import json
import os
import re


PLACEHOLDER_GUIDE = [
    "valid_password",
    "short_username",
    "six_char_username",
    "valid_username_a",
    "valid_username_b",
    "valid_username_c",
    "duplicate_username",
    "login_username",
    "wrong_password_username",
    "unregistered_username"
]


def generate_test_cases(prd_text, config, base_dir):
    cases, generation_meta = generate_cases_from_prd(prd_text, config)
    try:
        cases = normalize_cases(cases)
    except Exception as error:
        if generation_meta.get("source") != "openai":
            raise

        cases = normalize_cases(build_cases_from_prd(prd_text, config))
        generation_meta = {
            "source": "rule_fallback",
            "provider": generation_meta.get("provider", "openai"),
            "model": generation_meta.get("model"),
            "reason": f"llm response validation failed: {error}"
        }

    output_path = base_dir / config["generated"]["test_cases"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(cases, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    generation_meta = {
        **generation_meta,
        "case_count": len(cases)
    }
    save_generation_meta(base_dir, config, generation_meta)

    return cases, output_path, generation_meta


def generate_cases_from_prd(prd_text, config):
    llm_config = config.get("llm", {})

    if is_llm_enabled(llm_config):
        try:
            return build_cases_with_openai(prd_text, config)
        except Exception as error:
            return build_cases_from_prd(prd_text, config), {
                "source": "rule_fallback",
                "provider": llm_config.get("provider", "openai"),
                "reason": str(error)
            }

    return build_cases_from_prd(prd_text, config), {
        "source": "rule_fallback",
        "reason": "llm disabled"
    }


def is_llm_enabled(llm_config):
    override = os.getenv("AI_TEST_LLM_ENABLED")
    if override:
        return override.lower() not in {"0", "false", "no", "off"}

    return bool(llm_config.get("enabled", False))


def build_cases_with_openai(prd_text, config):
    llm_config = config.get("llm", {})
    provider = llm_config.get("provider", "openai")

    if provider != "openai":
        raise ValueError(f"unsupported llm provider: {provider}")

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set")

    try:
        from openai import OpenAI
    except ImportError as error:
        raise RuntimeError("openai package is not installed") from error

    model = os.getenv("OPENAI_MODEL") or llm_config.get("model", "gpt-5.6")
    client = OpenAI()
    output_text, api_name = request_openai_json(
        client=client,
        model=model,
        system_prompt=build_system_prompt(),
        user_prompt=build_user_prompt(prd_text, config)
    )

    payload = parse_json_payload(output_text)
    if isinstance(payload, dict):
        cases = payload.get("test_cases")
    elif isinstance(payload, list):
        cases = payload
    else:
        cases = None

    if not cases:
        raise ValueError("llm response does not contain test_cases")

    return cases, {
        "source": "openai",
        "provider": "openai",
        "model": model,
        "api": api_name
    }


def request_openai_json(client, model, system_prompt, user_prompt):
    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            text={"format": {"type": "json_object"}}
        )
        return response.output_text, "responses"
    except Exception as responses_error:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            return completion.choices[0].message.content, "chat.completions"
        except Exception as chat_error:
            raise RuntimeError(
                f"openai call failed; responses error: {responses_error}; "
                f"chat completions error: {chat_error}"
            ) from chat_error


def build_system_prompt():
    return (
        "你是资深测试工程师。你的任务是根据 PRD 和接口配置生成接口自动化测试用例。"
        "只输出 JSON，不输出 Markdown，不解释。"
    )


def build_user_prompt(prd_text, config):
    api_config = json.dumps(config.get("api", {}), ensure_ascii=False, indent=2)
    placeholders = ", ".join("{{" + item + "}}" for item in PLACEHOLDER_GUIDE)

    return f"""
请根据下面的 PRD 生成接口测试用例。

要求：
1. 输出必须是 JSON 对象，顶层字段为 test_cases。
2. 每条用例字段必须包含：case_id、module、name、method、path、payload、expected_status、expected_text。
3. 如用例需要前置数据，例如登录前先注册、重复注册前先创建用户，请添加 setup 数组。
4. path 只能使用接口配置中给出的接口路径。
5. expected_status 和 expected_text 必须来自 PRD 中的预期业务规则，不要根据现有代码行为猜测。
6. 优先覆盖正常流程、必填校验、边界值、重复数据、认证失败等场景。
7. 可以使用这些占位符避免重复运行冲突：{placeholders}。

接口配置：
{api_config}

输出示例：
{{
  "test_cases": [
    {{
      "case_id": "TC-001",
      "module": "用户注册",
      "name": "用户名为空时注册失败",
      "method": "POST",
      "path": "/api/register",
      "payload": {{"username": "", "password": "{{{{valid_password}}}}"}},
      "expected_status": 400,
      "expected_text": "用户名不能为空"
    }}
  ]
}}

PRD：
{prd_text}
""".strip()


def parse_json_payload(output_text):
    if not output_text:
        raise ValueError("llm response is empty")

    try:
        return json.loads(output_text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", output_text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(1))


def normalize_cases(cases):
    if not isinstance(cases, list):
        raise ValueError("test cases must be a list")

    normalized = []
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            raise ValueError(f"test case #{index} is not an object")

        expected_status = case.get("expected_status")
        try:
            expected_status = int(expected_status)
        except (TypeError, ValueError) as error:
            raise ValueError(f"test case #{index} has invalid expected_status") from error

        path = case.get("path")
        if not path:
            raise ValueError(f"test case #{index} missing path")

        expected_text = case.get("expected_text")
        if expected_text is None:
            raise ValueError(f"test case #{index} missing expected_text")

        normalized_case = {
            "case_id": str(case.get("case_id") or f"TC-{index:03d}"),
            "module": str(case.get("module") or ""),
            "name": str(case.get("name") or f"用例 {index}"),
            "method": str(case.get("method") or "POST").upper(),
            "path": normalize_path(path),
            "payload": case.get("payload") if "payload" in case else None,
            "expected_status": expected_status,
            "expected_text": str(expected_text)
        }

        for optional_field in ("params", "headers"):
            if optional_field in case:
                normalized_case[optional_field] = case[optional_field]

        setup_steps = normalize_setup_steps(case.get("setup", []))
        if setup_steps:
            normalized_case["setup"] = setup_steps

        normalized.append(normalized_case)

    if not normalized:
        raise ValueError("no test cases generated")

    return normalized


def normalize_setup_steps(setup_steps):
    if not setup_steps:
        return []

    if not isinstance(setup_steps, list):
        raise ValueError("setup must be a list")

    normalized_steps = []
    for index, step in enumerate(setup_steps, start=1):
        if not isinstance(step, dict):
            raise ValueError(f"setup step #{index} is not an object")

        path = step.get("path")
        if not path:
            raise ValueError(f"setup step #{index} missing path")

        normalized_step = {
            "method": str(step.get("method") or "POST").upper(),
            "path": normalize_path(path),
            "payload": step.get("payload") if "payload" in step else None
        }

        for optional_field in ("params", "headers"):
            if optional_field in step:
                normalized_step[optional_field] = step[optional_field]

        normalized_steps.append(normalized_step)

    return normalized_steps


def normalize_path(path):
    path = str(path)
    return path if path.startswith("/") else f"/{path}"


def save_generation_meta(base_dir, config, generation_meta):
    meta_path = base_dir / config.get("generated", {}).get(
        "generation_meta",
        "generated/generation_meta.json"
    )
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(
        json.dumps(generation_meta, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


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

from datetime import datetime


def generate_outputs(config, results, base_dir):
    report_path = base_dir / config["outputs"]["test_report"]
    bugs_path = base_dir / config["outputs"]["bugs"]

    report_path.parent.mkdir(parents=True, exist_ok=True)
    bugs_path.parent.mkdir(parents=True, exist_ok=True)

    report_path.write_text(build_test_report(config, results), encoding="utf-8")
    bugs_path.write_text(build_bug_report(results), encoding="utf-8")

    return report_path, bugs_path


def build_test_report(config, results):
    total = len(results)
    passed = len([item for item in results if item["result"] == "PASS"])
    failed = total - passed
    pass_rate = round((passed / total) * 100, 2) if total else 0

    lines = [
        f"# {config['project_name']}测试报告",
        "",
        "## 1. 测试概述",
        "",
        f"- 项目名称：{config['project_name']}",
        f"- 被测服务地址：{config['base_url']}",
        f"- 报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "- 测试类型：接口自动化测试",
        "",
        "## 2. 执行统计",
        "",
        f"- 用例总数：{total}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        f"- 通过率：{pass_rate}%",
        "",
        "## 3. 执行明细",
        "",
        "| 用例编号 | 模块 | 用例名称 | 预期状态码 | 实际状态码 | 结果 |",
        "|---|---|---|---:|---:|---|"
    ]

    for item in results:
        lines.append(
            f"| {item['case_id']} | {item.get('module', '')} | {item['name']} | "
            f"{item['expected']['status_code']} | "
            f"{item['actual']['status_code']} | {item['result']} |"
        )

    failed_cases = [item for item in results if item["result"] == "FAIL"]
    lines.extend([
        "",
        "## 4. 测试结论",
        "",
        build_summary(failed_cases) if failed else
        "本次测试全部通过。"
    ])

    return "\n".join(lines) + "\n"


def build_bug_report(results):
    failed_cases = [item for item in results if item["result"] == "FAIL"]

    if not failed_cases:
        return "# Bug 单\n\n本次测试未发现 Bug。\n"

    lines = ["# Bug 单", ""]

    for index, item in enumerate(failed_cases, start=1):
        bug_id = f"BUG-{index:03d}"
        suggestion = build_fix_suggestion(item)

        lines.extend([
            f"## {bug_id} {item['name']}",
            "",
            f"- 关联用例：{item['case_id']}",
            f"- 所属模块：{item.get('module', '')}",
            "- 严重级别：Major",
            "- 优先级：P1",
            f"- 请求接口：{item['request']['api']}",
            f"- 请求数据：`{item['request']['payload']}`",
            f"- 预期结果：状态码 {item['expected']['status_code']}，响应包含 `{item['expected']['text']}`",
            f"- 实际结果：状态码 {item['actual']['status_code']}，响应内容 `{item['actual']['body']}`",
            "",
            "### 修复建议",
            "",
            suggestion,
            ""
        ])

    return "\n".join(lines)


def build_summary(failed_cases):
    failed_names = "、".join([item["name"] for item in failed_cases])
    return f"本次测试发现 {len(failed_cases)} 个失败用例：{failed_names}。请优先检查接口实现与 PRD 需求是否一致。"


def build_fix_suggestion(item):
    expected_text = item["expected"]["text"]

    if "用户名长度不能少于6位" in expected_text:
        return "在后端注册接口中补充用户名最小长度校验：当用户名长度小于 6 位时，返回 400，并提示用户名长度不能少于6位。"

    return f"根据关联需求补充接口校验或修正业务逻辑，确保接口返回状态码 {item['expected']['status_code']}，且响应内容包含 `{expected_text}`。"

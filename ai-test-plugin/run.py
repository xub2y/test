import json
from pathlib import Path

from api_tester import run_api_tests
from case_generator import generate_test_cases
from report_generator import generate_outputs

BASE_DIR = Path(__file__).resolve().parent


def load_config():
    config_path = BASE_DIR / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_file(relative_path):
    file_path = BASE_DIR / relative_path
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def save_json(relative_path, data):
    file_path = BASE_DIR / relative_path
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    config = load_config()

    prd = read_file(config["docs"]["prd"])
    requirements = read_file(config["docs"]["requirements"])
    test_cases = read_file(config["docs"]["test_cases"])

    print("AI 自动化测试插件原型启动成功")
    print(f"项目名称：{config['project_name']}")
    print(f"PRD 文档长度：{len(prd)} 字符")
    print(f"需求文档长度：{len(requirements)} 字符")
    print(f"测试用例文档长度：{len(test_cases)} 字符")

    print("开始根据 PRD 生成结构化测试用例...")
    generated_cases, generated_case_path, generation_meta = generate_test_cases(prd, config, BASE_DIR)
    print(f"已生成测试用例：{len(generated_cases)} 条")
    print(f"用例生成方式：{format_generation_source(generation_meta)}")
    print(f"结构化测试用例已保存到：{generated_case_path}")

    print("开始执行接口测试...")
    results = run_api_tests(config, generated_cases)

    save_json(config["outputs"]["test_results"], results)
    report_path, bugs_path = generate_outputs(config, results, BASE_DIR)

    total = len(results)
    passed = len([item for item in results if item["result"] == "PASS"])
    failed = total - passed

    print(f"接口测试执行完成：共 {total} 条，通过 {passed} 条，失败 {failed} 条")
    print(f"测试结果已保存到：{config['outputs']['test_results']}")
    print(f"测试报告已保存到：{report_path}")
    print(f"Bug 单已保存到：{bugs_path}")


def format_generation_source(generation_meta):
    source = generation_meta.get("source")
    if source == "openai":
        return f"OpenAI 大模型生成（{generation_meta.get('model')} / {generation_meta.get('api')}）"

    reason = generation_meta.get("reason", "unknown")
    return f"规则生成兜底（{reason}）"


if __name__ == "__main__":
    main()

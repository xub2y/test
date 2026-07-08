import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def load_config():
    config_path = BASE_DIR / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_file(relative_path):
    file_path = BASE_DIR / relative_path
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def main():
    config = load_config()

    prd = read_file(config["docs"]["prd"])
    requirements = read_file(config["docs"]["requirements"])
    test_cases = read_file(config["docs"]["test_cases"])

    print("AI 自动化测试插件原型启动成功")
    print(f"项目名称：{config['project_name']}")
    print(f"被测服务地址：{config['base_url']}")
    print(f"PRD 文档长度：{len(prd)} 字符")
    print(f"需求文档长度：{len(requirements)} 字符")
    print(f"测试用例文档长度：{len(test_cases)} 字符")


if __name__ == "__main__":
    main()

# AI 自动化测试插件原型

## 1. 原型目标

本目录用于实现 AI 驱动的自动化测试全流程原型，验证从 PRD 解析、需求拆解、测试用例生成、接口自动化执行、测试报告生成到 Bug 单生成的完整闭环。

当前登录注册系统只是被测样例。插件本身已经改造成“PRD + 接口配置驱动”的通用原型：测试用例不再写死在执行器中，而是先由大模型或规则兜底生成结构化 JSON 用例，再由通用 API 执行器统一执行。

## 2. 核心流程

1. 读取 docs/PRD.md
2. 根据 PRD 和 config.json 中的接口信息生成结构化测试用例
3. 将测试用例保存到 generated/test_cases.json
4. 通用 API 执行器读取 JSON 用例并执行接口测试
5. 生成 outputs/test_results.json
6. 生成 outputs/test_report.md
7. 根据失败用例生成 outputs/bugs.md

用例生成优先级：

- 已配置 `OPENAI_API_KEY`：调用 OpenAI，根据 PRD 自动生成测试用例
- 未配置 Key 或调用失败：自动回退到本地规则生成，保证流程可运行

## 3. 第一版实现范围

第一版先不做复杂 UI，只实现命令行原型。

优先支持：

- 读取 PRD 文档
- 根据 PRD 生成结构化测试用例
- 通过 JSON 用例驱动接口自动化执行
- 发现用户名小于 6 位仍可注册的预埋 Bug
- 生成测试报告和 Bug 单

## 4. 运行方式

安装依赖：

```bash
cd ai-test-plugin
pip install -r requirements.txt
```

如果要启用大模型生成测试用例，先设置 OpenAI API Key：

```bash
export OPENAI_API_KEY="你的 OpenAI API Key"
```

模型默认读取 `config.json` 中的 `llm.model`，也可以临时覆盖：

```bash
export OPENAI_MODEL="gpt-5.6"
```

先启动后端服务：

```bash
cd backend
python app.py
```

后端启动后，在另一个终端运行插件：

```bash
cd ai-test-plugin
python run.py
```

如果不设置 `OPENAI_API_KEY`，也可以直接运行。此时会显示“规则生成兜底”，并继续生成用例、执行接口测试、生成报告和 Bug 单。

## 5. 当前通用化边界

当前版本已经不是只会执行写死的 Demo 用例，但仍需要在 config.json 中提供接口路径，例如注册、登录接口地址。

大模型负责从 PRD 生成测试用例；执行器仍然只认结构化 JSON 用例。这样后续更换被测系统时，主要改 PRD 和 config.json，而不是改执行器代码。

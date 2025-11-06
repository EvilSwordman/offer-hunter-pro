import os
import sys
import runpy
from pathlib import Path

try:
    from openai import OpenAI
except Exception:
    print("[ERROR] 未安装 openai，请在当前环境执行: pip install openai")
    sys.exit(1)


def main():
    # 项目根目录
    project_root = Path(__file__).resolve().parents[3]

    # 载入 LLMExtract.py，复用其中的 SYSTEM_PROMPT（保持一致）
    ns = runpy.run_path((project_root / 'plugin' / 'src' / 'cleaner' / 'LLMExtract.py').as_posix())
    system_prompt = ns.get('SYSTEM_PROMPT', '你是一个简洁专业的助手。')

    # 优先环境变量，其次 config.API_KEY
    api_key = os.getenv('DASHSCOPE_API_KEY')
    if not api_key:
        try:
            from config import API_KEY as FALLBACK_API_KEY
            api_key = FALLBACK_API_KEY
        except Exception:
            api_key = None

    if not api_key:
        print('[ERROR] 未找到 API Key，请设置环境变量 DASHSCOPE_API_KEY 或在 config.py 中填写 API_KEY')
        sys.exit(2)

    # 取一条示例输入（cleaned_面经.txt 首条非空行）
    cleaned_file = project_root / 'Data' / 'cleaned' / 'cleaned_面经.txt'
    if cleaned_file.exists():
        with open(cleaned_file, 'r', encoding='utf-8') as f:
            sample = next((l.strip() for l in f if l.strip()), '示例：我在XX公司面了前端岗...')
    else:
        sample = '示例：我在XX公司面了前端岗...'

    client = OpenAI(
        api_key=api_key,
        base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
    )

    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': sample},
    ]

    try:
        resp = client.chat.completions.create(model='qwen-plus', messages=messages)
        print('[LLM RESPONSE]', resp.choices[0].message.content)
        print('[SUCCESS] 测试调用成功')
    except Exception as e:
        print('[FAILED] 调用失败:', repr(e))
        sys.exit(3)


if __name__ == '__main__':
    main()



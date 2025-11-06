import os
from openai import OpenAI
from config import API_KEY
from pathlib import Path


SYSTEM_PROMPT = """任务：对输入文本进行信息提取与分类。

分类：
- 面试经验分享
- 求助问答

抽取规则（若缺失则不输出该字段）：
- 面试经验分享：公司、岗位、薪资与福利、评价
- 求助问答：公司、岗位、薪资、问题

多公司文本：按公司粒度拆分为多条记录。

输出要求：
- 必须使用简体中文
- 严格输出为 JSON Lines（每行一个 JSON 对象）
- 字段：{"type":"...","company":"...","role":"...","salary_benefits":"...","review_or_question":"..."}
  - 当 type=面试经验分享：review_or_question 填“评价”内容
  - 当 type=求助问答：review_or_question 填“问题”内容
- 不要添加解释、前后缀、代码块或额外字符
- 保持内容精炼，避免复述无关信息
"""

_CLIENT = None


def _get_client(api_key: str) -> OpenAI:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    return _CLIENT


def call_with_messages(api_key, prompt):
    client = _get_client(api_key)

    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': prompt}
    ]

    completion = client.chat.completions.create(
        model="qwen-plus",
        messages=messages,
    )
    return completion.choices[0].message.content

def read_text_from_file(file_path):
    lines = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            lines.append(line.strip())
    return lines

def save_responses_to_file(api_key, input_texts, output_file_path):
    output_path = Path(output_file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        wrote_any = False
        for text in input_texts:
            try:
                response = call_with_messages(api_key, text)
            except Exception:
                response = ''
            if response:
                f.write(response + '\n')
                wrote_any = True
        f.flush()
    return output_path.as_posix()

if __name__ == "__main__":
    api_key = API_KEY

    # 解析项目根目录
    project_root = Path(__file__).resolve().parents[3]
    cleaned_dir = project_root / "Data" / "cleaned"
    output_dir = project_root / "Data" / "LLM_extract"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 仅处理“面经”文件
    input_file = cleaned_dir / "cleaned_面经.txt"
    if not input_file.exists():
        raise FileNotFoundError(f"未找到输入文件: {input_file}")

    input_texts = read_text_from_file(input_file.as_posix())
    output_file_path = output_dir / "extracted_面经.txt"

    print(f"Processing {input_file} -> {output_file_path}")
    final_path = save_responses_to_file(api_key, input_texts, output_file_path.as_posix())
    print(f"Saved to {final_path}")

    # # 依次处理 cleaned 目录下的文件
    # for input_file in sorted(cleaned_dir.glob("cleaned_*.txt")):
    #     input_texts = read_text_from_file(input_file.as_posix())
    #     # 输出文件名以 extracted_ 为前缀，去掉原有的 cleaned_ 前缀
    #     base_name = input_file.name
    #     if base_name.startswith("cleaned_"):
    #         base_name = base_name[len("cleaned_"):]
    #     output_file_path = output_dir / ("extracted_" + base_name)

    #     print(f"Processing {input_file} -> {output_file_path}")
    #     save_responses_to_file(api_key, input_texts, output_file_path.as_posix())
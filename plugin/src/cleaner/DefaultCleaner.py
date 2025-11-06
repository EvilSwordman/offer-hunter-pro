import re
import time
import emoji
from pathlib import Path

def process_files(input_files, output_prefix):
    for file_path in input_files:
        result = []
        now = time.strftime("%Y-%m-%d", time.localtime())
        file_name = f"{file_path}_{now}.txt"
        # Input directory Data/origin under project root
        project_root = Path(__file__).resolve().parents[3]
        origin_dir = project_root / 'Data' / 'origin'
        input_file_path = origin_dir / file_name
        with open(input_file_path.as_posix(), 'r', encoding='utf-8') as file:
            lines = file.readlines()
            i = 0
            while i < len(lines):
                if lines[i].startswith('Full Post Text:'):
                    full_post_text = clean_text(lines[i].split('Full Post Text: ')[1].strip())
                    if full_post_text:
                        result.append(full_post_text)
                i += 1
        # Ensure output directory Data/cleaned exists under project root
        cleaned_dir = project_root / 'Data' / 'cleaned'
        cleaned_dir.mkdir(parents=True, exist_ok=True)
        output_file_name = cleaned_dir / (output_prefix + file_path + '.txt')
        with open(output_file_name.as_posix(), 'w', encoding='utf-8') as output_file:
            for text in result:
                output_file.write(text + '\n')


def clean_text(text):
    if text != "No post content available":
        # Use regular expressions to remove links and labels.
        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'#\S+#', '', text)
        # 移除emoji
        text = remove_emojis(text)
        # 移除特殊字符
        # text = re.sub(r'[^\w\s]', '', text)
        # 去掉多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    return None

def remove_emojis(text):
    return emoji.demojize(text).replace(':', '')

if __name__ == "__main__":
    file_path = ["秋招", "校招", "面经", "算法工程师","Java后端开发","前端开发","硬件开发","软件开发"]   #input filename
    output_prefix = 'cleaned_'   #output filename
    process_files(file_path, output_prefix)

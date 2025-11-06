import requests
import time
import random
import re
import json
from bs4 import BeautifulSoup
import datetime
from itertools import product
from pathlib import Path

class BossSpiderAPI:
    def __init__(self, cookie, keywords, cities, experience_str, scale_str, max_pages=2):
        # 清理 Cookie 字符串：移除换行符和多余空白字符，保留分号后的空格
        clean_cookie = re.sub(r'\s+', ' ', cookie.strip())
        self.base_url = "https://www.zhipin.com/wapi/zpgeek/search/joblist.json"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "Referer": "https://www.zhipin.com/",
            "Cookie": clean_cookie
        }
        self.detail_headers = {
            "User-Agent": self.headers["User-Agent"],
            "Cookie": self.headers["Cookie"]
        }
        self.keywords = keywords
        self.cities = cities
        self.experience_str = experience_str   # 如 '106,107'
        self.scale_str = scale_str             # 如 '303,305,308'
        self.max_pages = max_pages
        self.data_list = []

    def fetch_data(self, keyword, city):
        print(f"\n正在抓取：关键词[{keyword}] 城市[{city}] 经验[{self.experience_str}] 规模[{self.scale_str}]")
        for page in range(1, self.max_pages + 1):
            params = {
                "scene": "1",
                "query": keyword,
                "city": city,
                "experience": self.experience_str,
                "scale": self.scale_str,
                "page": page,
                "pageSize": 30
            }
            try:
                resp = requests.get(self.base_url, headers=self.headers, params=params, timeout=10)
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"请求失败：{e}")
                continue

            result = resp.json()
            job_list = result.get("zpData", {}).get("jobList", [])
            if not job_list:
                print("没有更多数据了")
                break

            for job in job_list:
                job_id = job.get("encryptJobId")
                job_desc = self.get_job_detail(job_id)
                item = {
                    "职位": job.get("jobName"),
                    "公司": job.get("brandName"),
                    "薪资": job.get("salaryDesc"),
                    "地区": job.get("cityName"),
                    "经验要求": job.get("jobExperience"),
                    "学历要求": job.get("jobDegree"),
                    "公司规模": job.get("brandScaleName"),
                    "行业": job.get("brandIndustry"),
                    "福利标签": ",".join(job.get("welfareList", [])),
                    "技能标签": ",".join(job.get("skills", [])),
                    "职位链接": f"https://www.zhipin.com/job_detail/{job_id}.html",
                    "职位描述": job_desc
                }
                self.data_list.append(item)
                time.sleep(random.uniform(0.5, 1.1))  # 防风控

    def get_job_detail(self, job_id):
        url = f"https://www.zhipin.com/job_detail/{job_id}.html"
        try:
            resp = requests.get(url, headers=self.detail_headers, timeout=8)
            if resp.status_code != 200:
                return ""
            soup = BeautifulSoup(resp.text, 'html.parser')
            desc_tag = soup.select_one('.job-sec-text')
            return desc_tag.text.strip() if desc_tag else ""
        except Exception as e:
            print(f"详情页获取失败: {e}")
            return ""

    def save_json(self):
        # 计算项目根目录（从 plugin/src/spiders/boss_spider.py 向上3层）
        project_root = Path(__file__).resolve().parents[3]
        boss_dir = project_root / 'Data' / 'boss'
        boss_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"Boss直聘_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = boss_dir / filename
        
        # 保存为 JSON 格式，确保中文正确编码
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data_list, f, ensure_ascii=False, indent=2)
        
        print(f"\n保存成功：{file_path}，共 {len(self.data_list)} 条职位")

    def run(self):
        combos = list(product(self.keywords, self.cities))
        total = len(combos)
        print(f"总共请求组合数：{total}")
        for i, (keyword, city) in enumerate(combos, 1):
            print(f"\n==> 第 {i}/{total} 组")
            self.fetch_data(keyword, city)
        self.save_json()

if __name__ == "__main__":
    my_cookie = "Hm_lvt_194df3105ad7148dcf2b98a91b5e727a=1760773271; __zp_seo_uuid__=382fd051-a278-41d6-8adf-f1a720e4bd7a; __g=-; __l=r=https%3A%2F%2Fwww.bing.com%2F&l=%2Fwww.zhipin.com%2Fweb%2Fgeek%2Fjobs&s=3&g=&friend_source=0&s=3&friend_source=0; wt2=DvKGiEgbxH1rBlOyUbhaAwvXj0rQJqVdeQFm6WbyBXfHX4J3OoGshSmBhic_ZOX3u9tPmTUGi2p67rE3Iflj1VA~~; wbg=0; zp_at=L3r1IclW-Q2v6BIqQSkD6vYultN6vqDwir2LgV1BiI0~; __zp_stoken__=2d9ffw4nDncKYBz4OVnZRCGxbwrPCs394U0jDilVEZE1WV8Kkc8KUW1tQVsK8VGzCsMKmwrppRUvDu8OAwpfCp8O2esKZwr%2FCi8KcwpRbwpLEnMOvecOQwprCpsKywpY4JAICDAMPBQUDDAgJCQYJBQcHAQ4aCAgGCQU7I8O%2BwoE8PDU8IVpHRw5NV1FCV0ENW09LMztYBxADOyfCssKZMz8ywrXDvsOKIMK1xIDCvcKvwrjEgMK7wogzNzIywr3Dqi4tQhDCuFkOwrkSBysOwrLCrQfDj1EzwqnCtcK5cSYyOMKyNTkeOTw5Nz84Nzk5LjXCv8Kvw4JXMsKiwrzCvGEoPxkxPzgxOzk%2FODM5Nys4NyovPzMvNQkDBwgFLDbCt8KOwrLDkz84; Hm_lpvt_194df3105ad7148dcf2b98a91b5e727a=1762365315; HMACCOUNT=06EA8C4822E53994; bst=V2RtkkFOz43lpoVtRuyR4aKiiy7DrVxSw~|RtkkFOz43lpoVtRuyR4aKiiy7DrRwyo~; __c=1760773272; __a=48701850.1755272243.1758633026.1760773272.34.4.26.34"        
    
    # keywords = ["算法工程师", "Java后端工程师", "前端开发", "产品经理"]
    keywords = ["Java后端开发工程师"]
    # cities = ["101010100", "101020100", "101030100", "101040100"] #北京，上海，杭州，深圳 
    cities = ["101220100"] 
    experience_str = "106"  
    scale_str = "303,304,305"

    # 5. 每组爬几页
    max_pages = 1

    spider = BossSpiderAPI(
        cookie=my_cookie,
        keywords=keywords,
        cities=cities,
        experience_str=experience_str,
        scale_str=scale_str,
        max_pages=max_pages
    )
    spider.run()



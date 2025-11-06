import datetime
import re
import time
import json
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ================ 推荐复用chrome已登录窗口，免风控 ================
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
browser = webdriver.Chrome(options=chrome_options)  # 如未用调试端口也可直接webdriver.Chrome()

rows = []


# 具体岗位的URL列表
category_urls = [
    'https://www.zhipin.com/web/geek/jobs?query=&city=100010000&position=100101',  
    'https://www.zhipin.com/web/geek/jobs?query=&city=100010000&position=100901',  
    'https://www.zhipin.com/web/geek/jobs?query=&city=100010000&position=101310',
    'https://www.zhipin.com/web/geek/jobs?query=&city=100010000&position=110101'
]

today = datetime.date.today().strftime('%Y-%m-%d')

for category_url in category_urls:
    try:
        print(f"{today}正在抓取: {category_url}")
        
        # 直接访问小类URL
        browser.get(category_url)
        
        # 等待页面加载
        WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)
        
        # 检查是否有安全验证
        page_source = browser.page_source
        if "安全验证" in page_source or "验证身份" in browser.title or "滑动完成验证" in page_source:
            print(f"检测到风控页面/安全验证，跳过: {category_url}")
            continue
        
        # 等待职位列表加载
        time.sleep(3)
        
        # 尝试多种选择器查找职位卡片
        job_detail = []
        selectors = [
            'li.job-card-box',
        ]
        for selector in selectors:
            try:
                job_detail = WebDriverWait(browser, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
                if job_detail and len(job_detail) > 0:
                    print(f"共找到{len(job_detail)}个职位卡片（选择器: {selector}）")
                    break
            except:
                continue
        
        # 如果WebDriverWait没找到，再尝试直接查找
        if not job_detail:
            time.sleep(2)
            for selector in selectors:
                try:
                    job_detail = browser.find_elements(By.CSS_SELECTOR, selector)
                    if job_detail and len(job_detail) > 0:
                        print(f"共找到{len(job_detail)}个职位卡片（选择器: {selector}）")
                        break
                except:
                    continue
        
        if not job_detail:
            print(f"警告：未找到职位列表元素，URL: {category_url}")
            continue

        for idx, job in enumerate(job_detail):
            # 职位名称
            try:
                job_title = job.find_element(By.CSS_SELECTOR, "a.job-name").text.strip()
            except: job_title = ""
           
            # 公司
            try:
                job_company = job.find_element(By.CSS_SELECTOR, "span.boss-name").text.strip()
            except: job_company = ""
            # 地址
            try:
                job_location = job.find_element(By.CSS_SELECTOR, "span.company-location").text.strip()
            except: job_location = ""
            # 工作年限/学历
            tag_list = job.find_elements(By.CSS_SELECTOR, ".tag-list li")
            job_experience = tag_list[0].text.strip() if len(tag_list)>0 else ""
            job_education = tag_list[1].text.strip() if len(tag_list)>1 else ""
            # 其他字段
            job_industry = ""
            job_finance = ""
            job_scale = ""
            job_skills = "无"
            # 链接
            try:
                job_link = job.find_element(By.CSS_SELECTOR, "a.job-name").get_attribute("href")
            except: job_link = ""

            # 职业描述（详情页）：
            job_desc = ''
            if job_link:
                try:
                    current_handle = browser.current_window_handle
                    browser.execute_script("window.open(arguments[0])", job_link)
                    time.sleep(2)
                    for h in browser.window_handles:
                        if h != current_handle:
                            browser.switch_to.window(h)
                            break
                    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    time.sleep(1)
                    
                    # 提取职位描述
                    try:
                        desc_elem = browser.find_element(By.CSS_SELECTOR, '.job-sec-text')
                        job_desc = desc_elem.text.strip()
                    except:
                        job_desc = ""
                    # 详情页兜底提取薪资（列表页常见字符混淆）
                    try:
                        needs_fix = (not job_salary_range) or any(ch in job_salary_range for ch in ['\uf0f2', '', '', '', '', '', '', '', ''])
                    except:
                        needs_fix = True
                    if needs_fix:
                        # 1) 详情页头部薪资
                        try:
                            header_salary = browser.find_element(By.CSS_SELECTOR, '.job-primary .name .salary').text.strip()
                            if header_salary:
                                job_salary_range = header_salary
                        except:
                            pass
                        # 2) window._jobInfo.job_salary
                        if not job_salary_range:
                            try:
                                js_salary = browser.execute_script('return window._jobInfo && window._jobInfo.job_salary ? window._jobInfo.job_salary : null;')
                                if js_salary:
                                    job_salary_range = str(js_salary).strip()
                            except:
                                pass
                        # 3) 从 page_source 正则提取 job_salary: 'xxx'
                        if not job_salary_range:
                            try:
                                html = browser.page_source
                                import re as _re
                                m = _re.search(r"job_salary\s*:\s*'([^']+)'", html)
                                if m:
                                    job_salary_range = m.group(1).strip()
                            except:
                                pass
                    
                    # 提取行业类型、融资情况、企业规模（从侧边栏公司信息）
                    # 行业类型 - 在 <p><i class="icon-industry"></i><a>人工智能</a></p> 中
                    try:
                        industry_elem = browser.find_element(By.XPATH, '//div[@class="sider-company"]//p[.//i[contains(@class, "icon-industry")]]//a')
                        job_industry = industry_elem.text.strip()
                    except:
                        try:
                            # 备用方式：直接查找包含industry的p标签下的a标签
                            industry_elem = browser.find_element(By.XPATH, '//div[@class="sider-company"]//p[contains(.//i/@class, "icon-industry")]/a')
                            job_industry = industry_elem.text.strip()
                        except:
                            job_industry = ""
                    
                    # 融资情况 - 在 <p><i class="icon-stage"></i>C轮</p> 中
                    try:
                        finance_p = browser.find_element(By.XPATH, '//div[@class="sider-company"]//p[.//i[contains(@class, "icon-stage")]]')
                        finance_text = finance_p.text.strip()
                        # 去掉可能的图标字符，只保留融资信息（去掉i标签内的文本）
                        job_finance = finance_text
                    except:
                        try:
                            # 备用方式：查找包含stage的p标签
                            finance_p = browser.find_element(By.XPATH, '//div[@class="sider-company"]//p[contains(.//i/@class, "icon-stage")]')
                            finance_text = finance_p.text.strip()
                            job_finance = finance_text
                        except:
                            job_finance = ""
                    
                    # 企业规模 - 在 <p><i class="icon-scale"></i>10000人以上</p> 中
                    try:
                        scale_p = browser.find_element(By.XPATH, '//div[@class="sider-company"]//p[.//i[contains(@class, "icon-scale")]]')
                        scale_text = scale_p.text.strip()
                        job_scale = scale_text
                    except:
                        try:
                            # 备用方式：查找包含scale的p标签
                            scale_p = browser.find_element(By.XPATH, '//div[@class="sider-company"]//p[contains(.//i/@class, "icon-scale")]')
                            scale_text = scale_p.text.strip()
                            job_scale = scale_text
                        except:
                            job_scale = ""
                    
                    browser.close()
                    browser.switch_to.window(current_handle)
                except Exception as e:
                    print(f"提取详情页信息失败: {e}")
                    job_desc = ""
                    try:
                        browser.switch_to.window(current_handle)
                    except:
                        pass

            if job_location:
                city = job_location.split('·')[0] if '·' in job_location else job_location
            print(job_title, job_location, job_company, job_industry, job_finance, job_scale, job_salary_range, job_experience, job_education, job_link)   
            rows.append({
                '岗位名称': job_title,
                '工作地址': job_location,
                '企业名称': job_company,
                '行业类型': job_industry,
                '融资情况': job_finance,
                '企业规模': job_scale,
                '薪资范围': job_salary_range,
                '工作年限': job_experience,
                '学历要求': job_education,
                '职业描述': job_desc,
                '链接': job_link,
            })
    except Exception as e:
        print(f"采集错误: {e}")
        continue

project_root = Path(__file__).resolve().parents[4]
boss_dir = project_root / 'Data' / 'boss'
boss_dir.mkdir(parents=True, exist_ok=True)
filename = f"Boss直聘_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
out_path = boss_dir / filename

if rows:
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"已写入: {out_path}，共 {len(rows)} 条职位")
else:
    print("未采集到数据.")

try: browser.quit()
except: pass
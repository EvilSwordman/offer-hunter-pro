# offer-hunter-pro
This project continues the logic of offer-hunter, fixes the Boss spider functionality, and will later implement a LLM job finding assistant based on Coze.

## spider
We implemented crawlers for boss, maimai, and niuke. The files are in the directory `plugin/src/spiders`.
Firstly you need to install dependencies:
```bash
pip install -r requirements.txt
```
Then run spiders to get the origin data:
```bash
python CrawlData.py
python  BossSelenium.py
```
       
## Data Clean and Extract
Posts crawled from maimai and niuke need to be data cleaned.We first clean the original data and then use LLM to extract information `plugin/src/cleaner` :
```bash 
sh run.sh
```
For large models, we use the Alibaba Cloud Bailian platform, and you need to get api_key on this platform, then configure the api_key in `config.py`.
All data is under 'Data', the prepared data is then restored to `boss` and `LLM_extract`.

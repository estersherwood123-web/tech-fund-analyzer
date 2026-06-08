# -*- coding: utf-8 -*-
import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
import logging
import json
import re

logger = logging.getLogger(__name__)

class TianTianFundCrawler:
    """天天基金爬虫"""
    
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.base_url = 'https://fundmobapi.eastmoney.com'
    
    def get_realtime_nav(self, fund_code):
        """获取基金实时净值"""
        try:
            url = f'http://fundgz.1234567.com.cn/js/fundgz_{fund_code}.js'
            response = self.session.get(url, headers=self.headers, timeout=10, verify=False)
            response.encoding = 'gb2312'
            
            data_str = response.text
            if 'jsonpgz' in data_str:
                match = re.search(r'jsonpgz\((.*?)\)', data_str)
                if match:
                    data = json.loads(match.group(1))
                    return {
                        'code': fund_code,
                        'name': data.get('name'),
                        'current_nav': float(data.get('lastclose', 0)),
                        'yesterday_nav': float(data.get('lastyearend', 0)),
                        'change_rate': float(data.get('rate', 0)),
                        'update_time': data.get('time'),
                        'fetch_time': datetime.now().isoformat()
                    }
        except Exception as e:
            logger.error(f"获取 {fund_code} 实时净值失败: {str(e)}")
        
        return None
    
    def get_quote_history(self, fund_code, days=100):
        """获取基金历史净值"""
        try:
            data = {
                'FCODE': fund_code,
                'pageIndex': '1',
                'pageSize': str(days),
                'appType': 'ttjj',
                'version': '6.2.8',
            }
            
            url = f'{self.base_url}/FundMNewApi/FundMNHisNetList'
            response = self.session.get(
                url, 
                params=data, 
                headers=self.headers, 
                timeout=10,
                verify=False
            )
            
            json_data = response.json()
            if json_data.get('Datas'):
                rows = []
                for item in json_data['Datas']:
                    rows.append({
                        'date': item.get('FSRQ'),
                        'nav': float(item.get('DWJZ', 0) or 0),
                        'cumulative_nav': float(item.get('LJJZ', 0) or 0),
                        'change_rate': float(item.get('JZZZL', 0) or 0)
                    })
                df = pd.DataFrame(rows)
                return df
        except Exception as e:
            logger.error(f"获取 {fund_code} 历史数据失败: {str(e)}")
        
        return pd.DataFrame()
    
    def get_invest_position(self, fund_code):
        """获取基金持仓信息"""
        try:
            url = f'http://fundf10.eastmoney.com/jjcc_{fund_code}.html'
            response = self.session.get(url, headers=self.headers, timeout=10, verify=False)
            response.encoding = 'gb2312'
            
            position_data = {
                'fund_code': fund_code,
                'fetch_time': datetime.now().isoformat(),
                'holdings': []
            }
            
            return position_data
        except Exception as e:
            logger.error(f"获取 {fund_code} 持仓失败: {str(e)}")
        
        return {}
    
    def get_fund_manager(self, fund_code):
        """获取基金经理信息"""
        try:
            url = f'http://fundf10.eastmoney.com/jjjl_{fund_code}.html'
            response = self.session.get(url, headers=self.headers, timeout=10, verify=False)
            response.encoding = 'gb2312'
            
            manager_info = {
                'fund_code': fund_code,
                'managers': []
            }
            
            return manager_info
        except Exception as e:
            logger.error(f"获取 {fund_code} 经理信息失败: {str(e)}")
        
        return {}

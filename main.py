# -*- coding: utf-8 -*-
import logging
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from src.crawlers.tiantian_fund_crawler import TianTianFundCrawler
from src.crawlers.sina_finance_crawler import SinaFinanceCrawler
from src.crawlers.eastmoney_crawler import EastMoneyCrawler
from src.crawlers.finance_news_crawler import FinanceNewsCrawler
from src.data_processing.data_cleaner import DataCleaner
from src.data_processing.database_manager import DatabaseManager
from src.sentiment_analysis.sentiment_analyzer import SentimentAnalyzer
from src.prediction.rule_engine import RuleEngine
from src.prediction.trend_predictor import TrendPredictor
from src.report_generation.report_generator import ReportGenerator
from config.config import MY_FUNDS, SCHEDULER_CONFIG, LOGGING_CONFIG

# 创建日志目录
os.makedirs('logs', exist_ok=True)
os.makedirs('output/reports', exist_ok=True)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format=LOGGING_CONFIG['format'],
    handlers=[
        logging.FileHandler(LOGGING_CONFIG['log_file']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TechFundAnalyzer:
    """科技基金分析系统主类"""
    
    def __init__(self):
        logger.info("正在初始化系统...")
        try:
            self.db_manager = DatabaseManager()
            self.crawlers = self._init_crawlers()
            self.sentiment_analyzer = SentimentAnalyzer()
            self.rule_engine = RuleEngine()
            self.trend_predictor = TrendPredictor()
            self.report_generator = ReportGenerator()
            logger.info("✅ 系统初始化成功")
        except Exception as e:
            logger.error(f"❌ 系统初始化失败: {str(e)}", exc_info=True)
            raise
    
    def _init_crawlers(self):
        """初始化所有爬虫"""
        logger.info("正在初始化爬虫模块...")
        return {
            'tiantian': TianTianFundCrawler(),
            'sina': SinaFinanceCrawler(),
            'eastmoney': EastMoneyCrawler(),
            'news': FinanceNewsCrawler()
        }
    
    def run_analysis(self):
        """执行完整分析流程"""
        logger.info("=" * 80)
        logger.info(f"【开始执行分析流程】 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        
        try:
            # 第 1 步：数据采集
            logger.info("\n【第1步】数据采集...")
            fund_data = self._fetch_fund_data()
            news_data = self._fetch_news_data()
            
            if not fund_data:
                logger.warning("❌ 无法采集基金数据，中止分析")
                return
            
            # 第 2 步：数据清洗
            logger.info("\n【第2步】数据清洗...")
            cleaner = DataCleaner()
            fund_data = cleaner.clean_fund_data(fund_data)
            news_data = cleaner.clean_news_data(news_data)
            logger.info(f"✅ 清洗完成: {len(fund_data)} 个基金, {sum(len(v) for v in news_data.values())} 条新闻")
            
            # 第 3 步：数据存储
            logger.info("\n【第3步】数据存储...")
            self.db_manager.save_fund_data(fund_data)
            self.db_manager.save_news_data(news_data)
            logger.info("✅ 数据已保存到数据库")
            
            # 第 4 步：舆情分析
            logger.info("\n【第4步】舆情分析...")
            sentiment_results = self.sentiment_analyzer.analyze(news_data)
            self.db_manager.save_sentiment_data(sentiment_results)
            logger.info("✅ 舆情分析完成")
            
            # 第 5 步：规则引擎
            logger.info("\n【第5步】规则引擎评分...")
            rule_scores = self.rule_engine.evaluate(fund_data, sentiment_results)
            logger.info("✅ 规则评分完成")
            
            # 第 6 步：趋势预测
            logger.info("\n【第6步】趋势预测...")
            predictions = self.trend_predictor.predict(fund_data, rule_scores)
            self.db_manager.save_predictions(predictions)
            logger.info("✅ 趋势预测完成")
            
            # 第 7 步：生成报告
            logger.info("\n【第7步】生成报告...")
            report = self.report_generator.generate_daily_report(
                fund_data, 
                sentiment_results, 
                rule_scores, 
                predictions
            )
            
            # 第 8 步：输出结果
            logger.info("\n【第8步】输出结果...")
            self._output_results(report)
            
            logger.info("\n" + "=" * 80)
            logger.info("✅ 【分析完成！】")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ 分析出错: {str(e)}", exc_info=True)
    
    def _fetch_fund_data(self):
        """采集基金数据"""
        all_data = {}
        for fund in MY_FUNDS:
            code = fund['code']
            logger.info(f"  爬取基金 {code} - {fund['name']}...")
            
            try:
                nav_data = self.crawlers['tiantian'].get_realtime_nav(code)
                history_data = self.crawlers['tiantian'].get_quote_history(code)
                position_data = self.crawlers['tiantian'].get_invest_position(code)
                manager_data = self.crawlers['tiantian'].get_fund_manager(code)
                
                if nav_data:
                    all_data[code] = {
                        'nav': nav_data,
                        'history': history_data,
                        'position': position_data,
                        'manager': manager_data,
                        'meta': fund
                    }
                    logger.info(f"    ✅ {code} 采集成功")
                else:
                    logger.warning(f"    ⚠️ {code} 采集失败")
            except Exception as e:
                logger.error(f"    ❌ 爬取 {code} 失败: {str(e)}")
        
        return all_data
    
    def _fetch_news_data(self):
        """采集新闻数据"""
        logger.info("  爬取新闻数据...")
        all_news = {}
        
        try:
            logger.info("    获取新浪财经新闻...")
            sina_news = self.crawlers['sina'].get_tech_news()
            if sina_news:
                all_news['sina'] = sina_news
                logger.info(f"    ✅ 获取 {len(sina_news)} 条新浪新闻")
            
            logger.info("    获取东方财富新闻...")
            em_news = self.crawlers['eastmoney'].get_tech_news()
            if em_news:
                all_news['eastmoney'] = em_news
                logger.info(f"    ✅ 获取 {len(em_news)} 条东方财富新闻")
            
            logger.info("    获取其他财经新闻...")
            other_news = self.crawlers['news'].crawl_all_sources()
            if other_news:
                all_news['other'] = other_news
                logger.info(f"    ✅ 获取 {len(other_news)} 条其他新闻")
            
        except Exception as e:
            logger.error(f"  ❌ 爬取新闻失败: {str(e)}")
        
        return all_news
    
    def _output_results(self, report):
        """输出结果"""
        report_path = self.report_generator.save_report(report)
        logger.info(f"📄 报告已保存: {report_path}")
        
        print("\n" + "=" * 80)
        print(report['summary'])
        print("\n【你的基金预测】")
        for fund_info in report['funds']:
            code = fund_info['code']
            name = fund_info['name']
            pred = fund_info['prediction']
            tomorrow = pred['tomorrow']
            scores = pred['rule_scores']
            
            print(f"\n{code} - {name}")
            print(f"  ├─ 明天预测: {tomorrow['direction']} ({tomorrow['estimate_change']}) | 置信度: {tomorrow['confidence']}%")
            print(f"  └─ 评分: 利好 {scores['good_news']:.0%} | 中立 {scores['neutral']:.0%} | 利空 {scores['bad_news']:.0%}")
        
        print("\n" + "=" * 80)

def schedule_analysis():
    """配置定时任务"""
    scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
    
    run_time = SCHEDULER_CONFIG['run_time']
    hour, minute = map(int, run_time.split(':'))
    
    scheduler.add_job(
        analyzer.run_analysis,
        'cron',
        hour=hour,
        minute=minute,
        id='daily_analysis',
        name='每日基金分析'
    )
    
    scheduler.start()
    logger.info(f"✅ 定时任务已启动，每天 {run_time} 自动执行")
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()
        logger.info("❌ 定时任务已停止")

if __name__ == '__main__':
    analyzer = TechFundAnalyzer()
    
    # ===== 测试模式：立即运行一次 =====
    logger.info("🚀 启动系统...")
    analyzer.run_analysis()
    
    # ===== 生产模式：启动定时任务 =====
    # 取消下面的注释以启用定时任务
    # schedule_analysis()

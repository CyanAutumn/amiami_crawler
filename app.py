import os
import time
import requests
from utils.driver import webDriver
from utils import database
from utils import flogger
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from apscheduler.schedulers.background import BackgroundScheduler

log = flogger.Flogger().get_logger(__name__)


def thread_download_image():
    while True:
        try:
            task = database.get_download_task()
            if task is None:
                time.sleep(3)
                continue
            log.info(task.url)
            response = requests.get(task.url)
            if response.status_code == 200:
                with open(f"./temp/{task.file_name}", "wb") as file:
                    file.write(response.content)
                database.del_download_task(task)
        except:
            pass


if __name__ == "__main__":
    # 初始化参数和下载进程
    database.init()
    last_page = database.get_last_page()
    scheduler = BackgroundScheduler()
    for i in range(3):  # 对应开启的下载进程数量，如果太频繁会导致服务器拒绝响应
        scheduler.add_job(thread_download_image, "date", next_run_time=datetime.now())
    scheduler.start()

    # 单纯让下载进程下载完数据库里的下载任务
    # while True:
    #     pass
    # 开始抓取
    with webDriver() as driver:
        driver.get(
            f"https://www.amiami.com/cn/search/list/?s_cate2=459&pagecnt={last_page}&s_sortkey=releasedated"
        )  # 默认按照发布日期进行排序

        while (
            next_page := driver.wait_element_by_xpath(
                '//*[@id="__layout"]/div/div[1]/div[2]/div/div/div/div/div[2]/div[4]/p[2]/a[2]'
            )
        ) is not None:
            log.info(f"最后一次抓取的页面{last_page}")
            # 检查商品url
            for ele_commodity_button in driver.wait_elements_by_xpath(
                '//ul/li[@class="newly-added-items__item nomore"]/a'
            ):
                url = ele_commodity_button.get_property("href")
                commodity_key = url.split("=")[-1]
                if database.check_commodity_key(commodity_key):
                    log.info("商品已被抓取")
                    continue

                # 图片页
                driver.execute_script(f'window.open("{url}", "_blank");')
                time.sleep(3)
                driver.switch_to.window(driver.window_handles[1])
                if (
                    ele_btn_show_all_pic := driver.wait_element_by_xpath(
                        '//*[@id="__layout"]/div/div[1]/div[2]/div/div/div/div/div/section[1]/div/div[2]/div[2]/p/a'
                    )
                ) is not None:
                    ele_btn_show_all_pic.click()
                    for ele_image in driver.wait_elements_by_xpath(
                        '//*[@id="__layout"]/div/div[1]/div[2]/div/div/section/ul/li/img'
                    ):
                        url = ele_image.get_property("src")
                        name = url.split("/")[-1]
                        database.add_commodity_url(url, name)
                database.set_commodity_key(commodity_key)
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            last_page += 1
            database.set_last_page(last_page)
            next_page.click()

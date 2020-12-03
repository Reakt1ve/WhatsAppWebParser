# -*- coding:utf-8 -*-
import time
import requests
import sys
import wmi
import logging

from sys import exit
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

import warnings

warnings.filterwarnings("ignore")

class Whatsapp():
    def __init__(self, driver, config, logger):
        self.driver = driver
        self.config = config
        self.wait = WebDriverWait(self.driver, 60)
        self.previous_message = ''  # позже нам это пригодится
        self.previous_name = ''
        self.last_text = ''
        self.logger = logger

    def login(self):
        self.logger.info(config.get('Settings', 'open_window'))
        self.logger.info(f'Запуск бота...')
        net_connection(
                        lambda: self.driver.get('https://web.whatsapp.com'),
                        self.logger,
                        verbose="yes"
                       )
        self.logger.info(config.get('Settings', 'scan_qr'))
        input()
        self.logger.info(config.get("Settings", "logged_in"))

    def parse(self):
        """
        Запись всех сообщений беседы в .txt файл
        Кроме пересланных сообщений
        :return:
        """

        self.logger.info(config.get('Settings', "target_contact"))
        input()
        target = self.driver.find_element_by_class_name("YEe1t").text

        # config
        path_to_txt = self.config.get('Settings', 'PATH_TXT_RESULT')
        file = open(path_to_txt, 'w', encoding='utf-8')
        file.write(f'{config.get("Settings", "messages_from")} "{target}":' + '\n')
        file.close()

        # загрузить все сообщения беседы (ленты)
        html = self.driver.find_element_by_tag_name(
            'html')

        self.logger.info(f'Сканируемый пользователь: {target}')
        self.logger.info(f'Получение диалога...')
        
        try:
            select_chat = self.driver.find_element_by_class_name("tSmQ1").click()
        except Exception:
            chat = self.driver.find_elements_by_css_selector('span.selectable-text')
            select_chat = chat[len(chat) - 1].click()

        a = 0
        time_start = time.time()
        #получение сейчас времени
        # 15 сек
        while a != 1 and time.time() - time_start < 15:
            try:
                
                # self.driver.find_element_by_xpath("//span[@data-testid='lock-small']").is_displayed()
                var = self.driver.find_element_by_xpath(
                    "//span[@data-testid='lock-small']").location_once_scrolled_into_view
                a = 1
            except NoSuchElementException:
                html.send_keys(Keys.HOME)

        higher_class = self.driver.find_elements_by_class_name("_1dB-m")
        i = 0
        companion_diag = list()
        self.logger.info(f'Обработка полученной информации...')
        
        while i <= len(higher_class) - 1:
            try:
                condition = target + ': '
                meta_block = higher_class[i].find_element_by_css_selector('div.copyable-text')
                author = self.format_meta_block(meta_block)
                if author == condition:
                    companion_diag.append(higher_class[i])
                    
            except NoSuchElementException:
                pass
            finally:
                i += 1
    
        # Удаляем пересланные сообщения
        # G1sHr - сообщение удалено
        # _1FXrP - пересылаемое сообщение
        # _3fs13 - редирект в одном чате
        i = 0
        while i < len(companion_diag):
            if len(companion_diag[i].find_elements_by_css_selector('div._3fs13')) == 1 or \
                len(companion_diag[i].find_elements_by_css_selector('div._1FXrP')) == 1 or \
                len(companion_diag[i].find_elements_by_css_selector('div.G1sHr')) == 1:
                    del companion_diag[i]
            else:
                i += 1

        # Удаляем время отправления сообщения
        all_messages_only_text = list()
        for i in range(len(companion_diag)):
            if companion_diag[i].text.rfind("\n1") != -1:
                all_messages_only_text.append(companion_diag[i].text.split("\n1")[0])
            elif companion_diag[i].text.rfind("\n2") != -1:
                all_messages_only_text.append(companion_diag[i].text.split("\n2")[0])
            elif companion_diag[i].text.rfind("\n0") != -1:
                all_messages_only_text.append(companion_diag[i].text.split("\n0")[0])

        for i in range(len(all_messages_only_text)):
            message = all_messages_only_text[i]
            file = open(path_to_txt, 'a', encoding='utf-8')
            file.write(f'{message}' + '\n')
            file.close()

        # Чтение из .txt и запись(копирование) в буфер обмена ОС
        import pyperclip
        file = open(path_to_txt, 'r', encoding='utf-8')
        pyperclip.copy(file.read())
        pyperclip.paste()
        file.close()

        
        # Вывод в терминал
        file = open(path_to_txt, 'r', encoding='utf-8')
        print(file.read())
        file.close()

        self.logger.info(config.get('Settings', 'clipboard'))

    def format_meta_block(self, block):
        return block.get_attribute('data-pre-plain-text').split('] ')[1]

def Config(path):
    """
    Чтение конфига
    :param path: путь к файлу конфигурации
    :return: параметры конфига
    """
    import configparser  # импортируем библиотеку
    config = configparser.ConfigParser()  # создаём объекта парсера
    config.read(path, encoding='utf-8')  # читаем конфиг
    return config

def net_connection(func, logger, verbose="no"):
    count = 10
    while True:
        if count == 0:
            logger.info(f'Время истекло')
            exit()
                
        try:
            if verbose in "no":
                reval = bin_forward(lambda: func())
            elif verbose in "yes":
                reval = func()
            else:
                pass
            break
            
        except requests.exceptions.ConnectionError: 
            count -= 1
            logger.warning("Ошибка соединения. Осталось времени на переподключение: " + f'{count}')
            time.sleep(1)

    return reval

def bin_forward(func):
    old_targeterr = sys.stderr
    f = open('nul', 'w')
    sys.stderr = f
    reval = func()
    sys.stderr = old_targeterr
    return reval

def build_logger():
    # root logger
    logging.getLogger().setLevel(logging.INFO)

    # WhatsApp logger
    logger = logging.getLogger("WhatsApp")
    c_handler = logging.StreamHandler()
    c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    logger.addHandler(c_handler)
    return logger

def build_chrome_options():
    chrome_options = Options()

    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_argument(config.get('Settings', 'WINDOW_SIZE'))
    chrome_options.add_argument(config.get('Settings', 'PATH_TO_COOKIE'))
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--ignore-ssl-errors=yes")
    chrome_options.add_argument("--ignore-certificate-errors")
    return chrome_options 

def check_dublication_web_browser(logger):
    task_manager = wmi.WMI()
    while True:
        for process in task_manager.Win32_Process(): 
            if "chrome.exe" in process.name:
                logger.warning(f'Обнаружена запущенная сессия. Пожалуйста, закройте окно веб-браузера и нажмите Enter')
                input()
                break
        else:
            break

# Сборка .exe файла в один + иконка
# pyinstaller -F --icon=Whatsapp.ico Whatsapp.py

if __name__ == '__main__':
    path = "config.ini"
    config = Config(path)
    logger = build_logger()
    chrome_options = build_chrome_options()
    check_dublication_web_browser(logger)
    driver = net_connection(
                            lambda: webdriver.Chrome(executable_path=ChromeDriverManager().install(),
                            options=chrome_options),
                            logger
                            )

    try:
        bot = Whatsapp(driver, config, logger)
        bot.login()
        bot.parse()

        logger.info(config.get("Settings", "finished"))    
        input()
        driver.quit()
        exit()
    
    except WebDriverException:
        logger.error(f'Ошибка Сhrome драйвера. Нажмите Enter для выхода из программы')
        input()
        driver.quit()
        exit()

    except Exception:
        logger.error(f'Неизвестная ошибка. Нажмите Enter для выхода из программы')
        input()
        driver.quit()
        exit()

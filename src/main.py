#!/usr/bin/env python


from __future__ import print_function
import os
import sys
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

# system
from   datetime import datetime, timedelta
from   functools import wraps
import pprint
import random
import re
import sys
import time


# pypi
import argh
import click
from clint.textui import progress
from splinter import Browser

from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException, WebDriverException
from selenium.webdriver.common.by import By
import selenium.webdriver.support.expected_conditions as EC
import selenium.webdriver.support.ui as ui

# local
import conf  # it is used. Even though flymake cant figure that out.



random.seed()

pp = pprint.PrettyPrinter(indent=4)

base_url = 'https://www.sharebuilder.com/'

action_path = dict(
    login = "",
    trade = 'sharebuilder/trade/realtime.aspx',
)

one_minute    = 60
three_minutes = 3 * one_minute
ten_minutes   = 10 * one_minute
one_hour      = 3600


def url_for_action(action):
    return "{0}/{1}".format(base_url, action_path[action])

def loop_forever():
    while True: pass

def wait_visible(driver, locator, by=By.XPATH, timeout=30):
    try:
        return ui.WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((by, locator)))
    except TimeoutException:
        return False

def trap_unexpected_alert(func):
    @wraps(func)
    def wrapper(self):
        try:
            return func(self)
        except UnexpectedAlertPresentException:
            print("Caught unexpected alert.")
            return 254
        except WebDriverException:
            print("Caught webdriver exception.")
            return 254

    return wrapper

def trap_any(func):
    @wraps(func)
    def wrapper(self):
        try:
            return func(self)
        except:
            print("Caught exception.")
            return 254

    return wrapper

def trap_alert(func):
    @wraps(func)
    def wrapper(self):
        try:
            return func(self)
        except UnexpectedAlertPresentException:
            print("Caught UnexpectedAlertPresentException.")
            return 254

    return wrapper


class Entry(object):

    def __init__(
            self, browser, spend, profit, symbol
    ):


        self._username = conf.username
        self._password = conf.password
        self.browser = browser
        self.spend = spend
        self.profit = profit
        self.symbol = symbol


    def login(self):
        print("Logging in...")

        self.browser.visit(url_for_action('login'))

        self.browser.find_by_name('widget_signInUsername').type(self._username)
        self.browser.find_by_name('widget_signInPassword').type(self._password)

        elem = self.browser.find_by_xpath(
            '//span[text()="Sign In"]'
        )

        elem = elem[1]

        print("Found elem {}".format(elem))

        elem.click()

    def view_ads(self):
        for i in xrange(1,11):
            print("Viewing ad {0}".format(i))
            while True:
                result = self.view_ad()
                if result == 0:
                    break

        self.calc_time(stay=False)
        self.calc_account_balance()


    @trap_alert
    def view_ad(self):

        self.browser.visit(url_for_action('viewads'))
        time.sleep(random.randrange(2,5))

        buttons = self.browser.find_by_css('.text_button')
        #print("Found {0} buttons".format(buttons))

        buttons[0].click()

        self.solve_captcha()

        #self.wait_on_ad()
        self.wait_on_ad2()

        return 0

    def wait_on_ad(self):
        time_to_wait_on_ad = random.randrange(40,50)
        for i in progress.bar(range(time_to_wait_on_ad)):
            time.sleep(1)

    def wait_on_ad2(self):
        wait_visible(self.browser.driver,
                     '//img[@src="images/moreadstop.gif"]',
                     By.XPATH,
                     60)


    def calc_account_balance(self):

        time.sleep(3)

        self.browser.visit(url_for_action('dashboard'))

        elem = self.browser.find_by_xpath(
            '/html/body/table[2]/tbody/tr/td[2]/table/tbody/tr/td[2]/table[6]/tbody/tr/td/table/tbody/tr[2]/td/h2[2]/font/font'
        )

        print("Available Account Balance: {}".format(elem.text))


    def calc_time(self, stay=True):

        time.sleep(3)

        self.browser.visit(url_for_action('dashboard'))

        elem = self.browser.find_by_xpath(
            '//table[@width="80%"]/tbody/tr/td[1]'
        )

        remaining = elem.text.split()
        for i, v in enumerate(remaining):
            print(i,v)

        indices = dict(
            hours=17,
            minutes=19
        )

        hours = int(remaining[indices['hours']])
        minutes = int(remaining[indices['minutes']])

        next_time  = datetime.now() + timedelta(
            hours=hours, minutes=minutes)

        print("Next time to click is {0}".format(
            next_time.strftime("%Y-%m-%d %H:%M")))

        if stay:
            loop_forever()

    def solve_captcha(self):
        time.sleep(3)
        elem = self.browser.find_by_xpath(
            "/html/body/form[@id='form1']/table/tbody/tr/td/table/tbody/tr[1]/td/font"
        )
        time.sleep(3)

        (x, y, captcha) = elem.text.split()

        print("CAPTCHA = {0}".format(captcha))

        self.browser.find_by_name('codeSb').fill(captcha)

        time.sleep(6)
        button = self.browser.find_by_name('Submit')
        button.click()


@click.command()
@click.option('--spend', default=1000, help="Amout to spend.")
@click.option('--profit', default=5, help='Desired percentage of profit')
@click.option('--symbol', prompt='Symbol to trade')
def main(spend, profit, symbol):
    '''Program to login and issue a trade'''

    symbol = symbol.upper()

    print(locals())

    with Browser() as browser:

        browser.driver.set_window_size(1200,1100)

        e = Entry(browser, spend, profit, symbol)

        e.login()

        loop_forever()

if __name__ == '__main__':
    main()

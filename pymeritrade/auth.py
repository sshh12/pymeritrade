from urllib.parse import unquote_plus
import webbrowser
import time

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium import webdriver

from pymeritrade.errors import TDAPermissionsError


class DefaultAuthHandler:
    def __init__(self, client):
        self.client = client

    def login(self):
        if self.client.access_token is None:
            try:
                self.client.access_token, self.client.refresh_token = self.generate_token()
            except Exception as e:
                raise TDAPermissionsError("Login failed " + str(e))
        if not self.client.check_login() and not self.client._refresh_token():
            self.on_failed_refresh()
            if not self.client.check_login():
                raise TDAPermissionsError("Unable to login after token refresh.")
        self.client._setup()

    def get_code_from_auth_url(self, auth_url):
        print("Go to the link below, login, then copy the code from the url.")
        print(auth_url)
        webbrowser.open(auth_url)
        code = unquote_plus(input("code > "))
        if "?code=" in code:
            # user passed entire url rather than just the code.
            code = code.split("?code=")[1]
        return code

    def generate_token(self):
        print("Generating access token...")
        auth_url = (
            "https://auth.tdameritrade.com/auth?"
            + "response_type=code&redirect_uri={}&client_id={}@AMER.OAUTHAP".format(
                self.client.redirect_uri, self.client.consumer_key
            )
        )
        code = self.get_code_from_auth_url(auth_url)
        resp = self.client._call_oauth(
            dict(
                grant_type="authorization_code",
                access_type="offline",
                client_id=self.client.consumer_key + "@AMER.OAUTHAP",
                redirect_uri=self.client.redirect_uri,
                code=code,
            )
        )
        if "access_token" not in resp:
            raise TDAPermissionsError(str(resp))
        access_token = resp["access_token"]
        refresh_token = resp["refresh_token"]
        return access_token, refresh_token

    def on_failed_refresh(self):
        access_token, refresh_token = self.generate_token()
        self.client.access_token = access_token
        self.client.refresh_token = refresh_token
        self.client.login()


class SeleniumHandler(DefaultAuthHandler):
    def get_sms_code(self):
        return input("SMS code > ")

    def get_phone_idx(self):
        return 0

    def get_login_creds(self):
        username = input("Username > ")
        password = input("Password > ")
        return username, password

    def get_driver(self):
        return webdriver.Chrome()

    def wait_a_little(self):
        time.sleep(2)

    def get_code_from_auth_url(self, auth_url):
        self.driver = self.get_driver()
        self.driver.get(auth_url)
        username, password = self.get_login_creds()
        self._type_field("username0", username)
        self._type_field("password", password)
        self._accept()
        self.wait_a_little()
        phone_xpath = '//label[@for="smsnumber0_{}"]'.format(self.get_phone_idx())
        self.driver.find_element(By.XPATH, phone_xpath).click()
        self._accept()
        self._type_field("smscode0", self.get_sms_code())
        time.sleep(3)
        self._accept()
        self.wait_a_little()
        trust_xpath = '//label[@for="trustthisdevice0_0"]'
        self.driver.find_element(By.XPATH, trust_xpath).click()
        self._accept()
        self.wait_a_little()
        self._accept()
        self.wait_a_little()
        code = unquote_plus(self.driver.current_url.split("?code=")[1])
        self.driver.quit()
        return code

    def _type_field(self, elem_id, text):
        wait = WebDriverWait(self.driver, 10)
        wait.until(expected_conditions.element_to_be_clickable((By.ID, elem_id)))
        elem = self.driver.find_element_by_id(elem_id)
        elem.send_keys(text)

    def _click_xpath(self, xpath):
        wait = WebDriverWait(self.driver, 10)
        wait.until(expected_conditions.element_to_be_clickable((By.XPATH, xpath)))
        self.driver.find_element_by_xpath(xpath).click()

    def _accept(self):
        wait = WebDriverWait(self.driver, 10)
        wait.until(expected_conditions.element_to_be_clickable((By.ID, "accept")))
        self.driver.find_element_by_id("accept").click()


class SeleniumQuestionHandler(SeleniumHandler):
    def answer_question(self, question):
        return "answer"

    def get_code_from_auth_url(self, auth_url):
        self.driver = self.get_driver()
        self.driver.get(auth_url)
        username, password = self.get_login_creds()
        self._type_field("username0", username)
        self._type_field("password", password)
        self._accept()
        self.wait_a_little()
        self._click_xpath("/html/body/form/main/details/summary")
        self.wait_a_little()
        self._click_xpath("/html/body/form/main/details/div[4]/div/input")
        self.wait_a_little()
        question = self.driver.find_element_by_xpath("/html/body/form/main/div[2]/p[2]").get_attribute("innerText")
        ans = self.answer_question(question)
        self._type_field("secretquestion0", ans)
        self.wait_a_little()
        self._accept()
        self.wait_a_little()
        self._click_xpath("/html/body/form/main/fieldset/div/div[1]/label")
        self._accept()
        self.wait_a_little()
        self._accept()
        self.wait_a_little()
        code = unquote_plus(self.driver.current_url.split("?code=")[1])
        self.driver.quit()
        return code


class SeleniumHeadlessHandler(SeleniumHandler):
    def get_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        return webdriver.Chrome(chrome_options=chrome_options)


class SeleniumHeadlessQuestionHandler(SeleniumQuestionHandler):
    def get_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        return webdriver.Chrome(chrome_options=chrome_options)
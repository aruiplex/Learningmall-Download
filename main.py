import os
from pathlib import Path
import argparse
import requests
import bs4
import logging
import http.client as http_client
from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def get_cookies(username, password):
    """Get cookies from learningmall

    Returns:
        cookies: str of cookies
    """

    op = webdriver.ChromeOptions()
    op.add_argument('--headless')
    op.add_argument('--disable-gpu')
    op.add_argument('--no-sandbox')
    op.add_argument('--disable-dev-shm-usage')
    op.add_argument('--disable-extensions')

    web = webdriver.Chrome(
        executable_path=r"C:\App\chromedriver.exe", options=op)
    web.set_window_size(1920, 1080)
    web.get("https://sso.xjtlu.edu.cn/login")

    # login in oss
    web.find_element_by_xpath(
        '//*[@id="username_show"]').send_keys(username)
    web.find_element_by_xpath(
        '//*[@id="password_show"]').send_keys(password)
    web.find_element_by_xpath('//*[@id="btn_login"]/div/input').click()

    # switch to learning mall
    # click element in iframe
    try:
        # wait for web.switch_to.frame("main")
        WebDriverWait(web, 20).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))

        # wait for  web.find_element_by_xpath('//*[@id="appBox1"]/div[2]/div[1]').click()
        WebDriverWait(web, 20).until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="appBox1"]/div[2]/div[1]'))).click()
    except Exception as e:
        print(e)

    # wait for new_window_is_opened, because open window will spend time.
    # if immediately switch window, it will not work. use this method to instead os.sleep()
    WebDriverWait(web, 20).until(EC.new_window_is_opened(web.window_handles))
    # switch to current window
    web.switch_to.window(web.window_handles[-1])
    cks = web.get_cookies()
    cookies = ""
    # concat cookies to string
    for ck in cks:
        cookies += ck["name"] + "=" + ck["value"] + "; "
    web.close()
    return cookies


output_path = Path()

s = requests.Session()
s.headers = {
    "User-Agent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
}


def get_file_links(url: str) -> list:
    """Get all the file links in a course

    Args:
        url (string): coures url

    Returns:
        links: list of file links
    """
    res = s.request("GET", url)
    if res.status_code != 200:
        logging.error(f"Failed to get course page: {res.text}")
        exit(1)

    soup = bs4.BeautifulSoup(res.text, "html.parser")
    # find all links in first page in lmo causea page
    rs = soup.find_all("a", "aalink", href=True)
    links = []
    for r in rs:
        links.append(r["href"])
    return links


    # for link in links:
exists = os.listdir(output_path)


def get_file(link: str):
    """Get a file from a link

    Args:
        link (string): file link
    """
    # download the file in second page in lmo
    res = s.request("GET", link)
    soup = bs4.BeautifulSoup(res.text, "html.parser")
    # find file position
    rs = soup.find_all("div", "resourceworkaround")
    for r in rs:
        # write file with filename and content
        filename = r.a.text
        if filename in exists:
            logout.info("Downloaded file: " + filename + " exists")
        else:
            res = s.get(r.a["href"])
            f = open(os.path.join(output_path, filename), "wb")
            f.write(res.content)
            f.close()
            logout.info("Downloaded file: " + filename)


def get_args():
    parser = argparse.ArgumentParser(
        description="Download all the files in a Learning Mallcourse")
    parser.add_argument("-c", "--course", help="course url", required=True)
    parser.add_argument(
        "-u", "--username", help="username for login learning mall, if you use this option, the json file will be ignore.", required=False)
    parser.add_argument(
        "-p", "--password", help="password for login learning mall, if you use this option, the json file will be ignore.", required=False)
    parser.add_argument(
        "-ck", "--cookie", help="learning mall cookie, if use the option, program will not login automatically.", required=False)
    parser.add_argument(
        "-o", "--output", help="output directory", default=".", required=False)
    parser.add_argument("-v", "--verbose", help="verbose",
                        required=False, action="store_true")
    parser.add_argument("-t", "--threads", help="threads number",
                        default=3, required=False, type=int)
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()

    # init_logger(args.verbose)
    logout = logging.getLogger(__name__+".stdout_logger")
    if args.verbose:
        logout.setLevel(logging.INFO)
        http_client.HTTPConnection.debuglevel = 1
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.propagate = True
    else:
        logout.setLevel(logging.ERROR)
    logout.addHandler(logging.StreamHandler())

    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    exists = os.listdir(output_path)

    if args.username and args.password:
        username = args.username
        password = args.password
    else:
        import json
        cfg = json.load(open("account.json"))
        username = cfg['username']
        password = cfg['password']

    if args.cookie:
        s.headers["Cookie"] = args.cookie
    else:
        s.headers["Cookie"] = get_cookies(username, password)

    if args.verbose:
        print(s.headers["Cookie"])

    links = get_file_links(args.course)
    links = [x for x in links if "resource" in x]
    logout.info(f"Found files: {links}")

    with ThreadPoolExecutor(max_workers=int(args.threads)) as executor:
        executor.map(get_file, links)

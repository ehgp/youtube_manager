"""Youtube Manager.

From a list of movies that you want to download
seach YouTube and download the movies
Then upload them into your YT studio

*Not responsible for CR claims use at own risk*

author: ehgp
"""
from pytube import YouTube
import string
import pandas as pd
from os import listdir
from os.path import isfile, join
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from getpass import getuser
from bs4 import BeautifulSoup
import shutil
import time
import logging
import logging.config
import random
import os
import re
import sys
import datetime as dt
from pathlib import Path
import yaml
import keyring

yes = {"yes", "ye", "y"}
no = {"no", "n"}

# Creds
user = getuser()
yt_email = keyring.get_password("YOUTUBE_EMAIL", user)
yt_pass = keyring.get_password("YOUTUBE_PASSWORD", user)

# Paths
path = Path(os.getcwd())
binary_path = Path(path, "chromedriver.exe")
downloads_path = Path(path, "Downloads")


# Logging
log_config = Path(path, "log_config.yaml")
timestamp = "{:%Y_%m_%d_%H_%M_%S}".format(dt.datetime.now())
with open(log_config, "r") as log_file:
    config_dict = yaml.safe_load(log_file.read())
    # Append date stamp to the file name
    log_filename = config_dict["handlers"]["file"]["filename"]
    base, extension = os.path.splitext(log_filename)
    base2 = "youtube_manager"
    log_filename = "{}{}{}{}".format(base, base2, timestamp, extension)
    config_dict["handlers"]["file"]["filename"] = log_filename
    logging.config.dictConfig(config_dict)
logger = logging.getLogger(__name__)

# https://www.google.com/settings/security/lesssecureapps

print(
    "To start this program. select what you wanna do upload or download. your search terms will be added and videos will be pulled according to your choice of criteria (time uploaded and sort by highest rating) and will output an excel sheet with  new_title, new_descriptions and new tags column which must be filled by user before upload WORKS WTIH CHROME 88 ONLY"
)
time.sleep(10)


choice_what = int(
    input(
        """
WHAT DO YOU WANNA DO?
1 - DOWNLOAD VIDEOS
2 - UPLOAD VIDEOS
PLEASE USE 1 DIGIT ONLY: """
    )
)

if (choice_what < 1) | (choice_what > 2):
    print("wrong digit try again")
    exit()


YOUTUBE_LOGIN = "https://accounts.google.com/ServiceLogin/signinchooser?service=youtube"

YOUTUBE_SEARCH_BAR = "https://www.youtube.com/results?search_query="

# YOUTUBE_SEARCH_STRING = '-lyrics -link -part -lyrical -song -cover -playlist -review -quotes -game -trailer \"how to\" -hindi -reaction -bollywood -nollywood -hot -erotic'

YOUTUBE_FILTER_BUTTON = "//paper-button[@aria-label='Search filters']"

YOUTUBE_UP_LAST_HOUR = "//yt-formatted-string[text()='Last hour']"

YOUTUBE_UP_TODAY = "//yt-formatted-string[text()='Today']"

YOUTUBE_UP_THIS_WEEK = "//yt-formatted-string[text()='This week']"

YOUTUBE_UP_THIS_MONTH = "//yt-formatted-string[text()='This month']"

YOUTUBE_UP_THIS_YEAR = "//yt-formatted-string[text()='This year']"

YOUTUBE_TYPE_VIDEO = "//yt-formatted-string[text()='Video']"

YOUTUBE_TYPE_CHANNEL = "//yt-formatted-string[text()='Channel']"

YOUTUBE_TYPE_PLAYLIST = "//yt-formatted-string[text()='Playlist']"

YOUTUBE_TYPE_MOVIE = "//yt-formatted-string[text()='Movie']"

YOUTUBE_TYPE_SHOW = "//yt-formatted-string[text()='Show']"

YOUTUBE_DURATION_SHORT = "//yt-formatted-string[text()='Short (< 4 minutes)']"

YOUTUBE_DURATION_LONG = "//yt-formatted-string[text()='Long (> 20 minutes)']"

YOUTUBE_FEATURED_LIVE = "//yt-formatted-string[text()='Live']"

YOUTUBE_FEATURED_4K = "//yt-formatted-string[text()='4K']"

YOUTUBE_FEATURED_HD = "//yt-formatted-string[text()='HD']"

YOUTUBE_FEATURED_SUBTITLESCC = "//yt-formatted-string[text()='Subtitles/CC']"

YOUTUBE_FEATURED_CREATIVE = "//yt-formatted-string[text()='Creative Commons']"

YOUTUBE_FEATURED_360 = "//yt-formatted-string[text()='360°']"

YOUTUBE_FEATURED_VR180 = "//yt-formatted-string[text()='VR180']"

YOUTUBE_FEATURED_3D = "//yt-formatted-string[text()='3D']"

YOUTUBE_FEATURED_HDR = "//yt-formatted-string[text()='HDR']"

YOUTUBE_FEATURED_LOCATION = "//yt-formatted-string[text()='Location']"

YOUTUBE_FEATURED_PURCHASED = "//yt-formatted-string[text()='Purchased']"

YOUTUBE_SORT_BY_REVELANCE = "//yt-formatted-string[text()='Relevance']"

YOUTUBE_SORT_BY_UPLOAD_DATE = "//yt-formatted-string[text()='Upload Date']"

YOUTUBE_SORT_BY_RATING = "//yt-formatted-string[text()='Rating']"

YOUTUBE_SORT_BY_VIEW_COUNT = "//yt-formatted-string[text()='View count']"

# UPLOAD PARAMETERS
YOUTUBE_STUDIO = "https://studio.youtube.com/channel/"

YOUTUBE_UPLOAD_BUTTON = "//ytcp-button[@id='upload-button']"

YOUTUBE_TITLE_XPATH = "//ytcp-mention-input[@id='input']/div[@aria-label='Add a title that describes your video']"

YOUTUBE_DESCRIPTION_XPATH = (
    "//ytcp-mention-input[@id='input']/div[@aria-label='Tell viewers about your video']"
)

YOUTUBE_NO_KIDS_XPATH = "//paper-radio-button[@name='NOT_MADE_FOR_KIDS']"

YOUTUBE_MORE_OPTIONS_XPATH = "//ytcp-button[@label='More options']"

YOUTUBE_PAID_PROMO_XPATH = "//ytcp-checkbox-lit[@id='has-ppp']"

YOUTUBE_TAGS_XPATH = "//input[@aria-label='Tags']"

YOUTUBE_NEXT_XPATH = "//ytcp-button[@id='next-button']"

YOUTUBE_PUBLIC_XPATH = "//paper-radio-button[@name='PUBLIC']"

YOUTUBE_DONE_XPATH = "//ytcp-button[@id='done-button']"

# Configure ChromeOptions
options = Options()
options.page_load_strategy = "eager"
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
# prefs = {"profile.managed_default_content_settings.images": 2}
# options.add_experimental_option("prefs", prefs)
options.add_argument("user-data-dir=.profile-YOUTUBE")
# options.add_argument('--proxy-server=https://'+ self.proxies[0])
# options.add_argument('--proxy-server=http://'+ self.proxies[0])
# options.add_argument('--proxy-server=socks5://'+ self.proxies[0])
options.add_argument("--disable-notifications")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--ignore-ssl-errors")
# options.add_argument('user-agent = Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36')
# options.add_argument('--headless')
# options.add_argument('--window-size=1910x1080')
# options.add_argument('--proxy-server=http://'+ proxies[0])


def format_filename(s):
    """Take a string and return a valid filename constructed from the string.

    Uses a whitelist approach: any characters not present in valid_chars are
    removed.

    Note: this method may produce invalid filenames such as ``, `.` or `..`
    When I use this method I prepend a date string like '2009_01_15_19_46_32_'
    and append a file extension like '.txt', so I avoid the potential of using
    an invalid filename.
    """
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = "".join(re.sub("[^A-Za-z0-9]+", " ", c) for c in s if c in valid_chars)
    return filename


def save_html_to_file(response, title):
    """Save response to 'response.html'."""
    with open(Path(path, f"/responseYOUTUBE{title}.html"), "w", encoding="utf-8") as fp:
        fp.write(response)


def login(yt_email, yt_pass):
    """Login to YT."""
    driver.get(
        "https://accounts.google.com/o/oauth2/auth/identifier?client_id=717762328687-iludtf96g1hinl76e4lc1b9a82g457nn.apps.googleusercontent"
        ".com&scope=profile%20email&redirect_uri=https%3A%2F%2Fstackauth.com%2Fauth%2Foauth2%2Fgoogle&state=%7B%22sid%22%3A1%2C%22st%22%3A%2"
        "259%3A3%3Abbc%2C16%3A561fd7d2e94237c0%2C10%3A1599663155%2C16%3Af18105f2b08c3ae6%2C2f06af367387a967072e3124597eeb4e36c2eff92d3eef697"
        "1d95ddb5dea5225%22%2C%22cdl%22%3Anull%2C%22cid%22%3A%22717762328687-iludtf96g1hinl76e4lc1b9a82g457nn.apps.googleusercontent.com%22%"
        "2C%22k%22%3A%22Google%22%2C%22ses%22%3A%2226bafb488fcc494f92c896ee923849b6%22%7D&response_type=code&flowName=GeneralOAuthFlow"
    )

    driver.find_element_by_name("identifier").send_keys(yt_email)
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[@id='identifierNext']/div/button/div[2]")
        )
    ).click()
    driver.implicitly_wait(random.randint(4, 6))

    try:
        driver.find_element_by_name("password").send_keys(yt_pass)
        WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[@id='passwordNext']/div/button/div[2]")
            )
        ).click()
    except TimeoutException:
        print(
            "\nUsername/Password seems to be incorrect, please re-check\nand Re-Run the program."
        )
        exit()
    except NoSuchElementException:
        print(
            "\nUsername/Password seems to be incorrect, please re-check\nand Re-Run the program."
        )
        exit()
    try:
        WebDriverWait(driver, 5).until(
            lambda webpage: "https://stackoverflow.com/" in webpage.current_url
        )
        print("\nLogin Successful!\n")
    except TimeoutException:
        print(
            "\nUsername/Password seems to be incorrect, please re-check\nand Re-Run the program."
        )
        exit()


if choice_what == 1:
    if os.path.exists(".profile-YOUTUBE"):
        PATHDS = Path(path, ".profile-YOUTUBE")
        shutil.rmtree(PATHDS)
    YOUTUBE_SEARCH_STRING = input("Please input your search terms: ")

    choice_time = int(
        input(
            """
1 - UPLOADED_LAST_HOUR
2 - UPLOADED_TODAY
3 - UPLOADED_THIS_WEEK
4 - UPLOADED_THIS_MONTH
5 - UPLOADED_THIS_YEAR
PLEASE USE 1 DIGIT ONLY: """
        )
    )

    if (choice_time < 1) | (choice_time > 5):
        print("wrong digit try again")
        exit()

    choice_sort = int(
        input(
            """
1 - RELEVANT
2 - UPLOAD DATE
3 - VIEW COUNT
4 - RATING
PLEASE USE 1 DIGIT ONLY: """
        )
    )

    if (choice_sort < 1) | (choice_sort > 5):
        print("wrong digit try again")
        exit()

    links = []
    stats = []
    titles = []
    tags = []
    description = []
    # CREATES SEARCH AND GRABS LINKS AND DOWNLOADS VIDEOS WITH METADATA
    with webdriver.Chrome(executable_path=binary_path, options=options) as driver:
        login(yt_email, yt_pass)
        driver.get(YOUTUBE_SEARCH_BAR + YOUTUBE_SEARCH_STRING)
        time.sleep(random.uniform(0.5, 0.8))
        if choice_time == 1:
            youtube_filter = (
                WebDriverWait(driver, 10)
                .until(EC.element_to_be_clickable((By.XPATH, YOUTUBE_FILTER_BUTTON)))
                .click()
            )
            time.sleep(random.uniform(0.5, 0.8))
            this_hour = (
                WebDriverWait(driver, 10)
                .until(EC.element_to_be_clickable((By.XPATH, YOUTUBE_UP_LAST_HOUR)))
                .click()
            )
            time.sleep(random.uniform(0.5, 0.8))
        if choice_time == 2:
            youtube_filter = (
                WebDriverWait(driver, 10)
                .until(EC.element_to_be_clickable((By.XPATH, YOUTUBE_FILTER_BUTTON)))
                .click()
            )
            time.sleep(random.uniform(0.5, 0.8))
            this_hour = (
                WebDriverWait(driver, 10)
                .until(EC.element_to_be_clickable((By.XPATH, YOUTUBE_UP_TODAY)))
                .click()
            )
            time.sleep(random.uniform(0.5, 0.8))
        if choice_time == 3:
            youtube_filter = (
                WebDriverWait(driver, 10)
                .until(EC.element_to_be_clickable((By.XPATH, YOUTUBE_FILTER_BUTTON)))
                .click()
            )
            time.sleep(random.uniform(0.5, 0.8))
            this_week = (
                WebDriverWait(driver, 10)
                .until(EC.element_to_be_clickable((By.XPATH, YOUTUBE_UP_THIS_WEEK)))
                .click()
            )
            time.sleep(random.uniform(0.5, 0.8))
        if choice_time == 4:
            youtube_filter = (
                WebDriverWait(driver, 10)
                .until(EC.element_to_be_clickable((By.XPATH, YOUTUBE_FILTER_BUTTON)))
                .click()
            )
            time.sleep(random.uniform(0.5, 0.8))
            this_month = (
                WebDriverWait(driver, 10)
                .until(EC.element_to_be_clickable((By.XPATH, YOUTUBE_UP_THIS_MONTH)))
                .click()
            )
            time.sleep(random.uniform(0.5, 0.8))
        if choice_time == 5:
            youtube_filter = (
                WebDriverWait(driver, 10)
                .until(EC.element_to_be_clickable((By.XPATH, YOUTUBE_FILTER_BUTTON)))
                .click()
            )
            time.sleep(random.uniform(0.5, 0.8))
            this_year = (
                WebDriverWait(driver, 10)
                .until(EC.element_to_be_clickable((By.XPATH, YOUTUBE_UP_THIS_YEAR)))
                .click()
            )
            time.sleep(random.uniform(0.5, 0.8))
        if choice_sort == 1:
            youtube_filter = (
                WebDriverWait(driver, 10)
                .until(EC.element_to_be_clickable((By.XPATH, YOUTUBE_FILTER_BUTTON)))
                .click()
            )
            time.sleep(random.uniform(0.5, 0.8))
            revelant = (
                WebDriverWait(driver, 10)
                .until(
                    EC.element_to_be_clickable((By.XPATH, YOUTUBE_SORT_BY_REVELANCE))
                )
                .click()
            )
            time.sleep(random.uniform(0.5, 0.8))
        if choice_sort == 2:
            youtube_filter = (
                WebDriverWait(driver, 10)
                .until(EC.element_to_be_clickable((By.XPATH, YOUTUBE_FILTER_BUTTON)))
                .click()
            )
            time.sleep(random.uniform(0.5, 0.8))
            this_hour = (
                WebDriverWait(driver, 10)
                .until(
                    EC.element_to_be_clickable((By.XPATH, YOUTUBE_SORT_BY_UPLOAD_DATE))
                )
                .click()
            )
            time.sleep(random.uniform(0.5, 0.8))
        if choice_sort == 3:
            youtube_filter = (
                WebDriverWait(driver, 10)
                .until(EC.element_to_be_clickable((By.XPATH, YOUTUBE_FILTER_BUTTON)))
                .click()
            )
            time.sleep(random.uniform(0.5, 0.8))
            this_hour = (
                WebDriverWait(driver, 10)
                .until(
                    EC.element_to_be_clickable((By.XPATH, YOUTUBE_SORT_BY_VIEW_COUNT))
                )
                .click()
            )
            time.sleep(random.uniform(0.5, 0.8))
        if choice_sort == 4:
            youtube_filter = (
                WebDriverWait(driver, 10)
                .until(EC.element_to_be_clickable((By.XPATH, YOUTUBE_FILTER_BUTTON)))
                .click()
            )
            time.sleep(random.uniform(0.5, 0.8))
            this_hour = (
                WebDriverWait(driver, 10)
                .until(EC.element_to_be_clickable((By.XPATH, YOUTUBE_SORT_BY_RATING)))
                .click()
            )

        # for i in range(0,2):
        #     time.sleep(random.uniform(0.5,0.8))
        #     driver.find_element_by_tag_name('body').send_keys(Keys.END)
        time.sleep(random.randint(10, 15))
        elem = driver.find_element_by_xpath("//*")
        source_code = elem.get_attribute("outerHTML")
        save_html_to_file(source_code, 0)
        soup = BeautifulSoup(source_code, "lxml")

    links = [
        "https://www.youtube.com"
        + soup.findAll("a", attrs={"id": "video-title"})[i]["href"]
        for i in range(0, len(soup.findAll("a", attrs={"id": "video-title"})))
    ][0:10]

    stats = [
        soup.findAll("a", attrs={"id": "video-title"})[i]["aria-label"]
        for i in range(0, len(soup.findAll("a", attrs={"id": "video-title"})))
    ][0:10]

    # titles = [format_filename(soup.findAll("a", attrs={"id": "video-title"})[i]['title']).replace('  ','').replace('mp4','.mp4') for i in range(0,len(soup.findAll("a", attrs={"id": "video-title"})))][0:10]

    for i in links:
        time.sleep(random.uniform(0.5, 0.8))
        video = YouTube(i)
        titles.append(
            format_filename(video.title).replace("  ", "").replace("mp4", ".mp4")
        )
        tags.append(video.keywords)
        description.append(
            format_filename(video.description).replace("  ", "").replace("mp4", ".mp4")
        )
        stream = video.streams.get_highest_resolution()
        time.sleep(random.uniform(0.5, 0.8))
        stream.download(downloads_path)

    your_title = [""] * 10
    your_description = [""] * 10
    your_tags = [""] * 10
    new_videos = pd.DataFrame(
        {
            "your_title": your_title,
            "your_description": your_description,
            "your_tags": your_tags,
            "new_title": titles,
            "new_description": description,
            "new_link": links,
            "new_stat": stats,
            "new_tags": tags,
        }
    )

    new_videos.to_csv(str(path) + "\\metadata\\new_videos_youtube.csv", index=False)

    answer = input("Ingestion's done ^_^: Would you like to upload? (y/n): ")

if answer in yes:
    if choice_what == 2:
        if os.path.exists(".profile-YOUTUBE"):
            PATHDS = Path(path, "/.profile-YOUTUBE")
            shutil.rmtree(PATHDS)
        os.chdir(path)
        onlyfiles = [
            os.rename(
                os.path.join(downloads_path, f),
                os.path.join(
                    downloads_path,
                    format_filename(f).replace("  ", "").replace("mp4", ".mp4"),
                ),
            )
            for f in listdir(downloads_path)
            if isfile(join(downloads_path, f))
        ]
        onlyfiles = [f for f in listdir(downloads_path)]
        print("# of files to upload: " + str(len(onlyfiles)))

        for k in range(0, len(onlyfiles)):
            video_path = Path(path, "Downloads", onlyfiles[k])
            video_data = pd.read_csv(Path(path, "metadata", "new_videos_youtube.csv"))
            title = video_data[
                video_data["new_title"]
                == onlyfiles[k].replace(" .mp4", "").replace(".mp4", "")
            ]["your_title"]
            title.reset_index(inplace=True, drop=True)
            title = title[0]
            description = video_data["your_description"].loc[
                video_data["new_title"]
                == onlyfiles[k].replace(" .mp4", "").replace(".mp4", "")
            ]
            description.reset_index(inplace=True, drop=True)
            description = description[0]
            tags = video_data["your_tags"].loc[
                video_data["new_title"]
                == onlyfiles[k].replace(" .mp4", "").replace(".mp4", "")
            ]
            tags.reset_index(inplace=True, drop=True)
            tags = tags[0].replace("[", "").replace("]", "").replace("'", "")

            os.chdir(path)
            with webdriver.Chrome(
                executable_path=binary_path, options=options
            ) as driver:
                login(yt_email, yt_pass)
                driver.get(YOUTUBE_STUDIO)
                time.sleep(random.randint(3, 5))
                upload_vid = driver.find_element_by_xpath("/html/body").click()
                time.sleep(random.uniform(0.5, 0.8))
                upload_vid = (
                    WebDriverWait(driver, 10)
                    .until(
                        EC.element_to_be_clickable((By.XPATH, YOUTUBE_UPLOAD_BUTTON))
                    )
                    .click()
                )
                time.sleep(random.uniform(0.5, 0.8))
                fileInput = driver.find_element_by_xpath("//input[@type='file']")
                time.sleep(random.uniform(0.5, 0.8))
                driver.execute_script(
                    "arguments[0].style.display = 'block';", fileInput
                )
                time.sleep(random.uniform(0.5, 0.8))
                fileInput.send_keys(str(video_path))
                time.sleep(random.uniform(0.5, 0.8))
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, YOUTUBE_TITLE_XPATH))
                ).send_keys(Keys.BACKSPACE)
                time.sleep(random.uniform(0.5, 0.8))
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, YOUTUBE_TITLE_XPATH))
                ).send_keys(title)
                time.sleep(random.uniform(0.5, 0.8))
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, YOUTUBE_DESCRIPTION_XPATH))
                ).send_keys(description)
                time.sleep(random.uniform(0.5, 0.8))
                no_kids = driver.find_element_by_xpath(YOUTUBE_NO_KIDS_XPATH).click()
                time.sleep(random.uniform(0.5, 0.8))
                more_opts = driver.find_element_by_xpath(
                    YOUTUBE_MORE_OPTIONS_XPATH
                ).click()
                time.sleep(random.uniform(0.5, 0.8))
                paid_promo = driver.find_element_by_xpath(
                    YOUTUBE_PAID_PROMO_XPATH
                ).click()
                time.sleep(random.uniform(0.5, 0.8))
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, YOUTUBE_TAGS_XPATH))
                ).send_keys(tags)
                time.sleep(random.uniform(0.5, 0.8))
                next_button = (
                    WebDriverWait(driver, 10)
                    .until(EC.element_to_be_clickable((By.XPATH, YOUTUBE_NEXT_XPATH)))
                    .click()
                )
                time.sleep(random.uniform(0.5, 0.8))
                next_button = (
                    WebDriverWait(driver, 10)
                    .until(EC.element_to_be_clickable((By.XPATH, YOUTUBE_NEXT_XPATH)))
                    .click()
                )
                time.sleep(random.uniform(0.5, 0.8))
                public_button = driver.find_element_by_xpath(
                    YOUTUBE_PUBLIC_XPATH
                ).click()
                time.sleep(random.uniform(0.5, 0.8))
                save_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, YOUTUBE_DONE_XPATH))
                )
else:
    exit()

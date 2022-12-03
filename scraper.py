# This is a sample Python script.
import re

import discord
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import psycopg2
from discord import Webhook, RequestsWebhookAdapter
import configparser

driver = webdriver.Firefox()


def get_game_tiers():
    # game tiers
    games_collection = driver.find_elements(By.XPATH, "//span[@class='item-title']")

    tiers = []
    games_list = []
    tiers_games_dict = {}

    # issue with title
    for game in games_collection:
        game_name = game.text
        games_list.append(game_name)

    # If the bundle has multiple tiers
    if driver.find_elements(By.XPATH, "//div[@class='tier-filters']"):
        tier_options = driver.find_elements(By.XPATH, "//a[contains(@class, 'js-tier-filter')]")
        tier_price_size = {}

        for tier in tier_options:
            tier_size = re.search(r'\d+', tier.text).group()
            tier.click()
            tier_price = driver.find_element(By.XPATH, "//h3[contains(@class, 'tier-header')]").text
            tier_price_size[tier_price] = int(tier_size)

        games_list.reverse()
        prev_tier_size = 0
        first_tier = True
        for price_quote, size in reversed(tier_price_size.items()):
            # price_quote = re.search(r'£\d+.\d+', price_quote).group()

            # No change this back to just quoting what HB says so users are aware of average tiers
            # if first_tier:
            #     price_quote = "Pay at least " + price_quote + " to get " + str(size - prev_tier_size) + " items:"
            #     first_tier = False
            # else:
            #     price_quote = "Pay at least " + price_quote + " to get " + str(size - prev_tier_size) + " more items:"

            # Create dictionary item containing the tier + price coupled with the no. of games and the game names
            tiers_games_dict[price_quote] = games_list[prev_tier_size:size]
            # prev_tier_size = size
    else:
        # If the bundle is a single tier
        single_tier_items = driver.find_element(By.XPATH, "//h3[contains(@class, 'tier-header')]").text
        tiers_games_dict[single_tier_items] = games_list

    return tiers_games_dict


def get_list_of_games(new_bundle):
    driver.get(new_bundle)
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
        (By.XPATH, "//div[@class='desktop-tier-collection-view']")))

    tiers_games_dict = get_game_tiers()

    message = build_discord_message(tiers_games_dict)

    send_discord_message(new_bundle, message)


def build_discord_message(tiers_games_dict):
    message = ""
    for key, value in tiers_games_dict.items():
        message += '***' + key + '***\n' + '\n'.join([str(i) for i in value]) + '\n\n'

    return message


def send_discord_message(new_bundle, games_list):
    webhook = Webhook.from_url(
        "https://discord.com/api/webhooks/1008066237609300080/"
        "xT7HplJknPuhiSALuKcttf2PTH7hbf8ZDLQ0vn86SGlKQutvT-vlzZHWrssR7w0kwAnB", adapter=RequestsWebhookAdapter())

    webhook.send(content=new_bundle,
                 avatar_url="https://cdn.humblebundle.com/static/hashed/03de04a2224923e1ff35c11a3a1cd0e675b5003e.png")

    embed = discord.Embed(title="Games in this bundle by tier:", description=games_list, color=0xd0011b)
    webhook.send(embed=embed)


def search_humble():
    driver.get("https://www.humblebundle.com/games")
    # Give the page a chance to fully load before searching
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='info-section']")))
    bundles = driver.find_elements(By.XPATH, "//div[@class='info-section']")

    built_bundles = [["" for i in range(2)] for i in range(len(bundles))]
    pos = 0  # position of cursor in 'links' list
    for bundle in bundles:
        built_bundles[pos][0] = ("https://www.humblebundle.com" + bundle.get_attribute('href').split("?")[0])
        built_bundles[pos][1] = bundle.text.split("\n")[0]
        pos += 1

    pos = 0
    for bundle in built_bundles:
        bundle_link = bundle[0]
        bundle_title = bundle[1]
        cur.execute("SELECT COUNT(*) FROM humbleBundles WHERE name = %s OR link = %s;",
                    (bundle_link, bundle_title))

        exists = cur.fetchone()[0]

        if exists == 0:
            print("New bundle " + bundle_title.lower() + " found!")

            get_list_of_games(bundle_link)

            # Save the new bundle in the database so that it is ignored next time.
            cur.execute("INSERT INTO humblebundles "
                        "VALUES (%s, %s);",
                        (bundle_title, bundle_link))
            conn.commit()
        else:
            print(bundle_title + " already found...")
        pos += 1


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')

    db = config['Credentials']['database_name']
    user = config['Credentials']['database_username']
    password = config['Credentials']['database_pass']

    print('Connecting to the PostgreSQL database...')
    conn = psycopg2.connect(dbname=db, user=user, password=password)

    # Create a cursor - DB will execute a statement, then keep the result stored in DB memory
    cur = conn.cursor()

    print('PostgreSQL database version: ', end='')
    cur.execute('SELECT version()')

    db_version = cur.fetchone()
    print(db_version)

    search_humble()

    try:
        cur.close()
        print('Database connection closed')
    except Exception as err:
        print('Uh oh, an error occurred: ' + err)
    finally:
        driver.quit()
        print('Finished :)')


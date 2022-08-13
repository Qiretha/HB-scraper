# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from discord import Webhook, RequestsWebhookAdapter


def send_discord_message(new_bundle):
    webhook = Webhook.from_url(
        "https://discord.com/api/webhooks/1008066237609300080/"
        "xT7HplJknPuhiSALuKcttf2PTH7hbf8ZDLQ0vn86SGlKQutvT-vlzZHWrssR7w0kwAnB", adapter=RequestsWebhookAdapter())
    webhook.send(content=new_bundle)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import psycopg2

    print('Connecting to the PostgreSQL database...')
    conn = psycopg2.connect("dbname=hbwatcher user=hbpython password=hbPython")

    # Create a cursor - DB will execute a statement, then keep the result stored in DB memory
    cur = conn.cursor()

    print('PostgreSQL database version: ', end='')
    cur.execute('SELECT version()')

    db_version = cur.fetchone()
    print(db_version)

    with webdriver.Firefox() as driver:
        driver.get("https://www.humblebundle.com/games")
        # Give the page a chance to fully load before searching
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='info-section']")))
        bundles = driver.find_elements(By.XPATH, "//div[@class='info-section']")

        links = []
        pos = 0  # position of cursor in 'links' list

        for bundle in bundles:
            # Build the link, removing the referral additions in the href
            bundle_link = "https://www.humblebundle.com" + bundle.get_attribute('href').split("?")[0]
            links.append(bundle_link)

            bundle_title = bundle.text.split("\n")[0]

            cur.execute("SELECT COUNT(*) FROM humbleBundles WHERE name = %s OR link = %s;", (bundle_title, links[pos]))

            exists = cur.fetchone()[0]

            if exists == 0:
                # Discord message
                send_discord_message(bundle_link)

                # Save the new bundle in the database so that it is ignored next time.
                cur.execute("INSERT INTO humblebundles "
                            "VALUES (%s, %s);",
                            (bundle_title, bundle_link))
                conn.commit()
            else:
                print(bundle_title + " already exists...")
            pos += 1
    try:
        cur.close()
        print('Database connection closed')
    except Exception as err:
        print('Uh oh, an error occurred: ' + err)
    finally:
        print('Finished :)')


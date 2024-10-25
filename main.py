from selenium import webdriver
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller
import time

print('Устанавливаю драйвер..')
chromedriver_autoinstaller.install()
driver = webdriver.Chrome()

print('Запускаю браузер..')
driver.get('https://vk.com/it_roll')

print('Жду прогрузки страницы..')

input(f'\n\n\n\n\n\n{"-" * 55}\nТеперь войдите в аккаунт и нажмите Enter в терминале..\n{"-" * 55}\n\n\n\n\n\n')
totalEnvelopeCount = 0

def countEnvelopeComments():
    count = 0
    comments = driver.find_elements(By.CSS_SELECTOR, '.wall_reply_text')
    for comment in comments:
        if "энвилоуп" in comment.text.lower():
            count += 1
    return count

def scrollToBottom():
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

previousPosts = set()

while True:
    posts = driver.find_elements(By.CSS_SELECTOR, '[id^="post-"]')
    currentPosts = [post.get_attribute("id").replace("post-", "") for post in posts]
    newPosts = set(currentPosts) - previousPosts

    if not newPosts:
        print('Посты закончились, загружаю новые..')
        
        scrollToBottom()
        posts = driver.find_elements(By.CSS_SELECTOR, '[id^="post-"]')
        currentPosts = [post.get_attribute("id").replace("post-", "") for post in posts]
        newPosts = set(currentPosts) - previousPosts
        
        if not newPosts:
            print("Нет новых постов для анализа. Завершение работы.")
            break
        
        driver.find_element(By.CSS_SELECTOR, 'div.wk_close_inner').click()
        time.sleep(2)
        continue

    for index, post_id in enumerate(newPosts):
        post_url = f'https://vk.com/it_roll?w=wall-{post_id}'
        print(f'Открываю пост {index + 1} из {len(newPosts)} | ID: {post_id}')
        driver.get(post_url)
        time.sleep(2)

        scrollToBottom()

        envelopeCount = countEnvelopeComments()
        totalEnvelopeCount += envelopeCount
        print(f'Количество "энвилоуп" в комментариях поста {post_id}: {envelopeCount} | Всего найдено: {totalEnvelopeCount}')

    previousPosts.update(newPosts)

print("Завершение работы.")
driver.quit()

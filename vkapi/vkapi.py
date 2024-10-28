import asyncio
import aiohttp
import time
from config import TOKEN

GROUP_ID = 218375169
WORD_TO_COUNT = "энвилоуп"
POSTS_PER_REQUEST = 100
COMMENTS_PER_REQUEST = 100
BATCH_SIZE = 12

async def fetch_comments_and_count(session, post_id, group_id, word):
    async with session.get(f'https://api.vk.com/method/wall.getComments', params={
        'owner_id': -group_id,
        'post_id': post_id,
        'count': COMMENTS_PER_REQUEST,
        'access_token': TOKEN,
        'v': '5.199'
    }) as response:
        comments_data = await response.json()
        
    comments = comments_data.get("response", {}).get("items", [])
    count = sum(comment["text"].lower().count(word.lower()) for comment in comments)
    return count

async def fetch_posts(session, group_id, offset):
    async with session.get(f'https://api.vk.com/method/wall.get', params={
        'owner_id': -group_id,
        'count': POSTS_PER_REQUEST * 2,
        'offset': offset,
        'access_token': TOKEN,
        'v': '5.199'
    }, headers={
        'Connection': 'keep-alive',
        'Upgrade': 'h2c'
    }) as response:
        data = await response.json()
        
    return data

async def count_word_mentions(word, group_id):
    async with aiohttp.ClientSession() as session:
        mention_count = 0
        offset = 0

        while True:
            batch_tasks = [fetch_posts(session, group_id, offset + i * POSTS_PER_REQUEST) for i in range(BATCH_SIZE)]
            batch_results = await asyncio.gather(*batch_tasks)

            all_posts = []
            for result in batch_results:
                posts = result.get("response", {}).get("items", [])
                if posts:
                    all_posts.extend(posts)

            if not all_posts:
                break

            count_tasks = [fetch_comments_and_count(session, post["id"], group_id, word) for post in all_posts]
            results = await asyncio.gather(*count_tasks)

            batch_mention_count = sum(results)
            mention_count += batch_mention_count
            
            offset += POSTS_PER_REQUEST * BATCH_SIZE

        return mention_count

def main(i):
    start_time = time.time()
    
    mention_count = asyncio.run(count_word_mentions(WORD_TO_COUNT, GROUP_ID))
    
    end_time = time.time()
    duration = end_time - start_time

    print(f"------{i + 1}/10------\n'{WORD_TO_COUNT}' упомянуто {mention_count} раз.")
    print(f"Время выполнения: {duration:.2f} секунд.")
    
    return duration

if __name__ == "__main__":
    print('[Запущено]')
    total_duration = 0

    for i in range(10):
        duration = main(i)
        total_duration += duration

    average_duration = total_duration / 10
    print(f"Среднее время выполнения: {average_duration:.2f} секунд.")

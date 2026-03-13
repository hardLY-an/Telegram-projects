import requests
from telethon import functions, types
from telethon.sync import TelegramClient
import time

# Enter details
api_id = None
api_hash = None
#

changed_counter = 0

#chekking time
update_time = time.time()+5
while True:
    #print(time.time())
    if time.time() >= update_time:
        # getting new photo for avatar
        url_search = 'https://api.waifu.im/search'
        params = {
            'included_tags': ['waifu'],
            'height': '>=1000',
            'byte_size': '<=5242880'
        }

        response = requests.get(url_search, params=params)

        if response.status_code == 200:
            data = response.json()
            # Process the response data as needed
        else:
            print('Request failed with status code:', response.status_code)

        url_photo = str(data['images'][0]['url'])
        res = requests.get(url_photo)
        with open('img.jpg', 'wb') as f:
            f.write(res.content)
        # end

        # Updating avatar
        with TelegramClient('anon', api_id, api_hash) as client:
            result = client(functions.photos.UploadProfilePhotoRequest(
                file=client.upload_file('img.jpg'),
            ))
        update_time = time.time()+30
        # end
        print("Successfully changed")
        changed_counter += 1
        print("change counter =", changed_counter)

    else:
        time.sleep(5)

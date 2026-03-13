import requests
import telepot
import time


bot = telepot.Bot("Enter your bot id")

send_time = time.time()+1
sent_counter = 0
url_photo = ''
included_tags = ['waifu']

while True:
    if time.time() >= send_time:
        print("url =", url_photo)
        # getting new photo for sending
        url_search = 'https://api.waifu.im/search'
        params = {
            'included_tags': included_tags,
            'height': '>=1000',
            'byte_size': '<=9437184',
            'is_nsfw': 'false'
        }

        response = requests.get(url_search, params=params)

        if response.status_code == 200:
            data = response.json()
            # Process the response data as needed
            url_photo = str(data['images'][0]['url'])

            # saving photo to local file
            res = requests.get(url_photo)
            with open('name.jpg', 'wb') as f:
                f.write(res.content)
            time.sleep(1)

            # sending photo
            bot.sendPhoto('enter channel', photo=open('name.jpg','rb'))
            sent_counter += 1
            print("Successfully sent")
            print("sent counter =", sent_counter)
            send_time = time.time() + 20   

        else:
            print('Request failed with status code:', response.status_code)
            send_time = time.time() + 5
    else:
        time.sleep(5)

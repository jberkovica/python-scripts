import requests
import time
from datetime import datetime
import random
import string


manifests = []
counter = 1
req_amount = 10

while counter < req_amount:
    for man in manifests:

        current_time = datetime.now().strftime("%H:%M:%S")
        letters = string.ascii_letters
        request_id = ''.join(random.choice(letters) for i in range(10))

        headers = {
            'User-Agent': 'Request N: {} ID: {}'.format(counter, request_id)
        }

        response = requests.get(man, headers=headers)
        print(current_time, headers, man, response, str(response.content))
        counter += 1

        time.sleep(5)

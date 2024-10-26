import requests
from datetime import datetime
import re
import time

# Sõnastik numbrite sõnaliste väljenduste jaoks
number_words = {
    "üks": 1,
    "kaks": 2,
    "kolm": 3,
    "neli": 4,
    "viis": 5,
    "kuus": 6,
    "seitse": 7,
    "kaheksa": 8,
    "üheksa": 9,
    "kümme": 10,
    "sada": 100,
    "tuhat": 1000
}

def words_to_number(text):
    words = text.split()
    total = 0
    for word in words:
        if word in number_words:
            total += number_words[word]
    return total

# Uus juurdepääsuluba ja albumi ID
access_token = 'EAB9JtNHpnzsBOwZARrMWFlzWgpfzIhlrJKq85ZAX5VjC5ZBvd4PygX8wC7sYGJbEisMoTHIKqAnfx6R5u1fmMmLZBiDMg6HJB4eNDoF9ZAoaDdCNliSG8N6BAt0fOvnibrqbGGs4ZBWKPK7BbwqbhtLENWQZAX5x2KfINFfI7oJOFRUCeEvAtRjmb5t3H1m8yp7OuZBqZBxthkG6ZB8ZC0ZCTUy9IZCoFKpx5LczeKIGbTB8O'
album_id = '122117217290543694'  # Lisatud sinu albumi ID

# Regulaaravaldis pakkumise ja kuupäeva leidmiseks
bid_pattern = re.compile(r'(\d+[.,]?\d*)')  # Otsib numbreid, mis võivad sisaldada koma või punkti
date_pattern = re.compile(r'LÕPP (\d{2})\.(\d{2})\.(\d{2}) KL (\d{2}):(\d{2})')  # Otsib kuupäeva formaadis "LÕPP dd.mm.yy KL hh:mm"

# Mälu, et hoida kõrgeimat pakkumist
photo_memory = {}

def update_highest_bid():
    print(f"Kontrollin pakkumisi kell {datetime.now()}")

    photos_url = f"https://graph.facebook.com/v12.0/{album_id}/photos"
    photos_response = requests.get(photos_url, params={'access_token': access_token})
    
    if photos_response.status_code != 200:
        print(f"Viga fotode päringus: {photos_response.status_code}")
        return
    
    photos = photos_response.json().get('data', [])
    print(f"Leitud fotosid: {len(photos)}")

    for photo in photos:
        photo_id = photo['id']
        
        # Kui mälu ei ole, algata
        if photo_id not in photo_memory:
            photo_memory[photo_id] = {'highest_bid': 0}

        highest_bid = photo_memory[photo_id]['highest_bid']

        # Loe foto pealkiri, et saada lõppkuupäev
        photo_details_url = f"https://graph.facebook.com/v12.0/{photo_id}"
        photo_details_response = requests.get(photo_details_url, params={'access_token': access_token, 'fields': 'name'})
        photo_details = photo_details_response.json()
        photo_caption = photo_details.get('name', '')
        
        # Leia lõppkuupäev pealkirjast
        date_match = date_pattern.search(photo_caption)
        if date_match:
            day, month, year, hour, minute = date_match.groups()
            year = int(year) + 2000  # Eeldame, et aastaarv on 2000+
            end_time = datetime(year, int(month), int(day), int(hour), int(minute))

        comments_url = f"https://graph.facebook.com/v12.0/{photo_id}/comments"
        comments_response = requests.get(comments_url, params={'access_token': access_token, 'fields': 'message,created_time,from{name}'})
        
        if comments_response.status_code != 200:
            print(f"Viga kommentaaride päringus foto ID-ga {photo_id}: {comments_response.status_code}")
            continue

        comments = comments_response.json().get('data', [])
        print(f"Foto ID-ga {photo_id} kommentaaride arv: {len(comments)}")

        # Leia kõrgeim pakkumine iga pildi kommentaaridest
        for comment in comments:
            message = comment['message']
            comment_id = comment['id']
            bid_match = bid_pattern.search(message)

            # Kui pakkumist ei leitud, jäta see kommentaar vahele
            if not bid_match:
                continue

            # Asenda koma punktiga, et teisendada arv floatiks
            bid = float(bid_match.group(1).replace(',', '.'))

            if highest_bid == 0 and bid < 2:
                # Esimene pakkumine peab olema vähemalt 2€
                response_message = f"Esimene pakkumine peab olema alghinnast vähemalt samm kõrgem."
                response_url = f"https://graph.facebook.com/v12.0/{comment_id}/comments"
                requests.post(response_url, data={'message': response_message, 'access_token': access_token})
            elif bid >= highest_bid + 1:
                # Uus kõrgeim pakkumine
                highest_bid = bid
                photo_memory[photo_id]['highest_bid'] = highest_bid

                # Kustuta vana kõrgeima pakkumise kommentaar
                for comment in comments:
                    if 'Kõrgeim pakkuja' in comment['message']:
                        delete_url = f"https://graph.facebook.com/v12.0/{comment['id']}"
                        requests.delete(delete_url, params={'access_token': access_token})

                # Uuenda kõrgeima pakkumise kommentaar
                update_message = f"Kõrgeim pakkuja {highest_bid}€ ning lõpp juba {end_time.strftime('%d.%m.%Y')} kl {end_time.strftime('%H:%M')}🌟Lõpphinnale lisandub käibemaks💫."
                update_url = f"https://graph.facebook.com/v12.0/{photo_id}/comments"
                post_response = requests.post(update_url, data={'message': update_message, 'access_token': access_token})
                if post_response.status_code == 200:
                    print(f"Uuendatud kommentaar postitatud foto ID-ga: {photo_id}")
                else:
                    print(f"Viga kommentaari postitamisel foto ID-ga {photo_id}: {post_response.status_code}")

            # Eemaldatud: vastamine eelmisele kõrgeimale pakkujale

# Korda funktsiooni iga 30 sekundi järel
while True:
    update_highest_bid()
    time.sleep(30)  # Oota 30 sekundit enne uuesti käivitamist
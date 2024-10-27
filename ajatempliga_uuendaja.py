import requests
import time
import json
from datetime import datetime, timedelta, timezone
import re

# Facebook Graph API seaded
access_token = 'EAAB0uDibqFABO9fgHhXRs2PkwSXrdfirAa9T72zFsjQ9DxPYZBo3RmBZCZCUekbhc6KbieEZCxOUNMbYLtmXhTtkGR9neiVZAsz1CkZCmOIeZCeZAE9Wtf3JRswBXYiY2eb4LIOoPZAcbaYrdSQgOswA4V6TMllbRcZBu9sBUumwEuG9b3BRX3Jio2ryKeZBzCY28bjS7R2DBDkA8EhESpQTMb2AkmHeiR3xkQfaTWfmv0B'  # Asenda oma kehtiva juurdepääsutunnusega
album_id = '576206708407530'
page_id = '463324893829156'  # Asenda oma lehe ID-ga

# Fail, kuhu salvestada ajatemplid ja pakkumised
data_file = 'bids_data.json'

# Funktsioon sõnade teisendamiseks numbriteks
def words_to_numbers(word):
    numbers = {
        'üks': 1, 'kaks': 2, 'kolm': 3, 'neli': 4, 'viis': 5,
        'kuus': 6, 'seitse': 7, 'kaheksa': 8, 'üheksa': 9, 'kümme': 10,
        'üksteist': 11, 'kaksteist': 12, 'kolmteist': 13, 'neliteist': 14, 'viisteist': 15,
        'kuusteist': 16, 'seitseteist': 17, 'kaheksateist': 18, 'üheksateist': 19, 'kakskümmend': 20,
        # Lisa kõik numbrid kuni sajani
    }
    return numbers.get(word.lower(), None)

# Kontroll, kas sõnum on potentsiaalne pakkumine
def is_valid_bid_message(message):
    excluded_phrases = [
        "hetke kõrgeim pakkumine",
        "oksjoni lõpp",
        "lõpphinnale lisandub",
        "kõik neljapäeval lõppevad oksjonid"
    ]

    if "http://" in message or "https://" in message:
        return False

    for phrase in excluded_phrases:
        if phrase in message.lower():
            return False

    return True

# Andmete laadimine failist
def load_data():
    try:
        with open(data_file, 'r') as f:
            data = json.load(f)
            for photo_id in data.get('end_times', {}):
                if isinstance(data['end_times'][photo_id], str):
                    data['end_times'][photo_id] = datetime.strptime(data['end_times'][photo_id], '%Y-%m-%d %H:%M:%S')
            return data
    except FileNotFoundError:
        return {'highest_bids': {}, 'comments': {}, 'end_times': {}, 'replied_comments': set()}

# Andmete salvestamine faili
def save_data(data):
    for photo_id in data['end_times']:
        if isinstance(data['end_times'][photo_id], datetime):
            data['end_times'][photo_id] = data['end_times'][photo_id].strftime('%Y-%m-%d %H:%M:%S')
    data['replied_comments'] = list(data['replied_comments'])
    with open(data_file, 'w') as f:
        json.dump(data, f)

# Kommentaarile vastamine
def reply_to_comment(comment_id, message):
    url = f"https://graph.facebook.com/v12.0/{comment_id}/comments"
    params = {
        'access_token': access_token,
        'message': message
    }
    response = requests.post(url, params=params)
    if response.status_code == 200:
        print(f"Vastatud kommentaarile ID-ga {comment_id}: {message}")
    else:
        print(f"Viga kommentaari ID-ga {comment_id} vastamisel: {response.json().get('error', {}).get('message', 'Tundmatu viga')}")

# Uue kommentaari postitamine
def post_comment(photo_id, message):
    url = f"https://graph.facebook.com/v12.0/{photo_id}/comments"
    params = {
        'access_token': access_token,
        'message': message
    }
    response = requests.post(url, params=params)
    if response.status_code == 200:
        comment_id = response.json().get('id')
        print(f"Postitatud kommentaar: {message}")
        return comment_id
    else:
        print(f"Viga kommentaari postitamisel: {response.json().get('error', {}).get('message', 'Tundmatu viga')}")
    return None

# Kommentaari kustutamine
def delete_comment(comment_id):
    if comment_id is None:
        return
    url = f"https://graph.facebook.com/v12.0/{comment_id}"
    params = {
        'access_token': access_token
    }
    response = requests.delete(url, params=params)
    if response.status_code == 200:
        print(f"Kustutatud eelmise kõrgeima pakkumise kommentaar ID-ga: {comment_id}")
    else:
        print(f"Viga kommentaari kustutamisel: {response.json().get('error', {}).get('message', 'Tundmatu viga')}")

# Kommentaaride ja vastuste saamine ja töötlemine
def get_album_comments():
    print("Alustan kommentaaride ja vastuste saamist...")
    url = f'https://graph.facebook.com/v12.0/{album_id}/photos'
    params = {
        'access_token': access_token,
        'fields': 'id,name,comments.summary(true){message,created_time,id,from,comments{message,created_time,id,from,parent}}',
        'limit': 25
    }
    next_page = True

    while next_page:
        response = requests.get(url, params=params)
        data = response.json()

        if 'error' in data:
            print(f"Tekkis viga: {data['error']['message']}")
            return

        stored_data = load_data()
        highest_bids = stored_data['highest_bids']
        comments_processed = stored_data['comments']
        end_times = stored_data.get('end_times', {})
        replied_comments = set(stored_data.get('replied_comments', []))

        for photo in data.get('data', []):
            print(f"Töötlen fotot ID-ga: {photo['id']}")
            photo_id = photo['id']
            comments = photo.get('comments', {}).get('data', [])
            photo_name = photo.get('name', '')

            # Kui lõppaeg pole määratud, siis määrame selle
            if photo_id not in end_times:
                end_date = extract_end_date(photo_name)
                if end_date:
                    end_times[photo_id] = end_date
                else:
                    # Määra vaikimisi lõppaeg, kui seda pole pealkirjas
                    end_times[photo_id] = datetime.now() + timedelta(days=1)  # Näiteks 1 päev pärast praegust aega

            # Kontrollime, kas oksjon on endiselt käimas
            current_time = datetime.now()
            if current_time > end_times[photo_id]:
                print(f"Oksjon ID-ga {photo_id} on lõppenud.")
                # Vasta ainult kehtivatele pakkumistele, mis on tehtud pärast lõppaega
                for comment in comments:
                    comment_time = datetime.strptime(comment['created_time'], '%Y-%m-%dT%H:%M:%S%z').astimezone(timezone.utc).replace(tzinfo=None)
                    comment_time += timedelta(hours=2)  # Lisa ajavööndi korrigeerimine
                    print(f"Kommentaari aeg: {comment_time}, Oksjoni lõppaeg: {end_times[photo_id]}")
                    if is_valid_bid_message(comment['message']):
                        print(f"Kehtiv pakkumine: {comment['message']}")
                    if comment['id'] not in replied_comments:
                        print(f"Kommentaari ID: {comment['id']} ei ole veel vastatud.")
                    if comment_time > end_times[photo_id]:
                        print(f"Kommentaari aeg on pärast oksjoni lõppemist.")
                    if is_valid_bid_message(comment['message']) and comment['id'] not in replied_comments and comment_time > end_times[photo_id]:
                        print(f"Vastan kommentaarile ID-ga: {comment['id']}")
                        reply_to_comment(comment['id'], "Kahjuks on antud oksjon juba lõppenud!")
                        replied_comments.add(comment['id'])
                continue

            # Kui kõrgeim pakkumine pole määratud, siis algväärtustame selle
            if photo_id not in highest_bids:
                highest_bids[photo_id] = {'amount': 0, 'comment_id': None}

            comments.sort(key=lambda x: x['created_time'])

            highest_bid = highest_bids[photo_id]
            highest_bid_updated = False

            # Kontrollime, kas kõrgeima pakkumise kommentaar on juba olemas
            today_date = datetime.now().strftime('%d.%m.%y')
            end_date_str = end_times[photo_id].strftime('%d.%m.%y')
            if end_date_str == today_date:
                end_date_display = "TÄNA"
            else:
                end_date_display = end_date_str

            # Uuenda kõrgeimat pakkumist
            for comment in comments:
                highest_bid_updated = process_comment(comment, photo_id, highest_bid, highest_bid_updated, comments_processed, end_times, replied_comments)

                replies = comment.get('comments', {}).get('data', [])
                for reply in replies:
                    highest_bid_updated = process_comment(reply, photo_id, highest_bid, highest_bid_updated, comments_processed, end_times, replied_comments)

            if highest_bid_updated:
                highest_bid_message = f"Kõrgeim pakkuja {highest_bid['amount']}€ ning lõpp juba {end_date_display} kl {end_times[photo_id].strftime('%H:%M')}🌟Lõpphinnale lisandub 22%💫."

                if not any(comment['message'] == highest_bid_message for comment in comments):
                    highest_bid['comment_id'] = post_comment(photo_id, highest_bid_message)
                    print(f"Postitatud kõrgeima pakkumise kommentaar: {highest_bid_message}")

            highest_bids[photo_id] = highest_bid

        stored_data['highest_bids'] = highest_bids
        stored_data['comments'] = comments_processed
        stored_data['end_times'] = end_times
        stored_data['replied_comments'] = replied_comments
        save_data(stored_data)

        next_page = 'paging' in data and 'next' in data['paging']
        if next_page:
            url = data['paging']['next']

    print("Kommentaaride töötlemine lõpetatud.")

# Kommentaari töötlemine
def process_comment(comment, photo_id, highest_bid, highest_bid_updated, comments_processed, end_times, replied_comments):
    message = comment['message']
    created_time = comment['created_time']
    comment_id = comment['id']

    # Kontrollime, kas 'from' väli on olemas ja kas kommentaar on meie enda loodud
    commenter_id = comment.get('from', {}).get('id', None)
    if commenter_id == page_id:
        print(f"Jätan vahele meie enda loodud kommentaari ID-ga: {comment_id}")
        return highest_bid_updated

    current_time = datetime.strptime(created_time, '%Y-%m-%dT%H:%M:%S%z').astimezone(timezone.utc).replace(tzinfo=None)
    current_time += timedelta(hours=2)

    # Kontrollime, kas oksjon on lõppenud
    if current_time > end_times[photo_id]:
        reply_message = "Kahjuks on antud oksjon juba lõppenud!"
        if is_valid_bid_message(message) and comment_id not in replied_comments:
            if not any(reply.get('message') == reply_message for reply in comment.get('comments', {}).get('data', [])):
                print(f"Oksjon on lõppenud. Kommentaarile '{message}' vastatakse sõnumiga: {reply_message}")
                reply_to_comment(comment_id, reply_message)
                replied_comments.add(comment_id)
        return highest_bid_updated

    today_date = datetime.now().strftime('%d.%m.%y')
    end_date_str = end_times[photo_id].strftime('%d.%m.%y')
    if end_date_str == today_date:
        end_date_display = "TÄNA"
    else:
        end_date_display = end_date_str

    highest_bid_message = f"Kõrgeim pakkuja {highest_bid['amount']}€ ning lõpp juba {end_date_display} kl {end_times[photo_id].strftime('%H:%M')}🌟Lõpphinnale lisandub 22%💫."
    if message == highest_bid_message:
        print(f"Jätan vahele meie enda loodud kõrgeima pakkumise kommentaari ID-ga: {comment_id}")
        return highest_bid_updated

    print(f"Kommentaar: '{message}' tehti ajal: {created_time}")
    if created_time not in comments_processed:
        bid = extract_bid_from_message(message)
        if bid is not None:
            if bid < 1:
                reply_message = "Pakkumine peab olema vähemalt 1 euro!"
                if comment_id not in replied_comments and not any(reply.get('message') == reply_message for reply in comment.get('comments', {}).get('data', [])):
                    reply_to_comment(comment_id, reply_message)
                    replied_comments.add(comment_id)
            elif bid >= highest_bid['amount'] + 1:
                # Uuenda kõrgeimat pakkumist ainult siis, kui see vastab nõuetele
                # Kontrollime, et ei kustutaks vana pakkumist, kui uus pakkumine on vastusena
                if highest_bid['comment_id'] and comment.get('parent', {}).get('id') != highest_bid['comment_id']:
                    delete_comment(highest_bid['comment_id'])
                highest_bid['amount'] = bid
                highest_bid_updated = True

                if current_time > end_times[photo_id] - timedelta(minutes=10):
                    end_times[photo_id] = current_time + timedelta(minutes=10)
                    print(f"Pikendasin oksjoni lõppaega: {end_times[photo_id]}")

            else:
                next_bid = highest_bid['amount'] + 1
                reply_message = f"Pakkumise samm vähemalt 1 euro! Hetkel kõrgeim pakkumine {highest_bid['amount']} eurot ja järgmine pakkumine peab olema vähemalt {next_bid} eurot! :)"
                if comment_id not in replied_comments and not any(reply.get('message') == reply_message for reply in comment.get('comments', {}).get('data', [])):
                    reply_to_comment(comment_id, reply_message)
                    replied_comments.add(comment_id)

        comments_processed[created_time] = message
    return highest_bid_updated

# Pakkumise väljavõtmine sõnumist
def extract_bid_from_message(message):
    if not is_valid_bid_message(message):
        return None

    match = re.search(r'\d+(?:[.,]\d+)?', message)
    if match:
        bid_str = match.group(0).replace(',', '.')
        return float(bid_str)

    words = message.split()
    for word in words:
        number = words_to_numbers(word)
        if number is not None:
            return float(number)

    return None

# Lõppkuupäeva eraldamine pealkirjast
def extract_end_date(photo_name):
    try:
        start_index = photo_name.index('LÕPP') + 5
        end_index = photo_name.index('KL', start_index) + 8
        date_str = photo_name[start_index:end_index].strip()

        try:
            return datetime.strptime(date_str, '%d.%m.%Y KL %H:%M')
        except ValueError:
            return datetime.strptime(date_str, '%d.%m.%y KL %H:%M')
    except ValueError:
        return None

def main():
    while True:
        get_album_comments()
        time.sleep(120)

if __name__ == '__main__':
    main()
import requests
import json
from datetime import datetime, timedelta, timezone
import re

# URL, kust lugeda kommentaare
json_url = 'your_json_url_here'  # Asenda see oma tegeliku URL-iga

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

# Andmete laadimine HTTP-lingi kaudu
def load_comments_from_url(url):
    response = requests.get(url)
    response.raise_for_status()  # Tõsta erand, kui päring ebaõnnestub
    data = response.json()
    return data

# Kommentaaride töötlemine
def process_comments(data):
    highest_bids = {}
    comments_processed = {}
    end_times = {}
    replied_comments = set()

    for item in data['data']:
        photo_id = item['id']
        comments = item.get('comments', {}).get('data', [])
        photo_name = item.get('name', '')

        # Kui lõppaeg pole määratud, siis määrame selle
        if photo_id not in end_times:
            end_date = extract_end_date(photo_name)
            if end_date:
                end_times[photo_id] = end_date
            else:
                end_times[photo_id] = datetime.now() + timedelta(days=1)

        # Kontrollime, kas oksjon on endiselt käimas
        current_time = datetime.now()
        if current_time > end_times[photo_id]:
            print(f"Oksjon ID-ga {photo_id} on lõppenud.")
            for comment in comments:
                comment_time = datetime.strptime(comment['created_time'], '%Y-%m-%dT%H:%M:%S%z').astimezone(timezone.utc).replace(tzinfo=None)
                comment_time += timedelta(hours=3)
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

    # Andmete salvestamine (vajadusel)
    # save_data(stored_data)

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
    current_time += timedelta(hours=3)

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
    data = load_comments_from_url(json_url)
    process_comments(data)

if __name__ == '__main__':
    main()
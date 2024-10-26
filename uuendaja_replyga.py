import requests
import re

# Facebook Graph API seaded
access_token = 'EAAB0uDibqFABOxJ2NbHkt9Tq9VpgrrFc2OuEhrYg9aWBqA8TL0fQI5ivuYE6yOkWCR8ZArleQahPYZA3NsgNzSRTSs0zFAXZAzhuprCvZBFIpWj3fuNPEjJCSvKokJ3kWQE38G4SR1kSHmylHRy5LTaqJp3r6mdEZBLeMfZBfYzAoOZCzretWJm2tGdTcaV8RMgbZBxDqVjk3w4c2ZAMdEpY43xEDaMZBX9XeoUWmdQTvc'  # Asenda oma kehtiva juurdepääsutunnusega
album_id = '122116335080519348'

# Sõnalised numbrid ja nende vastavad väärtused
word_to_number = {
    'üks': 1, 'kaks': 2, 'kolm': 3, 'neli': 4, 'viis': 5,
    'kuus': 6, 'seitse': 7, 'kaheksa': 8, 'üheksa': 9, 'kümme': 10,
    'üksteist': 11, 'kaksteist': 12, 'kolmteist': 13, 'neliteist': 14, 'viisteist': 15,
    'kuusteist': 16, 'seitseteist': 17, 'kaheksateist': 18, 'üheksateist': 19, 'kakskümmend': 20,
    'kolmkümmend': 30, 'nelikümmend': 40, 'viiskümmend': 50, 'kuuskümmend': 60, 'seitsekümmend': 70,
    'kaheksakümmend': 80, 'üheksakümmend': 90, 'sada': 100
}

def convert_word_to_number(word):
    return word_to_number.get(word.lower(), None)

# Funktsioon, et saada albumi fotod
def get_album_photos():
    url = f"https://graph.facebook.com/v12.0/{album_id}/photos"
    params = {
        'access_token': access_token
    }
    response = requests.get(url, params=params)
    return response.json().get('data', [])

# Funktsioon, et saada foto kommentaarid
def get_photo_comments(photo_id):
    url = f"https://graph.facebook.com/v12.0/{photo_id}/comments"
    params = {
        'access_token': access_token
    }
    response = requests.get(url, params=params)
    return response.json().get('data', [])

# Peamine funktsioon, et leida kõrgeim pakkumine
def find_highest_bid():
    photos = get_album_photos()
    highest_bid = 0
    highest_bidder = None

    for photo in photos:
        comments = get_photo_comments(photo['id'])
        for comment in comments:
            # Kontrolli numbrilisi pakkumisi
            numeric_bid = re.findall(r'\d+', comment['message'])
            if numeric_bid:
                bid = int(numeric_bid[0])
            else:
                # Kontrolli sõnalisi pakkumisi
                words = comment['message'].split()
                bid = sum(convert_word_to_number(word) for word in words if convert_word_to_number(word) is not None)

            if bid > highest_bid:
                highest_bid = bid
                highest_bidder = comment['from']['name']

    print(f"Kõrgeim pakkumine on {highest_bid}€ pakkujalt {highest_bidder}.")

# Käivita funktsioon
find_highest_bid()
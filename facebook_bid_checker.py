import requests
import re
import time

# Juurdepääsuluba ja albumi ID
access_token = 'EAAB0uDibqFABO46n8AwsqvarbYsI7vfOg9zl0NudGaKGrnKpy0rQoTZBKbDc9UxZCbrjnulJ9FEPwBXmh2pN6zJZCe8pHxJU63NzZCOjlNwfWAq66Nb0mNpxrMeYf83Ro7wSwvhq7RcZCbozS7g1zcGAlfWfmuWYF47zG3kbd8wu5BsdJ6oV2eZBIVllGju75d1fT9kH5NZBu5o9u9rK5zxDYxZBJLOYGlihdwjsr4g4'
album_id = '122117217290543694'  # Lisatud sinu albumi ID

# Regulaaravaldis pakkumise leidmiseks
bid_pattern = re.compile(r'(\d+[.,]?\d*)')

# Mälu, et hoida kõrgeimat pakkumist ja juba vastatud kommentaare
photo_memory = {}
responded_comments = set()

def respond_to_invalid_bid(comment_id, message):
    if comment_id not in responded_comments:
        response_message = f"Palun tutvuge oksjoni reeglitega! {message}"
        response_url = f"https://graph.facebook.com/v12.0/{comment_id}/comments"
        requests.post(response_url, data={'message': response_message, 'access_token': access_token})
        print(f"Vastatud vigasele pakkumisele: {message}")
        responded_comments.add(comment_id)

def check_invalid_bids():
    print("Alustan pakkumiste kontrollimist...")
    photos_url = f"https://graph.facebook.com/v12.0/{album_id}/photos"
    photos_response = requests.get(photos_url, params={'access_token': access_token})
    
    if photos_response.status_code != 200:
        print(f"Viga fotode päringus: {photos_response.status_code}")
        return
    
    photos = photos_response.json().get('data', [])
    print(f"Leitud fotosid: {len(photos)}")

    for photo in photos:
        photo_id = photo['id']
        
        if photo_id not in photo_memory:
            photo_memory[photo_id] = {'highest_bid': 0}

        highest_bid = photo_memory[photo_id]['highest_bid']

        comments_url = f"https://graph.facebook.com/v12.0/{photo_id}/comments"
        comments_response = requests.get(comments_url, params={'access_token': access_token, 'fields': 'message,created_time,from{name}'}).json()
        
        comments = comments_response.get('data', [])
        print(f"Foto ID-ga {photo_id} kommentaaride arv: {len(comments)}")

        for comment in comments:
            message = comment['message']
            comment_id = comment['id']
            bid_match = bid_pattern.search(message)

            if not bid_match:
                respond_to_invalid_bid(comment_id, "Pakkumine peab sisaldama numbrilist väärtust.")
                continue

            bid = float(bid_match.group(1).replace(',', '.'))

            if bid < 2:
                respond_to_invalid_bid(comment_id, "Pakkumise samm vähemalt 1 euro ehk esimene pakkumine peab olema 2 eurot!")
            elif bid < highest_bid + 1:
                respond_to_invalid_bid(comment_id, f"Pakkumise samm vähemalt 1 euro ehk esimene pakkumine peab olema 2 eurot!")
            else:
                highest_bid = bid
                photo_memory[photo_id]['highest_bid'] = highest_bid
                print(f"Uus kõrgeim pakkumine: {highest_bid}€ foto ID-ga {photo_id}")

while True:
    check_invalid_bids()
    time.sleep(5)  # Oota 5 sekundit enne uuesti käivitamist
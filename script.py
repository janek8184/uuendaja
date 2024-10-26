import requests
from datetime import datetime
import re

# Sinu juurdepääsuluba ja albumi ID
access_token = 'EAB9JtNHpnzsBO0uYwIiuxxjCzlcI38ostn3ICDOagONaKYOouhZAHe50s0A9fS2wXvNZAZCmUSSvI53lh6JEPrP4uLY2Vq2mLvmd9c02lawzRmzrmGuYba1rx2BAHlbWSX8MZAYHjpx809cpc5AkFfpODbTe90g81NjZBFqPZBKIOPCgW17LwOgFBFVIf0zlbnf61GyT33avZACvqRXfELgfRrdMhmzZC257bSILMaZCo'
album_id = '122117217290543694'  # Lisatud sinu albumi ID

# API URL fotode saamiseks albumist
photos_url = f"https://graph.facebook.com/v12.0/{album_id}/photos"
photos_response = requests.get(photos_url, params={'access_token': access_token})
photos = photos_response.json().get('data', [])

# Regulaaravaldis kuupäeva ja kellaaja leidmiseks (nt "26.10.24 KL 21:00" formaadis)
date_pattern = re.compile(r'(\d{2})\.(\d{2})\.(\d{2}) KL (\d{2}):(\d{2})')

# Postita kommentaar igale fotole
for photo in photos:
    photo_id = photo['id']
    # Saa foto pealkiri
    photo_details_url = f"https://graph.facebook.com/v12.0/{photo_id}"
    photo_details_response = requests.get(photo_details_url, params={'fields': 'name', 'access_token': access_token})
    photo_details = photo_details_response.json()
    caption = photo_details.get('name', '')

    # Otsi kuupäeva ja kellaaega pealkirjast
    match = date_pattern.search(caption)
    if match:
        day, month, year, hour, minute = map(int, match.groups())
        year += 2000  # Kaheksakohalise aasta teisendamine neljakohaliseks
        end_time = datetime(year, month, day, hour, minute)
        now = datetime.now()
        time_remaining = end_time - now
        hours, remainder = divmod(time_remaining.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        # Teade, mis postitatakse
        message = f"Oksjoni lõpuni on jäänud: {time_remaining.days} päeva, {hours} tundi ja {minutes} minutit."

        # Leia ja kustuta vana kommentaar
        comments_url = f"https://graph.facebook.com/v12.0/{photo_id}/comments"
        comments_response = requests.get(comments_url, params={'access_token': access_token})
        comments = comments_response.json().get('data', [])
        for comment in comments:
            if 'Oksjoni lõpuni on jäänud' in comment['message']:
                delete_url = f"https://graph.facebook.com/v12.0/{comment['id']}"
                delete_response = requests.delete(delete_url, params={'access_token': access_token})
                if delete_response.status_code == 200:
                    print(f"Vana kommentaar kustutati foto ID-ga: {photo_id}")

        # Postita uus kommentaar
        comment_url = f"https://graph.facebook.com/v12.0/{photo_id}/comments"
        response = requests.post(comment_url, data={'message': message, 'access_token': access_token})
        if response.status_code == 200:
            print(f"Uus kommentaar postitati edukalt foto ID-ga: {photo_id}")
        else:
            print(f"Viga foto ID-ga {photo_id}: {response.json()}")
    else:
        print(f"Kuupäeva ei leitud foto ID-ga: {photo_id}")
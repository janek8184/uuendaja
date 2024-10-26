import requests

access_token = 'EAB9JtNHpnzsBO0czas8koHls7oXXy1W7usdUzIvCwjBpq7GcGXDMPva4ii2UuxRWcjdcl70cPuZCfmEnYtqX1GFcTNNg0SaGWfZCt2tZCjyPphNpUwiOuU6wTGL2MPU44K24fjzPwgy1e5ISEsNVv7ymIpruUUhLhBJZB1TcmDh7jbPCrmF2pkMRe7ChL4X9jATZASqmLguzCanjwZBLvtVBnxNBTI4I74KBR17bIJ'
album_id = '122117217290543694'

def delete_comments_from_album_photos(album_id, access_token):
    # Get all photos in the album
    url = f'https://graph.facebook.com/v11.0/{album_id}/photos'
    params = {'access_token': access_token}
    response = requests.get(url, params=params)
    photos = response.json().get('data', [])

    for photo in photos:
        photo_id = photo['id']
        # Get comments for each photo
        comments_url = f'https://graph.facebook.com/v11.0/{photo_id}/comments'
        comments_response = requests.get(comments_url, params=params)
        comments = comments_response.json().get('data', [])

        for comment in comments:
            comment_id = comment['id']
            # Delete each comment
            delete_url = f'https://graph.facebook.com/v11.0/{comment_id}'
            delete_response = requests.delete(delete_url, params=params)
            if delete_response.status_code == 200:
                print(f'Comment {comment_id} deleted successfully.')
            else:
                print(f'Failed to delete comment {comment_id}.')

delete_comments_from_album_photos(album_id, access_token)
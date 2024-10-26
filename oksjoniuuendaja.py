import time
import facebook  # Facebook SDK for Python
from datetime import datetime, timedelta
import re
import json
import os

# Facebook API seadistamine
access_token = 'EAAB0uDibqFABO0DlcCdLShzyxYfpsnt4bVLsi9hjO1sxOWucmNcDd9M7LjsTAByBUr0Fhw9CZBFIvnYWDDrj9MPSQjgGVKeoqsHN6gLPkyZCXj1i37ZCl88yCbZBpFUY7FIlE7d4Iwi5p0fyCGFTafbGVgeeq01TkuH8muN8ELKO0ySNPQLs67Av75FEYpG5o5WYUbtaCRE4PRrPcpYJ6uEHnW9ScgjhtHY2ZBDXB'
graph = facebook.GraphAPI(access_token)

# Albumi ja oksjoni parameetrid
album_id = '122117217290543694'
alghind = 1.0
pakkumise_samm = 1.0
salvestusfail = 'oksjon_andmed.json'

# Lae eelmised andmed failist
def lae_andmed():
    if os.path.exists(salvestusfail):
        with open(salvestusfail, 'r') as f:
            return json.load(f)
    else:
        return {'töödeldud_kommentaarid': set(), 'kõrgeimad_pakkumised': {}, 'eelmised_kõrgeimad_id': {}}

# Salvesta andmed faili
def salvesta_andmed():
    with open(salvestusfail, 'w') as f:
        json.dump({
            'töödeldud_kommentaarid': list(töödeldud_kommentaarid),
            'kõrgeimad_pakkumised': kõrgeimad_pakkumised,
            'eelmised_kõrgeimad_id': eelmised_kõrgeimad_id
        }, f)

# Algandmete laadimine
andmed = lae_andmed()
töödeldud_kommentaarid = set(andmed['töödeldud_kommentaarid'])
kõrgeimad_pakkumised = andmed['kõrgeimad_pakkumised']
eelmised_kõrgeimad_id = andmed['eelmised_kõrgeimad_id']

numbrid_sõnades = {
    "üks": 1, "kaks": 2, "kolm": 3, "neli": 4, "viis": 5,
    "kuus": 6, "seitse": 7, "kaheksa": 8, "üheksa": 9, "kümme": 10,
    "üksteist": 11, "kaksteist": 12, "kolmteist": 13, # ja nii edasi kuni sajani
    "üheksakümmend üheksa": 99, "sada": 100
}

def leia_kuupäev_ja_kellaaeg(pealkiri):
    # Otsime kuupäeva ja kellaaega pealkirjast
    lõpp_kuupäev_match = re.search(r"LÕPP (\d{2}\.\d{2}\.\d{2}) KL (\d{2}:\d{2})", pealkiri)
    if lõpp_kuupäev_match:
        kuupäev_str = lõpp_kuupäev_match.group(1)
        kellaaeg_str = lõpp_kuupäev_match.group(2)
        print(f"Leitud kuupäev: {kuupäev_str}, kellaaeg: {kellaaeg_str}")
        # Kuupäeva ja kellaaja teisendamine datetime objektiks
        oksjoni_lõpp = datetime.strptime(f"{kuupäev_str} {kellaaeg_str}", "%d.%m.%y %H:%M")
        return oksjoni_lõpp
    else:
        print("Kuupäeva ja kellaaja andmeid ei leitud.")
        return None

def loe_piltide_kommentaare():
    print("Piltide kommentaaride lugemine algab.")
    try:
        photos = graph.get_connections(album_id, 'photos')
        if 'data' in photos:
            for photo in photos['data']:
                photo_id = photo['id']
                # Tuvasta oksjoni lõpp iga foto pealkirjast
                oksjoni_lõpp = leia_kuupäev_ja_kellaaeg(photo['name'])
                if not oksjoni_lõpp:
                    continue  # Kui lõppaja tuvastamine ebaõnnestub, jätka järgmise fotoga
                print(f"Loe kommentaare pildilt ID: {photo_id}")
                comments = graph.get_connections(photo_id, 'comments')
                if 'data' in comments:
                    for comment in comments['data']:
                        comment_id = comment['id']
                        if comment_id in töödeldud_kommentaarid:
                            continue  # Jätka, kui kommentaar on juba töödeldud
                        print(f"Loe kommentaar: {comment['message']}")
                        pakkumine = tuvastapakkumine(comment['message'])
                        if pakkumine is not None:
                            print(f"Tuvastatud pakkumine: {pakkumine}€ kommentaarist: {comment['message']}")
                            töötle_pakkumine(pakkumine, comment_id, photo_id, oksjoni_lõpp)
                        else:
                            print(f"Tehti kommentaar, mida ei õnnestunud tuvastada kui pakkumist: {comment['message']}")
                        töödeldud_kommentaarid.add(comment_id)  # Lisa kommentaar töödeldud komplekti
                else:
                    print("Kommentaaride andmeid ei leitud pildilt.")
        else:
            print("Pilte ei leitud albumist.")
    except Exception as e:
        print(f"Viga API päringus: {e}")

def tuvastapakkumine(tekst):
    try:
        pakkumine = float(tekst.replace(',', '.'))
        print(f"Tuvastatud numbriline pakkumine: {pakkumine}")
        return pakkumine
    except ValueError:
        for sõna, number in numbrid_sõnades.items():
            if sõna in tekst:
                print(f"Tuvastatud sõnaline pakkumine: {number}")
                return float(number)
    print("Pakkumist ei tuvastatud.")
    return None

def töötle_pakkumine(pakkumine, comment_id, photo_id, oksjoni_lõpp):
    global kõrgeimad_pakkumised, eelmised_kõrgeimad_id

    # Kui foto jaoks pole veel kõrgeimat pakkumist määratud, algväärtusta see alghinnaga
    if photo_id not in kõrgeimad_pakkumised:
        kõrgeimad_pakkumised[photo_id] = alghind

    kõrgeim_pakkumine = kõrgeimad_pakkumised[photo_id]

    if pakkumine < alghind + pakkumise_samm and kõrgeim_pakkumine == alghind:
        vastus = "Esimene pakkumine peab olema alghinnast vähemalt sammu võrra kõrgem!"
        print(f"Vastamine valele pakkumisele: {vastus}")
        vasta_kommentaarile(comment_id, vastus)
    elif pakkumine < kõrgeim_pakkumine + pakkumise_samm:
        vastus = f"Pakkumise samm vähemalt {pakkumise_samm} euro! Hetkel kõrgeim pakkuja {kõrgeim_pakkumine} eurot, järgmine pakkumine peab olema vähemalt {kõrgeim_pakkumine + pakkumise_samm} eurot!"
        print(f"Vastamine valele pakkumisele: {vastus}")
        vasta_kommentaarile(comment_id, vastus)
    elif pakkumine == kõrgeim_pakkumine:
        vastus = f"{kõrgeim_pakkumine} eurot on juba pakutud! Järgmine pakkumine peab olema vähemalt {kõrgeim_pakkumine + pakkumise_samm} eurot!"
        print(f"Vastamine samale pakkumisele: {vastus}")
        vasta_kommentaarile(comment_id, vastus)
    elif pakkumine > kõrgeim_pakkumine:
        if photo_id in eelmised_kõrgeimad_id:
            print(f"Kustutamine eelmine kõrgeim pakkumine kommentaar ID: {eelmised_kõrgeimad_id[photo_id]}")
            kustuta_kommentaar(eelmised_kõrgeimad_id[photo_id])
        kõrgeimad_pakkumised[photo_id] = pakkumine
        eelmised_kõrgeimad_id[photo_id] = postita_kommentaar(photo_id, f"Uus kõrgeim pakkumine {pakkumine}€! Lõpp juba {oksjoni_lõpp.strftime('%d.%m.%Y kl %H:%M')}🌟Lõpphinnale lisandub käibemaks💫.")
        print(f"Postitatud uus kõrgeim pakkumine: {pakkumine}€")
        oksjoni_lõpp += timedelta(minutes=10)  # Pikenda lõppu

def postita_kommentaar(photo_id, tekst):
    try:
        comment = graph.put_comment(object_id=photo_id, message=tekst)
        print(f"Kommentaar postitatud: {tekst}")
        return comment['id']
    except Exception as e:
        print(f"Viga kommentaari postitamisel: {e}")
        return None

def vasta_kommentaarile(comment_id, vastus):
    try:
        graph.put_comment(object_id=comment_id, message=vastus)
        print(f"Vastus kommentaarile {comment_id}: {vastus}")
    except Exception as e:
        print(f"Viga vastamisel: {e}")

def kustuta_kommentaar(comment_id):
    try:
        graph.delete_object(id=comment_id)
        print(f"Kommentaar {comment_id} kustutatud.")
    except Exception as e:
        print(f"Viga kommentaari kustutamisel: {e}")

try:
    while True:
        loe_piltide_kommentaare()
        salvesta_andmed()  # Salvesta andmed iga tsükli järel
        time.sleep(5)
except KeyboardInterrupt:
    salvesta_andmed()  # Salvesta andmed, kui skript katkestatakse
    print("Skript peatatud, andmed salvestatud.")
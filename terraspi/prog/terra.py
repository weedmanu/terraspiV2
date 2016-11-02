#! /usr/bin/env python
#-*- coding: utf-8 -*-

# import des librairies
import json
import MySQLdb
import sys
import Adafruit_DHT
import csv
import ephem
import datetime
import time
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

    
GPIO.setup(4, GPIO.OUT)  # lumiere
GPIO.setup(17, GPIO.OUT)  # chauffage

# on ouvre le fichier config .json
with open('/var/www/html/terraspi/csv/bdd.json') as config:    
    config = json.load(config)
    
login = config["mysql"]["loginmysql"]
mdp = config["mysql"]["mdpmysql"]

db = MySQLdb.connect(host="localhost", 
                     user=login,     
                     passwd=mdp, 
                     db="Terrarium")  
cur = db.cursor()
cur.execute("SELECT * FROM config")

for row in cur.fetchall():
    longitude = row[3]
    latitude = row[4]
    altitude = row[5]
    jour = row[8]
    nuit = row[9]
    HeureEI = row[15]

db.close()

# ici on régle en fonction des coordonnées de sa ville, ici: Gardanne 13120 france
somewhere = ephem.Observer()     
somewhere.lon = str(longitude)   #  longitude
somewhere.lat = str(latitude)
somewhere.elevation = int(altitude)   #  altitude 

# Heure actuelle ( du pi, GMT) convertie en chiffres
heurenow = int(time.strftime('%H%M'))


sun = ephem.Sun()
# r1 = heure lever soleil UTC
r1 = somewhere.next_rising(sun)
# s1 = heure coucher soleil UTC
s1 = somewhere.next_setting(sun)

# coucher = heure du coucher du soleil, en chiffres
# on commence par convertir l'heure de coucher en chiffres
# après avoir extrait les informations inutiles (date, etc.)
heurec = str(s1)
long = len(heurec)
fin = long - 8
heurec = heurec[fin:long-3]
coucher = int(heurec[0:2] + heurec[3:5])

# lever = heure du lever du soleil, en chiffres
# on commence par convertir l'heure de lever en chiffres
# après avoir extrait les informations inutiles (date, etc.)
heurel = str(r1)
long = len(heurel)
fin = long - 8
heurel = heurel[fin:long-3]
lever = int(heurel[0:2] + heurel[3:5])

lever = lever + HeureEI          #heure ete hiver
coucher = coucher + HeureEI


if lever < heurenow < coucher:    # si l'heure actuelle est comprise entre l'heure du lever et du coucher, s'il faut jour quoi.
  GPIO.output (4, True)            # on allume la lumière (on intervertira True et False suivant le branchement du relais  'normalement ouvert ou fermer'  )
  target = jour                    # on donne la consigne de jour comme temperature au point chaud
   
else:                                   
  GPIO.output (4, False)           # sinon on éteint la lumière
  target = nuit                    # on donne la consigne de nuit comme temperature au point chaud


fname1 = "/var/www/html/terraspi/csv/ephem.csv"    # on créer le fichier 
file1 = open(fname1, "wb")  
  
try:
    # Création de  CSV.
    writer1 = csv.writer(file1)
    # Écriture de la ligne d'en-tête avec le titre
    # des colonnes.
    writer1.writerow( ('lever' ,'coucher') )
    # Écriture des quelques données.
    writer1.writerow( (lever, coucher) )       

finally:    
    # Fermeture du fichier source
    file1.close()     
    
# on lit les sondes
humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 22)   #   point froid
humidityC, temperatureC = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 27)   #  point chaud

# on arrondi a 2 chiffres
humidity = round(humidity,2)                   
temperature = round(temperature,2)
humidityC = round(humidityC,2)
temperatureC = round(temperatureC,2)

# le controle du chauffage
if temperatureC > target:      # si la température du point chaud dépasse la target (nuit ou jour)
    GPIO.output (17, False)     # on coupe le chauffage
								# (on intervertira True et False suivant le branchement du relais 'normalement ouvert ou fermer')
else:
    GPIO.output (17, True)      # sinon on l'allume        

# on créer le fichier
fname = "/var/www/html/terraspi/csv/result.csv"    
file = open(fname, "wb")
 
try:
    # Création du CSV   
    writer = csv.writer(file)
    # Écriture de la ligne d'en-tête avec le titre
    # des colonnes.
    writer.writerow( ('Humidity' ,'Temperature') )
    # Écriture des quelques données.
    writer.writerow( (humidity, temperature) )
    writer.writerow( (humidityC, temperatureC) )       

finally:
    # Fermeture du fichier source    
    file.close()
    
sys.exit(1)

 

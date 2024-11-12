import http.server
import socketserver
from urllib.parse import urlparse, parse_qs, unquote
import json

from datetime import datetime
import sqlite3

import matplotlib.pyplot as plt
import matplotlib.dates as pltd

port_serveur = 8080


class RequestHandler(http.server.SimpleHTTPRequestHandler):
  static_dir = 'client'
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, directory=self.static_dir, **kwargs)
    

  def do_GET(self):
    self.init_params()
    if self.path_info[0] == 'stations_commune':
        self.send_stations_commune(self.path_info[1])    
    elif self.path_info[0] == 'stations':
      self.send_stations()

    elif self.path_info[0] == 'historique':
      self.send_historique()
    
    elif self.path_info[0] == 'somme_historique':
      self.send_somme_historique()
    
    elif self.path_info[0] == 'commune':
      self.send_commune()    
    else:
      super().do_GET()


  def send_stations(self):
    c = conn.cursor()
    
    c.execute("SELECT idstation,nom,lat,lon FROM 'stations-velov'")
    r = c.fetchall()
    body = json.dumps([{'idstation':id, 'nom':nom, 'lat':lat, 'lon': lon} 
                       for (id,nom,lat,lon) in r])    

    headers = [('Content-Type','application/json')];
    self.send(body,headers)
  
  def send_stations_commune(self,commune):
    c = conn.cursor()
    
    c.execute("SELECT idstation,nom,lat,lon FROM 'stations-velov' WHERE commune=?",(commune,))
    r = c.fetchall()
    body = json.dumps([{'idstation':id, 'nom':nom, 'lat':lat, 'lon': lon} 
                       for (id,nom,lat,lon) in r])    

    headers = [('Content-Type','application/json')];
    self.send(body,headers)

  def send_historique(self):
    # on récupère les informations de la requête
    l_idstation = []
    for i in range(5,len(self.path_info)) :
      l_idstation += [self.path_info[i]]
    donnee = self.path_info[1]
    heure1 = self.path_info[2][:2]
    heure2 = self.path_info[3][:2]
    jour = self.path_info[4]
    
    # configuration du tracé
    plt.figure(figsize=(18,6))
    plt.grid(which='major', color='#888888', linestyle='-')
    plt.grid(which='minor',axis='x', color='#888888', linestyle=':')
    ax = plt.subplot(111)
    loc_major = pltd.YearLocator()
    loc_minor = pltd.MonthLocator()
    ax.xaxis.set_major_locator(loc_major)
    ax.xaxis.set_minor_locator(loc_minor)
    format_major = pltd.DateFormatter('%B %Y')
    ax.xaxis.set_major_formatter(format_major)
    ax.xaxis.set_tick_params(labelsize=10)
    couleurs_disponibles = ['blue', 'red', 'green', 'orange', 'purple', 'black','pink']
    
    # boucle sur les stations pour tracer plusieurs courbes
    for idstation in l_idstation :
      c = conn.cursor()
      c2 = conn.cursor()
      # interrogation de la base de données sur les données de la station d'identifiant idstation
      c.execute("SELECT * FROM 'velov-histo' WHERE number=? ORDER BY horodate", (idstation,))
      c2.execute("SELECT nom FROM 'stations-velov' WHERE idstation=?", (idstation,))
      r = c.fetchall()
      r2 = c2.fetchall()
      nom = r2[0][0]
      # récupération de la date (1ère colonne) et des données qui nous intéressent
      dates = [(datetime.strptime(a[0].split("+")[0], '%Y-%m-%d %H:%M:%S'),a[4],a[5],a[6],a[7]) for a in r]
      # Sélection des dates en fonction du jour et des heures
      if jour != 'Tout' :
        dates_selectionnees = [date for date in dates if int(date[0].day) == int(jour) and int(date[0].hour) >= int(heure1) and int(date[0].hour) < int(heure2)]
      else : 
        dates_selectionnees = [date for date in dates if int(date[0].hour) >= int(heure1) and int(date[0].hour) < int(heure2)]
      # On convertit les dates dans le format pyplot
      x = [pltd.datestr2num(a[0].strftime('%Y-%m-%d %H:%M:%S')) for a in dates_selectionnees]
      ax.xaxis.set_major_locator(pltd.HourLocator(interval=1))
      ax.xaxis.set_major_formatter(pltd.DateFormatter("%H:%M"))
      plt.xticks(rotation=45)
      # En fonction du type sélectionné, on récupère les données
      if donnee == "Velos_disponibles" :
        y = [float(a[1]) for a in dates_selectionnees]
      elif donnee == "Stands_disponibles" :
        y = [float(a[2]) for a in dates_selectionnees]
      elif donnee == "Velos_electriques_disponibles" :
        y = [float(a[3]) for a in dates_selectionnees]
      elif donnee == "Velos_mecaniques_disponibles" :
        y = [float(a[4]) for a in dates_selectionnees]
      # tracé de la courbe
      if l_idstation.index(idstation)< len(couleurs_disponibles) :
         couleur = couleurs_disponibles[l_idstation.index(idstation)]
      else :
        couleur = 'gray'
      plt.plot_date(x,y,linewidth=1, linestyle='-',marker='', color= couleur, label=nom)
    
    # titre
    if len(l_idstation) == 1 :
      plt.title('Disponibilités de la station {}'.format(nom),fontsize=16)
    else :
      titre = 'Disponibilités'
      plt.title(titre,fontsize = 16)
    
    # légendes
    if donnee == "Velos_disponibles" :
      y_label = 'Nombre de vélos'
    elif donnee == "Stands_disponibles" :
      y_label = "Nombre de stands"
    elif donnee == "Velos_electriques_disponibles" :
      y_label = 'Nombre de vélos électriques'
    elif donnee == "Velos_mecaniques_disponibles" :
      y_label = 'Nombre de vélos mécaniques'
    plt.legend(loc='lower right')
    plt.ylabel(y_label)
    plt.xlabel('Heure')
    
    # génération de la courbe dans un fichier PNG 
    fichier = 'courbes/historique_{}_{}_{}.png'.format(donnee,jour+' '+heure1+' '+heure2,l_idstation)
    plt.savefig('client/{}'.format(fichier))
    # réponse au format JSON
    body = json.dumps({
            'title': 'Disponibilités'.format(nom), \
            'img': '/{}'.format(fichier) \
             })
    # envoi de la réponse
    headers = [('Content-Type','application/json')]
    self.send(body,headers)
  
  def send_somme_historique(self):
    # on récupère les informations de la requête
    l_idstation = []
    for i in range(5,len(self.path_info)) :
      l_idstation += [self.path_info[i]]
    donnee = self.path_info[1]
    heure1 = self.path_info[2][:2]
    heure2 = self.path_info[3][:2]
    jour = self.path_info[4]
    
    # configuration du tracé
    plt.figure(figsize=(18,6))
    plt.grid(which='major', color='#888888', linestyle='-')
    plt.grid(which='minor',axis='x', color='#888888', linestyle=':')
    ax = plt.subplot(111)
    loc_major = pltd.YearLocator()
    loc_minor = pltd.MonthLocator()
    ax.xaxis.set_major_locator(loc_major)
    ax.xaxis.set_minor_locator(loc_minor)
    format_major = pltd.DateFormatter('%B %Y')
    ax.xaxis.set_major_formatter(format_major)
    ax.xaxis.set_tick_params(labelsize=10)
    
    #On commence par traiter la premier station de la liste l_idstation
    #afin de pouvoir sommer dessus ensuite
    
    #récupération du nom de la station
    idstation = l_idstation[0]
    c2 = conn.cursor()
    c2.execute("SELECT nom FROM 'stations-velov' WHERE idstation=?", (idstation,))
    r2 = c2.fetchall()
    nom = r2[0][0]
    noms = nom
    
    # interrogation de la base de données sur les données de la station d'identifiant idstation
    c = conn.cursor()
    c.execute("SELECT * FROM 'velov-histo' WHERE number=? ORDER BY horodate", (idstation,))
    r = c.fetchall()
    # récupération de la date (1ère colonne) et des données qui nous intéressent
    dates = [(datetime.strptime(a[0].split("+")[0], '%Y-%m-%d %H:%M:%S'),a[4],a[5],a[6],a[7]) for a in r]
    # Sélection des dates en fonction du jour et des heures
    if jour != 'Tout' :
      dates_selectionnees = [date for date in dates if int(date[0].day) == int(jour) and int(date[0].hour) >= int(heure1) and int(date[0].hour) < int(heure2)]
    else : 
      dates_selectionnees = [date for date in dates if int(date[0].hour) >= int(heure1) and int(date[0].hour) < int(heure2)]
    #Conversion des dates dans le format pyplot
    x = [pltd.datestr2num(a[0].strftime('%Y-%m-%d %H:%M:%S')) for a in dates_selectionnees]
    ax.xaxis.set_major_locator(pltd.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(pltd.DateFormatter("%H:%M"))
    plt.xticks(rotation=45)
    
    #On récupère les données en fonction du type sélectionné
    if donnee == "Velos_disponibles" :
      y = [float(a[1]) for a in dates_selectionnees]
    elif donnee == "Stands_disponibles" :
      y = [float(a[2]) for a in dates_selectionnees]
    elif donnee == "Velos_electriques_disponibles" :
      y = [float(a[3]) for a in dates_selectionnees]
    elif donnee == "Velos_mecaniques_disponibles" :
      y = [float(a[4]) for a in dates_selectionnees]
          
    #On boucle ensuite sur les stations qu'il reste pour créer la courbe somme
    for idstation in l_idstation[1::] :
      c = conn.cursor()
      # interrogation de la base de données sur les données de la station
      c.execute("SELECT * FROM 'velov-histo' WHERE number=? ORDER BY horodate", (idstation,))
      r = c.fetchall()
      # récupération du nom de la station
      c2 = conn.cursor()
      c2.execute("SELECT nom FROM 'stations-velov' WHERE idstation=?", (idstation,))
      r2 = c2.fetchall()
      nom = r2[0][0]
      noms = noms + ' + ' + nom
      c = conn.cursor()
      # interrogation de la base de données sur les données de la station
      c.execute("SELECT * FROM 'velov-histo' WHERE number=? ORDER BY horodate", (idstation,))
      r = c.fetchall()
      # récupération de la date (1ère colonne) et des autres données
      dates = [(datetime.strptime(a[0].split("+")[0], '%Y-%m-%d %H:%M:%S'),a[4],a[5],a[6],a[7]) for a in r]
      # Sélection des dates en fonction du jour et des heures
      if jour != 'Tout' :
        dates_selectionnees = [date for date in dates if int(date[0].day) == int(jour) and int(date[0].hour) >= int(heure1) and int(date[0].hour) < int(heure2)]
      else : 
        dates_selectionnees = [date for date in dates if int(date[0].hour) >= int(heure1) and int(date[0].hour) < int(heure2)]
      # récupération des données en fonction du type choisi
      if donnee == "Velos_disponibles" :
        indice_donne = 1
      elif donnee == "Stands_disponibles" :
        indice_donne = 2
      elif donnee == "Velos_electriques_disponibles" :
        indice_donne = 3
      elif donnee == "Velos_mecaniques_disponibles" :
        indice_donne = 4
      yy = [float(a[indice_donne]) for a in dates_selectionnees]
      
      # Puis on somme avec le reste
      for i in range(len(y)):
        if i < len(yy) :
          y[i] += yy[i]
        
    # tracé de la courbe
    plt.plot_date(x,y,linewidth=1, linestyle='-',marker='', color= 'blue', label=noms)
    
    # titre
    if len(l_idstation) == 1 :
      plt.title('Disponibilités de la station {}'.format(nom),fontsize=16)
    else :
      titre = 'Somme des disponibilités'
      plt.title(titre,fontsize = 16)
    
    # légendes
    if donnee == "Velos_disponibles" :
      y_label = 'Nombre de vélos'
    elif donnee == "Stands_disponibles" :
      y_label = "Nombre de stands"
    elif donnee == "Velos_electriques_disponibles" :
      y_label = 'Nombre de vélos électriques'
    elif donnee == "Velos_mecaniques_disponibles" :
      y_label = 'Nombre de vélos mécaniques'
    plt.legend(loc='lower right')
    plt.ylabel(y_label)
    plt.xlabel('Heure')
    
    # génération de la courbe dans un fichier PNG 
    fichier = 'courbes/somme_historique_{}_{}_{}.png'.format(donnee,jour+' '+heure1+' '+heure2,l_idstation)
    plt.savefig('client/{}'.format(fichier))
    # réponse au format JSON
    body = json.dumps({
            'title': 'Somme des disponibilités', \
            'img': '/{}'.format(fichier) \
             })
    # envoi de la réponse
    headers = [('Content-Type','application/json')]
    self.send(body,headers)
  
  def send_commune(self) :
    c = conn.cursor()
    c.execute("SELECT DISTINCT commune FROM 'stations-velov'")
    r = c.fetchall()
    rr = [] 
    for i in r :
      rr.append(i[0])
    rr.sort()
    n = len(rr)
    for i in range(6,n-1):
        rr[n-1], rr[i] = rr[i], rr[n-1]
    body = json.dumps([{
            'commune' : rr[n]
             } for n in range(len(rr))])
    headers = [('Content-Type','application/json')]
    self.send(body,headers)

  def send(self, body, headers=[]):
    encoded = bytes(body, 'UTF-8')

    self.send_response(200)

    [self.send_header(*t) for t in headers]
    self.send_header('Content-Length', int(len(encoded)))
    self.end_headers()

    self.wfile.write(encoded)


  def init_params(self):
    info = urlparse(self.path)
    self.path_info = [unquote(v) for v in info.path.split('/')[1:]]
    self.query_string = info.query
    
    self.params = parse_qs(info.query)

    length = self.headers.get('Content-Length')
    ctype = self.headers.get('Content-Type')
    if length:
      self.body = str(self.rfile.read(int(length)),'utf-8')
      if ctype == 'application/x-www-form-urlencoded' : 
        self.params = parse_qs(self.body)
      elif ctype == 'application/json' :
        self.params = json.loads(self.body)
    else:
      self.body = ''

    print('init_params|info_path =', self.path_info)
    print('init_params|body =', length, ctype, self.body)
    print('init_params|params =', self.params)


conn = sqlite3.connect('velov.sqlite')

httpd = socketserver.TCPServer(("", port_serveur), RequestHandler)
print("Serveur lancé sur port : ", port_serveur)
httpd.serve_forever()

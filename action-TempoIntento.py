#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Accende e spegne i dispositivi:
config.ini [nostanza]
config.ini [stanzasingoli]
codice.py oggettiSala[]
codice.py oggettiCamera[]

La configurazione avviene con config.ini:
[conf]
password=
port=8123
ipaddress=192.168.X.X

Deve leggere 4 slot dall' intento (stanza - azione - numero - oggetto)
- Se non c'e' stanza ci riferiamo ad un oggetto generico [nostanza]
e possiamo infliarci anche qualche nick (comodino/mensola..)
- Se la stanza e' bagno / cucina / terrazzo (dove c'e' un solo oggetto ci riferiamo a [stanzasingoli]
- Se la stanza e' Sala o Camera dobbiamo ragionare anche sui numeri degli oggetti
'''


from hermes_python.hermes import Hermes
import configparser
import io
import json
import requests 



INTENT_NAME = "boggiano:AccendiSpegni"


MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))


CONFIG_ENCODING_FORMAT="utf-8"
CONFIG_INI="config.ini"



#Device in sala
oggettiSala = ["light.luce_sala_1","light.luce_sala_2","light.luce_sala_3",
"light.strip_sala","light.luce_sala_5",]

#Device in camera
oggettiCamera = ["light.luce_camera", "light.luce_bedlamp_2","light.luce_bedlamp"]



class SnipsConfigParser(configparser.SafeConfigParser):

  def to_dict(self):
#      print("Eseguo to_dict")
      datiConfig = {section : {option_name: option for option_name, option in self.items(section)} for section in self.sections()}
      return datiConfig



def read_config_file(conf_file):
    try:
        with io.open(conf_file, encoding=CONFIG_ENCODING_FORMAT) as f:
            conf_parser = SnipsConfigParser()
            conf_parser.readfp(f)
            return conf_parser.to_dict()
    except (IOError, configparser.Error) as e:
        print ("Problem in reading config file")
        return dict()


# Callback 
def intent_received_callback(hermes, intent_message):

  print("Message in topic arrived! YEAHH ")
  # Disable warning about wrong certificates
  requests.packages.urllib3.disable_warnings()

#  print("Leggiamo la configurazione")
  conf = read_config_file(CONFIG_INI)
#  print (conf['conf']['password'])
#  print (conf['conf']['port'])
#  print (conf['conf']['ipaddress'])
#  print (conf['nostanza']['modalità notte'])
#  print (conf['conf']['ipaddress'])


  dominio = ""
  myDeviceId = ""

  baseUrl = 'https://' + conf['conf']['ipaddress'] + ':' + conf['conf']['port'] + '/api/'

  header = {'Authorization': conf['conf']['password'], 'Content-Type': 'application/json'}
#  print ("[DEBUG] Header: {}".format(header))


#  print ("Intento : {}".format(intent_message.intent.intent_name))
  sentence = ''

  if intent_message.intent.intent_name == INTENT_NAME:

    stanza    = intent_message.slots.stanza.first()
    azione    = intent_message.slots.azione.first()
    numero    = intent_message.slots.numero.first()
    oggetto   = intent_message.slots.oggetto.first()


    if stanza is not None:
     print ("[Stanza] :  -{}-".format(stanza.value))

    if azione is not None:
      print ("[Azione] :  -{}-".format(azione.value))

    if numero is not None:
      print ("[Numero] :  -{}-".format(numero.value))

    if oggetto is not None:
      print ("[Oggetto] :  -{}-".format(oggetto.value))


#Definiamo l'azione che è uguale per tutti i casi
    if (azione.value == 'accendi'):
#      print("[DEBUG] ACCENDIAMO")
      azione = 'turn_on'
    else:
#      print("[DEBUG] SPEGNIAMO")
      azione = 'turn_off'


#CASO I
# Se siamo senza stanza possiamo  dobbiamo giocare con gli oggetti senza stanza

    if (stanza is None):
#      print ("Siamo SENZA STANZA");
      if (not oggetto.value in conf['nostanza']):
        print("ERRORE! L'oggetto -{}- non è contemplato in nel config.ini".format(oggetto.value))
      else:
#        Se esiste dobbiamo capire qual'è il dominio dell' oggetto

        dominio_tmp = conf['nostanza'][oggetto.value].split(".")
        dominio = dominio_tmp[0]
        del dominio_tmp

#        print ("[DEBUG][NO STANZA] Dominio: -{}-".format(dominio))
        myDeviceId = conf['nostanza'][oggetto.value]
#        print ("[DEBUG][NO STANZA] DeviceId: -{}-".format(myDeviceId))

        url = baseUrl + 'services/' + dominio + '/' + azione
#        print (url)


        payload = json.dumps({"entity_id": myDeviceId})
        response = requests.post (url, headers=header, data=payload, verify=False)


#CASO II
# Abbiamo la stanza
# Nel caso di terrazzo e bagno e cucina abbiamo solo una luce
    elif (stanza.value == 'terrazzo' or stanza.value == 'bagno' or stanza.value == 'cucina'):

#      print ("Siamo terrazzo o bagno o cucina")

      dominio_tmp = conf['stanzasingoli'][stanza.value].split(".")
      dominio = dominio_tmp[0]
      del dominio_tmp

#      print ("[DEBUG][STANZA:T/B/C] Dominio: -{}-".format(dominio))
      myDeviceId = conf['stanzasingoli'][stanza.value]
#      print ("[DEBUG][STANZA:T/B/C] DeviceId: -{}-".format(myDeviceId))

      url = baseUrl + 'services/' + dominio + '/' + azione
#      print (url)

      payload = json.dumps({"entity_id": myDeviceId})
      response = requests.post (url, headers=header, data=payload, verify=False)


#Siamo nel caso di sala e camera_da_letto
#per la sala abbiamo il problema della strip e della bedlamp
#In camera abbiamo due bedlamp
    elif (stanza.value == 'sala'):
#      print ("[DEBUG] Siamo in sala")
      dominio = 'light'
      try:
        if numero.value is not None:
          myDeviceId = oggettiSala[int(numero.value)-1]
      except:
        myDeviceId = 'group.sala'


    elif (stanza.value == 'camera'):
#      print ("[DEBUG] Siamo in camera")
      dominio = 'light'
      try:
        if numero.value is not None:
          myDeviceId = oggettiCamera[int(numero.value)-1]
      except:
        myDeviceId = 'group.camera'


#    print ("DOMINIO: {}".format(dominio))
    url = baseUrl + 'services/' + dominio + '/' + azione
#    print (url)

    payload = json.dumps({"entity_id": myDeviceId})
    response = requests.post (url, headers=header, data=payload, verify=False)


#Intento non e' quello desiderato
  else:
      print ("Non so dove siamo")
#    sentence = "Va bene"


  print ("Now the voice")
  sentence = "Va bene!"
  hermes.publish_end_session(intent_message.session_id, sentence)

  return


''''
  myDeviceId = "switch.tpdesklampstudio"


  if (action == 'query'):
    url = 'https://' + conf['conf']['ipaddress'] + ':' + conf['conf']['port'] + '/api/states/' + myDeviceId
#    print (url)

    response = requests.get (url, headers=header, verify=False)

      # Lo stato del device e' contenuta in response.json()['state']
#      print (response)
#      print (response.json()['state'])


    url = 'https://' + conf['conf']['ipaddress'] + ':' + conf['conf']['port'] + '/api/services/switch/' + azione
    payload = json.dumps({"entity_id": myDeviceId})
    response = requests.post (url, headers=header, data=payload, verify=False)

'''''




    

with Hermes(MQTT_ADDR) as h:
    print ("subscribe to Hermes")
    h.subscribe_intent(INTENT_NAME,intent_received_callback).start()






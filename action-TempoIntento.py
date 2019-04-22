#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hermes_python.hermes import Hermes
import configparser
import io
import json
import requests 

MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))


INTENT_NAME = "boggiano:AccendiSpegni"

CONFIG_ENCODING_FORMAT="utf-8"
CONFIG_INI="config.ini"


oggettiSenzaStanza = {"caffè" : 'switch.tpcucinacaffe',
 'modalità notte': 'input_boolean.bedtime_mode',
 'roomba 630'    : 'switch.romba630_clean',
 'roomba 620'    : 'switch.620_clean',
 'sveglia relax' : 'input_boolean.svegliarelax',
 'sveglia work'  : 'input_boolean.svegliawork'}


oggettiSingoliStanza = {'cucina' : 'light.strip_cucina',
'terrazzo' : 'light.luce_terrazzo',
'bagno' : 'light.luce_bagno_1'}


oggettiSala = ["light.luce_sala_1","light.luce_sala_2","light.luce_sala_3",
"light.strip_sala","light.luce_sala_5",]

oggettiCamera = ["light.luce_camera", "light.luce_bedlamp_2","light.luce_bedlamp"]



class SnipsConfigParser(configparser.SafeConfigParser):

    def to_dict(self):
        print("Eseguo to_dict")
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

  print("Leggiamo la configurazione")
  conf = read_config_file(CONFIG_INI)
  print (conf['conf']['password'])
  print (conf['conf']['port'])
  print (conf['conf']['ipaddress'])

  dominio = ""
  myDeviceId = ""

  baseUrl = 'https://' + conf['conf']['ipaddress'] + ':' + conf['conf']['port'] + '/api/'

  header = {'Authorization': conf['conf']['password'], 'Content-Type': 'application/json'}
  print (header)


  print ("Intento : {}".format(intent_message.intent.intent_name))
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

#    oggetto ="caffè"

#Definiamo l'azione che è uguale per tutti i casi
    if (azione.value == 'accendi'):
      print("ACCENDIAMO")
      azione = 'turn_on'
    else:
      print("SPEGNIAMO")
      azione = 'turn_off'


# Se siamo senza stanza possiamo  dobbiamo giocare con gli oggetti senza stanza

    if (stanza is None):
      print ("Siamo SENZA STANZA");
      if (not oggetto.value in oggettiSenzaStanza):
        print("ERRORE ! Non e' un oggetto contemplato")
      else:
#        Se esiste dobbiamo capire qual'è il dominio dell' oggetto
        print ("Prendiamo l'entity:")
        print ("Entity: {}".format(oggettiSenzaStanza[oggetto.value]))
        dominio_tmp = oggettiSenzaStanza[oggetto.value].split(".")
        dominio = dominio_tmp[0]
        print (dominio)
        myDeviceId = oggettiSenzaStanza[oggetto.value]
        print (myDeviceId)

        url = baseUrl + 'services/' + dominio + '/' + azione
        print (url)


        payload = json.dumps({"entity_id": myDeviceId})
        response = requests.post (url, headers=header, data=payload, verify=False)



# Abbiamo la stanza
# Nel caso di terrazzo e bagno e cucina abbiamo solo una luce
    elif (stanza.value == 'terrazzo' or stanza.value == 'bagno' or stanza.value == 'cucina'):

      print ("Siamo terrazzo o bagno o cucina")

      dominio_tmp = oggettiSingoliStanza[stanza.value].split(".")
      dominio = dominio_tmp[0]
      print (dominio)

      myDeviceId = oggettiSingoliStanza[stanza.value]
      print (myDeviceId)

      url = baseUrl + 'services/' + dominio + '/' + azione
      print (url)

      payload = json.dumps({"entity_id": myDeviceId})
      response = requests.post (url, headers=header, data=payload, verify=False)

# Qui siamo nel caso di sala e camera_da_letto
#per la sala abbiamo il problema della strip e della bedlamp
#In camera abbiamo due bedlamp
    elif (stanza.value == 'sala'):
      print ("Siamo in sala")
      dominio = 'light'
      if numero.value is not None:
        myDeviceId = oggettiSala[int(numero.value)-1]
      else:
        myDeviceId = 'group.sala'

    elif (stanza.value == 'camera'):
      print ("Siamo in camera")

      dominio = 'light'
      if numero is not None:
        myDeviceId = oggettiCamera[int(numero.value)-1]
      else:
        myDeviceId = 'group.sala'

    print ("DOMINIO: {}".format(dominio))
    url = baseUrl + 'services/' + dominio + '/' + azione
    print (url)

    payload = json.dumps({"entity_id": myDeviceId})
    response = requests.post (url, headers=header, data=payload, verify=False)


#Intento non e' quello desiderato
  else:
      print ("Non so dove siamo")
#    sentence = "Va bene"


#    hermes.publish_end_session(intent_message.session_id, sentence)


  print ("Now the voice")
  sentence = " Benissimo"
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
    h.subscribe_intents(intent_received_callback).start()






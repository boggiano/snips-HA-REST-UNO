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


oggettiSenzaStanza = {'caffè' : 'switch.tpcucinacaffe',
 'modalità notte': 'input_boolean.bedtime_mode',
 'roomba 630'    : 'switch.romba630_clean',
 'roomba 620'    : 'switch.620_clean',
 'sveglia relax' : 'input_boolean.svegliarelax',
 'sveglia work'  : 'input_boolean.svegliawork'}

dominio=""

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
  print("----------- 2 -----------------")
  # Disable warning about wrong certificates
  requests.packages.urllib3.disable_warnings()

  print("Prima di conf")
  conf = read_config_file(CONFIG_INI)
  print (conf['conf']['password'])
  print (conf['conf']['port'])
  print (conf['conf']['ipaddress'])

  baseUrl = 'https://' + conf['conf']['ipaddress'] + ':' + conf['conf']['port'] + '/api/'

  action = "query"
  #action = "spegni"



  header = {'Authorization': conf['conf']['password'], 'Content-Type': 'application/json'}
  print (header)


  print (intent_message.intent.intent_name)
  sentence = 'Hai chiesto '

  if intent_message.intent.intent_name == INTENT_NAME:

    stanza    = intent_message.slots.stanza.first()
    azione    = intent_message.slots.azione.first()
    numero    = intent_message.slots.numero.first()
    oggetto   = intent_message.slots.oggetto.first()

    if stanza is not None:
     print ("[Stanza] :  {}".format(stanza.value))

    if azione is not None:
      print ("[Azione] :  -{}-".format(azione.value))

    if numero is not None:
      print ("[Numero] :  {}".format(numero.value))

    if oggetto is not None:
      print ("[Oggetto] :  {}".format(oggetto.value))

    oggetto ="caffè"

# Se siamo senza stanza possiamo  giocare con gli oggetti senza stanza
    if (stanza is None):
      print ("Siamo SENZA STANZA");
      if (not oggetto in oggettiSenzaStanza):
        print("ERRORE ! Non e' un oggetto contemplato")
      else:
#        Se esiste dobbiamo capire qual'è il dominio dell' oggetto
        print ("Prendiamo l'entity:")
        print ("Entity: {}".format(oggettiSenzaStanza[oggetto]))
        dominio_tmp = oggettiSenzaStanza[oggetto].split(".")
        dominio = dominio_tmp[0]
        print (dominio)
        myDeviceId = oggettiSenzaStanza[oggetto]
        print (myDeviceId)

        if (azione.value == 'accendi'):
          print("ACCENDIAMO")
          azione = 'turn_on'
        else:
          print("SPEGNIAMO")
          azione = 'turn_off'

        url = baseUrl + 'services/' + dominio + '/' + azione
        print (url)


        payload = json.dumps({"entity_id": myDeviceId})
        response = requests.post (url, headers=header, data=payload, verify=False)

        print ("Now the voice")
        sentence = " Benissimo"
        hermes.publish_end_session(intent_message.session_id, sentence)


  else:
    print ("Prendiamo l'entity:")

#    sentence = "Va bene"


#    hermes.publish_end_session(intent_message.session_id, sentence)

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






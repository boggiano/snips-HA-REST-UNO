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


INTENT_NAME = "boggiano:TempoIntento"

CONFIG_ENCODING_FORMAT="utf-8"
CONFIG_INI="config.ini"


oggettiSenzaStanza = {'caffè' : 'switch.tpcucinacaffe',
 'modalità notte':' input_boolean.bedtime_mode',
 'roomba 630'    : 'switch.romba630_clean',
 'roomba 620'    :'switch.620_clean',
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
    print("Message in topic arrived!")

    sentence = 'Hai chiesto '

    if intent_message.intent.intent_name == INTENT_NAME:

      stanza = intent_message.slots.stanza.first()
      azione = intent_message.slots.citta.first()
      numero = intent_message.slots.previsioni.first()
      cosa   = intent_message.slots.cosa.first()



    else:
        return


    if citta_slot is not None:
        sentence += 'a ' + citta_slot.value
        print ("[Dove] :  {}".format(citta_slot.value))
    
    if previsioni_slot is not None:
        sentence += 'in ' + previsioni_slot.value
        print ("[Cosa] :  {}".format(previsioni_slot.value))
    
    if quando_slot is not None :
        sentence += ' ' + quando_slot.value
        print ("[Quando] :  {}".format(quando_slot.value))

    hermes.publish_end_session(intent_message.session_id, sentence)


with Hermes(MQTT_ADDR) as h:
    print ("subscribe to Hermese")

    conf = read_config_file(CONFIG_INI)
    print (conf['conf']['password'])
    print (conf['conf']['port'])
    print (conf['conf']['ipaddress'])


    action = "query"
    #action = "spegni"

    requests.packages.urllib3.disable_warnings()

    header = {'Authorization': conf['conf']['password'], 'Content-Type': 'application/json'}
    print (header)

    stanza = ''
    cosa= 'modalità notte'

# Se siamo senza stanza possiamo avere giocare con gli oggetti senza stanza
    if (stanza == ''):
      print ("Siamo SENZA STANZA");
      if (not cosa in oggettiSenzaStanza):
        print("ERRORE ! Non e' un oggetto contemplato'")
      else:
      # Se esiste dobbiamo capire qual'è il dominio dell' oggetto
        dominio_tmp = oggettiSenzaStanza[cosa].split(".")
        dominio = dominio_tmp[0]

        print (dominio)
    myDeviceId = "switch.tpdesklampstudio"


    if (action == 'query'):
      url = 'https://' + conf['conf']['ipaddress'] + ':' + conf['conf']['port'] + '/api/states/' + myDeviceId
      print (url)

      response = requests.get (url, headers=header, verify=False)

      # Lo stato del device e' contenuta in response.json()['state']
      print (response)
      print (response.json()['state'])

    else:
      if (action.lower() == 'accendi'):
        azione = 'turn_on'
      else:
        azione = 'turn_off'
      url = 'https://' + conf['conf']['ipaddress'] + ':' + conf['conf']['port'] + '/api/services/switch/' + azione
      payload = json.dumps({"entity_id": myDeviceId})
   
      response = requests.post (url, headers=header, data=payload, verify=False)


    h.subscribe_intents(intent_received_callback).start()

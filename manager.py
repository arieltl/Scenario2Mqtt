from mqtt import MqttManager
from telnetManager import TelnetManager
import json

class Manager:
	def __init__(self, modules) -> None:
		self.modules = {module.id: module for module in modules}
		self.mqtt = MqttManager(self.on_message)
		self.telnet = TelnetManager()
		for modId in modules:
			module = modules[modId]
			for zone in module.zones:
				#publish home assistant auto discovery light json mode unique id = modId+zone
				#subscribe to modId+zone
				self.mqtt.publish("homeassistant/light/"+modId+zone+"/config", json.dumps({
					"schema": "json",
					"name": "scenario "+ modId+" "+zone,
					"state_topic": f"ifsei/{modId}-{zone}/state",
					"command_topic": f"ifsei/{modId}-{zone}/set",
					"brightness": True,
					"unique_id":f"scenario-{modId}-{zone}",
					"brightness_scale": 63,
					"device": {
						"identifiers": f"scenario-{modId}-{zone}",
						"name": "Scenario Light" ,
						"model": "Dimmer Channel",
						"manufacturer": "Scenario"
					}
				}))
				self.mqtt.subscribe(f"ifsei/{modId}-{zone}/set")
				self.mqtt.publish(f"ifsei/{modId}-{zone}/state", json.dumps(module.state[zone]))

	def loop(self):
		self.mqtt.loop()
		msg = self.telnet.read()
		if msg is not None and msg.startswith("*D"):
			
		
	def on_message(self, msg):
		print(msg.topic+" "+str(msg.payload))
		
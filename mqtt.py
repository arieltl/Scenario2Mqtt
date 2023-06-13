import paho.mqtt.client as mqtt
import json



class MqttManager():
	def __init__(self,callback) -> None:
		with open('config.json') as f:
			# print(json.loads(f))
			config = json.load(f)["mqttBroker"]
		def on_connect(client, userdata, flags, rc):
			print("Connected with result code "+str(rc))
		self.client = mqtt.Client()
		self.client.on_connect = on_connect
		self.client.on_message = self.on_message
		self.client.username_pw_set(config["username"], config["password"])
		self.client.connect(config["host"], config["port"], 60)
		self.callback = callback

	

	# The callback for when a PUBLISH message is received from the server.
	def on_message(self, client, userdata, msg):
		print(msg.topic+" "+str(msg.payload))
		self.callback(msg)
	def subscribe(self, topic):
		self.client.subscribe(topic)
	
	def publish(self, topic, payload):
		self.client.publish(topic, json.dumps(payload) if isinstance(payload,dict) else payload,qos=2,retain=True)
	def loop(self):
		self.client.loop()
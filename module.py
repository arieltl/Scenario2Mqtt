class DimmerModule:
	def __init__(self, id, zones) -> None:
		self.id = id
		self.zones = set(zones)
		self.state = dict()
		for zone in zones:
			dict[zone] = {"state":"OFF", "bri":0}
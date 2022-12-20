from manager import Manager
from module import DimmerModule

if __name__ == "__main__":
	modules = [
		DimmerModule(1, range(1,8)), #module id, zones (all zones)
		DimmerModule(2, [1,4,5]), #module id, zones (only 1,4,5)

		]
	manager = Manager(modules)
	while True:
		manager.loop()
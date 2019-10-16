from abc import ABC, abstractmethod


class BaseReporter(ABC):
	def __init__(self):
		super().__init__()
	
	# Should return the file mapping
	@abstractmethod
	def map(self):
		pass

	# Should return a parsing method
	@abstractmethod
	def parse(self, report_content):
		pass
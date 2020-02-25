from reporters import BaseReporter
import re

class Reporter(BaseReporter):
	def __init__(self):
		super().__init__()

	def map(self):
		return {
			'IR::AREA::DSG': 'Area'
		}

	def parse(self, report_content):
		area = 1.2
		return {
			'IR::AREA::DSG': round(area, 4),
		}
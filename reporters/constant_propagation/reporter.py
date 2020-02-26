from reporters import BaseReporter
import re

class Reporter(BaseReporter):
	def __init__(self):
		super().__init__()

	def map(self):
		return {
			'design': 'design',
			'InstCount': 'Number of instances',
			'HasTieHi': 'Has Tie-Hi',
			'HasTieLo': 'Has Tie-Lo',
			'Edits': 'Applied edits',
			'IR::AREA::DSG': 'Area',
		}

	def parse(self, report_content):
		area = float(re.compile(r'Chip area for module\s+[\w\'\\]+\s*:\s*([-+]?[0-9]*\.?[0-9]+)', re.I).search(report_content)[1])
		edits = 0
		hasTieHi = re.compile(r'LOGIC1').search(report_content) != None
		hasTieLo = re.compile(r'LOGIC0').search(report_content) != None
		instCount = int(re.compile(r'Number of cells:\s+(\d+)', re.I).search(report_content)[1])
		editsMatches = re.compile(r'Applied constant propagation:\s*(\d+)', re.I).search(report_content)
		if editsMatches != None:
			edits = int(editsMatches[1])
		return {
			'InstCount': instCount,
			'HasTieHi': hasTieHi,
			'HasTieLo': hasTieLo,
			'Edits': edits,
			'IR::AREA::DSG': round(area, 4),
		}
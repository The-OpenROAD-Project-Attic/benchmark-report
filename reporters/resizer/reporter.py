from reporters import BaseReporter
import re

class Reporter(BaseReporter):
	def __init__(self):
		super().__init__()

	def map(self):
		return {
			'design': 'design',
			'TIMING::SLACK::DAT': 'DAT',
			'TIMING::SLACK': 'CP Slack',
			'TIMING::SLACK::TOTAL': 'Total Slack',
			'TIMING::SLACK::AVG': 'Average Slack',
			'TIMING::SLACK::TNS': 'TNS',
			'TIMING::SLACK::WNS': 'WNS',
			'IR::AREA::DSG': 'Area',
			'PLACEMENT::DENSITY': 'Utilization',
			'TIMING::VIOLATION::TOTAL': 'Violations'
		}

	def parse(self, report_content):
		path_slices = list(filter(lambda s: s.startswith(':'), re.compile(r'\s*Startpoint\s*', re.M).split(report_content)))
		last_data = path_slices[-1]
		min_dat = None
		max_dat = None
		min_slack = None
		max_slack = None
		for slice in path_slices:
			path_type = re.compile(r'Path\s+Type\s*\:\s*(\w+)', re.M).search(slice)[1]
			slack = float(re.compile(r'(\d+(.\d+)?)\s+slack\s+', re.M).search(slice)[1])
			dat = float(re.compile(r'(\d+(.\d+)?)\s+data\s+arrival\s+time\s+', re.M).search(slice)[1])
			if path_type == 'min':
				min_dat = dat
				min_slack = slack
			if path_type == 'max':
				max_dat = dat
				max_slack = slack
		area_matches = re.compile(r'Design\s+area\s+(\d+(.\d+)?)\s+u\^2\s+(\d+(.\d+)?)%\s+utilization\.', re.M).search(last_data)
		area = int(area_matches[1]);
		util = float(area_matches[3]);

		total_slack = float(re.compile(r'Total\s+Slack\s*\:\s*(\d+(.\d+)?)', re.M).search(last_data)[1])
		average_slack = 'N/A'
		if re.compile(r'Average\s+Slack\s*\:\s*(\d+(.\d+)?)', re.M).search(last_data):
			average_slack = float(re.compile(r'Average\s+Slack\s*\:\s*(\d+(.\d+)?)', re.M).search(last_data)[1])
		violations = len(re.compile('VIOLATED', re.M).findall(last_data))
		tns = float((re.compile(r'tns\s+(\d+(.\d+)?)', re.M).search(last_data) or [0.0, 0.0])[1])
		wns = float((re.compile(r'wns\s+(\d+(.\d+)?)', re.M).search(last_data) or [0.0, 0.0])[1])
		return {
			'TIMING::SLACK::DAT::MIN': round(min_dat, 4),
			'TIMING::SLACK::DAT::MAX': round(max_dat, 4),
			'TIMING::SLACK::MIN': round(min_slack, 4),
			'TIMING::SLACK::MAX': round(max_slack, 4),
			'TIMING::SLACK': round(max_slack, 4),
			'TIMING::SLACK::DAT': round(max_dat, 4),
			'IR::AREA::DSG': area,
			'PLACEMENT::DENSITY': round(util, 4),
			'TIMING::SLACK::TOTAL': round(total_slack, 4),
			'TIMING::SLACK::AVG': round(average_slack, 4) if average_slack != 'N/A' else average_slack,
			'TIMING::VIOLATION::TOTAL': violations,
			'TIMING::SLACK::TNS': round(tns, 4),
			'TIMING::SLACK::WNS': round(wns, 4)
		}
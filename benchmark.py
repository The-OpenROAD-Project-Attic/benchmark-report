"""Generate benchmark reports.

Usage:
  benchmark.py [options]
  benchmark.py (-h | --help)
  benchmark.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --working-dir=<dir>  Script working directory.  [default: ./]
  --reports-dir=<dir>  Reports directory. [default: ./logs]
  --no-run-flow  Generate the reports without re-running the flow.
  --platform=<tech>  Technology used (e.g. nangate45, tsmc65lp).  [default: nangate45]
  --stage=<stage>  Design stage to run (e.g. synth, floorplan..etc).  [default: place]
  --designs=<designs>  Comma-seperated list of designs to run the flow on.  [default: gcd,aes,ibex,swerv]
  --reports=<reports>  Comma-seperated list of reports to collect, can use semi-colon to specify report title.  [default: 3_1_2_place_gp_dp.log:DP Only,3_2_a_2_place_resized.log: Resize + Buffer -> DP,3_2_a_4_place_resized_cloned.log: Resize + Buffer -> DP -> Gate Cloning -> DP,3_2_b_2_place_cloned.log:Gate Cloning -> DP,3_2_b_4_place_cloned_resized.log: Gate Cloning -> DP -> Resize + Buffer -> DP]
  --compare=<deltas>  Expression to evaluate deltas between different reports in format of <report-index>,<report-index>,...:<attr>~<delta-name>,<attr>~<delta-name>...;<report-index>,<report-index>,...:<attr>~<delta-name>,<attr>~<delta-name>...  [default: 1,2,3:area~Area Change,dat~DAT Change,violations~Violations Change;1,4,5:area~Area Change,dat~DAT Change,violations~Violations Change]
  --no-color-delta  Disable values coloring starting with + or - as Green or Red respectively.  [default: False]
  --clean-command=<cmd>  The make command to clean the current designs.  [default: clean_all]
  --no-clean  Do not clean the output directories before starting the flow.  [Default: False]
  --excel  Generate the report in Excel format.
  --xlsx  Generate the report in Excel format.
  --csv  Generate the report in csv format.
  --html  Generate the report in html format.
  --json  Generate the report in json format.
  --quiet  Suppres flow run messages  [default: False]
  -o --out=<dir>  Output file name (without extension).  [default: ./report]
  --design-path-pattern=<path>  The pattern that will be used to map the design to configuration file.  [default: ./designs/{}_{}.mk]
  --make-cmd=<cmd>  The path/command to run the make tool.  [default: make]
  --design-config-var=<var>  The variable used to set the design configuration file in the Makefile.  [default: DESIGN_CONFIG]
"""
from docopt import docopt
import csv
import logging
import sys
import subprocess
import re
import os
from openpyxl import Workbook
from openpyxl.cell import Cell
from openpyxl.styles import Font, Border, Side, Alignment
import json

# from openpyxl.styles import PatternFill, Border, Side, Alignment, Protection, Font


timing_report_map = {
	'design': 'Design',
	'dat': 'DAT',
	'slack': 'CP Slack',
	'total_slack': 'Total Slack',
	'average_slack': 'Average Slack',
	'area': 'Area',
	'util': 'Utilization',
	'violations': 'Violations'
}

def read_file(filepath):
	with open(filepath, 'r') as f:
		return f.read()

def get_top_module(config_file):
	return re.compile('export\s+DESIGN_NAME\s*=\s*(\w+)', re.I).match(read_file(config_file))[1]

def run_flow(config_file, make_cmd='make', clean_cmd='clean_all', stage='place', design_config_var='DESIGN_CONFIG', no_clean=False):
	cmd = f'{make_cmd} {stage}'
	if not no_clean:
		cmd = f'{make_cmd} {clean_cmd} && {cmd}'
	env = os.environ.copy()
	env[design_config_var] = config_file
	popen = subprocess.Popen(cmd,
						shell=True,
						env=env,
						stdout=subprocess.PIPE,
						universal_newlines=True
			)
	for stdout_line in iter(popen.stdout.readline, ""):
		yield stdout_line 
	popen.stdout.close()
	return_code = popen.wait()
	if return_code:
		raise subprocess.CalledProcessError(return_code, cmd)

def parse_time_report(report_content):
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
		'min_dat': round(min_dat, 4),
		'max_dat': round(max_dat, 4),
		'min_slack': round(min_slack, 4),
		'max_slack': round(max_slack, 4),
		'slack': round(max_slack, 4),
		'dat': round(max_dat, 4),
		'area': area,
		'util': round(util, 4),
		'total_slack': round(total_slack, 4),
		'average_slack': round(average_slack, 4) if average_slack != 'N/A' else average_slack,
		'violations': violations,
		'tns': round(tns, 4),
		'wns': round(wns, 4)
	}
	

def parse_report(report_path, report_type='timing'):
	report_content = read_file(report_path)
	if report_type == 'timing':
		return parse_time_report(report_content)

def write_csv(writing_data, headers, output_file):
	outfile_path = os.path.join(os.path.dirname(output_file), os.path.basename(output_file) + '.csv')
	with open(outfile_path, 'w', newline='') as csvfile:
		writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction='ignore')
		writer.writeheader()
		for report_name, report in writing_data.items():
			writer.writerow({headers[0]: report['title']})
			for row in report['rows']:
				writer.writerow(row)
	
def write_xlsx(writing_data, headers, output_file, color_delta=False):
	outfile_path = os.path.join(os.path.dirname(output_file), os.path.basename(output_file) + '.xlsx')
	wb = Workbook()

	ws = wb.active

	thin = Side(border_style="thin", color="000000")
	double = Side(border_style="medium", color="000000")

	header_cells = [Cell(ws, column="A", row=1, value=header) for header in headers]
	
	for cell in header_cells:
		cell.font = Font(bold=True)
		cell.border = Border(top=double, left=double, right=double, bottom=double)
		cell.alignment = Alignment(horizontal="center", vertical="center")
	ws.append(header_cells)
	for report_name, report in writing_data.items():
		title_cell = Cell(ws, column="A", row=1, value=report['title'])
		title_cell.font = Font(bold=True)
		# title_cell.alignment = Alignment(horizontal="center", vertical="center")
		ws.append([title_cell])
		for row in report['rows']:
			cells = [Cell(ws, column="A", row=1, value=(row[header] if header in row else ""))  for header in headers]
			for i,cell in enumerate(cells):
				# if i == 0:
				# 	cell.font = Font(bold=True)
				cell.border = Border(top=thin, left=thin, right=thin, bottom=thin)
				cell.alignment = Alignment(horizontal="center", vertical="center")
				if color_delta:
					if str(cell.value).startswith('+'):
						if float(cell.value) != 0:
							cell.font = Font(bold=True, color='00a933')
						else:
							cell.font = Font(bold=True)
					elif str(cell.value).startswith('-'):
						if float(cell.value) != 0:
							cell.font = Font(bold=True, color='c9211e')
						else:
							cell.font = Font(bold=True)
			ws.append(cells)
	column_widths = []
	for i,header in enumerate(headers):
		column_widths.append(len(header) * 1.4 + 4)


	for i, column_width in enumerate(column_widths):
		ws.column_dimensions[chr(ord('A') + i)].width = column_width
	wb.save(outfile_path)

def write_json(writing_data, headers, output_file):
	outfile_path = os.path.join(os.path.dirname(output_file), os.path.basename(output_file) + '.json')
	json_data = {}
	for report_name, report in writing_data.items():
		json_data[report['title']] = {}
		for row in report['rows']:
			json_data[report['title']][row['Design']] = dict((header, row[header] if header in row else 'N/A') for header in headers)

	with open(outfile_path, 'w') as jsonfile:
		json.dump(json_data, jsonfile, sort_keys=True, indent=4, separators=(',', ': '))

def write_html(writing_data, headers, output_file, color_delta=False):
	outfile_path = os.path.join(os.path.dirname(output_file), os.path.basename(output_file) + '.html')
	script_path = os.path.dirname(os.path.realpath(__file__))
	report_template_path = os.path.join(script_path, 'report_template.html')
	table_template_path = os.path.join(script_path, 'table_template.html')
	report_template = read_file(report_template_path)
	table_template = read_file(table_template_path)


	tables = ''
	headers_html = '\n'.join(['<th>{}</th>'.format(header) for header in headers])
	for report_name, report in writing_data.items():
		rows = []
		for row in report['rows']:
			cols = []
			for col in row.values():
				style = ''
				if color_delta:
					if str(col).startswith('+'):
						if float(col) != 0:
							style = 'color: #00a933; font-weight: bold;'
						else:
							style = 'font-weight: bold;'
					elif str(col).startswith('-'):
						if float(col) != 0:
							style = 'color: #c9211e; font-weight: bold;'
						else:
							style = 'font-weight: bold;'
				cols = cols + ['<td style="{style}">{col}</td>'.format(style=style, col=col)]
			rows = rows + ['<tr>' + '\n'.join(cols) + '</tr>']
		rows = '\n'.join(rows)
		tables = tables + '\n' + table_template.format(title=report['title'], headers=headers_html, rows=rows) + '\n'
	report = report_template.format(tables=tables)

	with open(outfile_path, 'w') as htmlfile:
		htmlfile.write(report)

def main(arguments):
	generate_xlsx = arguments['--excel'] or arguments['--xlsx']
	generate_csv = arguments['--csv']
	generate_html = arguments['--html']
	generate_json = arguments['--json']
	no_run_flow = arguments['--no-run-flow']
	tech = arguments['--platform']
	design_path_pattern = arguments['--design-path-pattern']
	make_cmd = arguments['--make-cmd']
	design_config_var = arguments['--design-config-var']
	clean_cmd = arguments['--clean-command']
	quiet = arguments['--quiet']
	stage = arguments['--stage']
	no_clean = arguments['--no-clean']
	report_dirs = arguments['--reports-dir']
	reports = arguments['--reports']
	compare_expr = arguments['--compare']
	output_file = arguments['--out']
	color_delta = not arguments['--no-color-delta']

	if not generate_csv and not generate_html and not generate_json and not generate_xlsx:
		generate_xlsx = True
	
	os.chdir(arguments['--working-dir'])
	
	designs = re.compile(r'\s*[,:;]+\s*').split(arguments['--designs'])

	if not no_run_flow:
		for design in designs:
				if not quiet:
					print(f'Running flow [{stage}] for design {design}:{tech}')
				config_file = design_path_pattern.format(design, tech)
				for results in run_flow(config_file, make_cmd=make_cmd, clean_cmd=clean_cmd, stage=stage, design_config_var=design_config_var, no_clean=no_clean):
					if not quiet:
						print(results)


	parsed_report_names = []
	report_index_to_name = {}
	i = 0
	for report_name in re.compile('[,]').split(reports):
		report_name_parts = re.compile('[\:]\s*').split(report_name)
		report_title = os.path.join(os.path.dirname(report_name_parts[0].strip()), os.path.basename(report_name_parts[0].strip()))
		if len(report_name_parts) >= 2 and report_name_parts[1].strip():
			report_title = report_name_parts[1].strip()
		parsed_report_names.append({
			'title': report_title,
			'filename': report_name_parts[0],
			'deltas': {}
		})
		report_index_to_name[i] = report_name_parts[0]
		i = i + 1
  
	delta_fields_dict = {}
	for expr in re.compile('\s*[;]\s*').split(compare_expr):
		[report_indices, attrs] = re.compile('\s*:\s*').split(expr)
		report_indices = list(map(lambda x: int(x) - 1, re.compile('\s*,\s*').split(report_indices)))
		attrs_key_value = re.compile('\s*,\s*').split(attrs)
		attrs = list(map(lambda x: (re.compile('\s*~\s*').split(x)[0], re.compile('\s*~\s*').split(x)[1]), re.compile('\s*,\s*').split(attrs)))
		for i, index in enumerate(report_indices):
			if i == 0:
				continue
			prev_index = report_indices[i - 1]
			if prev_index not in parsed_report_names[index]['deltas']:
				parsed_report_names[index]['deltas'][prev_index] = []
			for attr in attrs:
				delta_fields_dict[attr[0]] = attr[1]
				parsed_report_names[index]['deltas'][prev_index] += [attr]

	writing_data = dict((report['filename'], {'file': report['filename'], 'title': report['title'], 'rows': []}) for report in parsed_report_names)

	raw_parsed_reports = {}
	parsed_reports = {}

	for design in designs:
		config_file = design_path_pattern.format(design, tech)
		top_module = get_top_module(config_file)
		report_dir = os.path.join(report_dirs, tech, top_module)
		for parsed_report_name in parsed_report_names:
			filename = parsed_report_name['filename']
			report_path = os.path.join(report_dir, filename)
			parsed_report = parse_report(report_path)
			parsed_report['design'] = design

			if filename not in raw_parsed_reports:
				raw_parsed_reports[filename] = {}
				parsed_reports[filename] = {}

			raw_parsed_reports[filename][design] = parsed_report
			parsed_reports[filename][design] = {}

			for k,v in timing_report_map.items():
				parsed_reports[filename][design][v] = parsed_report[k]

	for parsed_report_name in parsed_report_names:
			deltas = parsed_report_name['deltas']
			report_name = parsed_report_name['filename']
			for design in designs:
				parsed_report = parsed_reports[report_name][design]
				for report_index, attr_pairs in deltas.items():
					for attr, attr_title in attr_pairs:
						diff = round(raw_parsed_reports[report_name][design][attr] - raw_parsed_reports[report_index_to_name[report_index]][design][attr], 4)
						parsed_report[attr_title] = '+' + str(diff) if diff >= 0 else '-' + str(-1 * diff)
	headers = list(timing_report_map.values()) + list(delta_fields_dict.values())

	for filename, data in writing_data.items():
		parsed_report = parsed_reports[filename]
		data['headers'] = headers
		for design in designs:
			data['rows'].append(parsed_report[design])
	
	if generate_csv:
		write_csv(writing_data, headers, output_file)

	if generate_xlsx:
		write_xlsx(writing_data, headers, output_file, color_delta=color_delta)

	if generate_json:
		write_json(writing_data, headers, output_file)

	if generate_html:
		write_html(writing_data, headers, output_file, color_delta=color_delta)


if __name__ == '__main__':
	arguments = docopt(__doc__, version='1.0.1')
	main(arguments)
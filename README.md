# OpenROAD Benchmark Report

A tool to generate benchmark reports reflecting enhancements/modifications for OpenROAD tools (currently configured for the Resizer optimization flow).

## Requirments

Python 3.x

## Install dependencies

`pip install -r requirements.txt`

## Run

`python benchmark.py [options]`

### Options

-   `-h --help` Show help screen.
-   `--version` Show version.
-   `--working-dir=<dir>` Script working directory. **default: ./**
-   `--reports-dir=<dir>` Reports directory. **default: ./logs**
-   `--no-run-flow` Generate the reports without re-running the flow.
-   `--platform=<tech>` Technology used (e.g. nangate45, tsmc65lp). **default: nangate45**
-   `--stage=<stage>` Design stage to run (e.g. synth, floorplan..etc). **default: place**
-   `--tool=<tool>` The target tool for the report to pick the proper parser **[default: resizer]**
-   `--designs=<designs>` Comma-seperated list of designs to run the flow on. **default: gcd,aes,ibex,swerv**
-   `--reports=<reports>` Comma-seperated list of reports to collect, can use semi-colon to specify report title. **default: 3_1_2_place_gp_dp.log:DP Only,3_2_a_2_place_resized.log: Resize + Buffer -> DP,3_2_a_4_place_resized_cloned.log: Gate Cloning -> DP,3_2_b_2_place_cloned.log:Gate Cloning -> DP,3_2_b_4_place_cloned_resized.log: Gate Cloning -> DP -> Resize + Buffer -> DP**
-   `--compare=<deltas>` Expression to evaluate deltas between different reports in format of \<report-index\>,\<report-index\>,...:\<attr\>\~\<delta-name\>,\<attr\>\~\<delta-name\>...;\<report-index\>,\<report-index\>,...:\<attr\>\~\<delta-name\>,\<attr\>\~\<delta-name\>... **[default: 1,2,3:area\~Area Change,dat\~DAT Change,violations\~Violations Change;1,4,5:area\~Area Change,dat\~DAT Change,violations\~Violations Change]**
-   `--clean-command=<cmd>` The make command to clean the current designs. **default: clean_all**
-   `--no-clean` Do not clean the output directories before starting the flow. **Default: False**
-   `--excel` Generate the report in Excel format. **default: True**
-   `--no-color-delta` Disable coloring for values starting with + or - as Green or Red respectively. **default: False**
-   `--csv` Generate the report in csv format. **default: False**
-   `--html` Generate the report in html format. **default: False**
-   `--json` Generate the report in json format. **default: False**
-   `--quiet` Suppres flow run messages **default: False**
-   `-o --out=<dir>` Output file name (without extension). **default: ./report**
-   `--design-path-pattern=<path>` The pattern that will be used to map the design to configuration file. **default: ./designs/{}\_{}.mk**
-   `--make-cmd=<cmd>` The path/command to run the make tool. **default: make**
-   `--design-config-var=<var>` The variable used to set the design configuration file in the Makefile. **default: DESIGN_CONFIG**

## Adding reports for another tool

To support reports from another tool, you need to create a new subdirectory under tool root dir, you then need to export a class named `Reporter` that inherits from BaseReporter and implements `parse` and `map` methods. You can then use the new module by passing the subdirectory name to the option `--tool=<tool>`. Refer to the Resizer reporter (`./resizer`) for reference.

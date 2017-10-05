# compare_gw

HGS generate observation well output provides measurements like head, soil moisture, and elevation for 
each simulation time step in block format. The purpose of this script is to post process the data into
column format and perform transformation including:
*convert head to depth
*convert simulation time to real time
*average data on weekly average
		
## Usage

* read_raw_obs: read hgs observation well output (block format)

* reorder_raw2column: convert bloc format to column format

* head_to_depth: convert head to depth from surface elevation

* to_realtime: convert simulation time (in seconds) to ISO time 

* avg_weekly: averge all the columns on ISO calender week

* op: output the processed data as CSV format

## Prerequisites

*hgs_tools* need to be installed, and it is avalaible at "\\\aqfs1\Data\temp_data_exchange\Fan\HGS_tools". The source code is avaliable at [repository](https://github.com/namedyangfan/HGS)

```
to install the wheel file, type in the following in the terminal

pip install hgs_tools-1.3-py3-none-any.whl
```

# Method

## *class* compare_gw( *file_directory, file_name* )
 * file_directory: directory of the *.observation_well_flow.* file.
 * file_name: *.observation_well_flow.* file name 
```
Obs_well_hgs( file_directory = file_directory, file_name='ARB_QUAPo.observation_well_flow.Baildon059.dat')
```

### compare_gw. **read_raw_obs()**
read the *.observation_well_flow.* file generated by HGS.

### compare_gw. **reorder_raw2column(*var_names = ['H', 'S', 'Z'], start_sheet = None, end_sheet = None*)**
reorder the *.observation_well_flow.* data to column format

- var_names: a list of variables read from the *.observation_well_flow.* file. The default read *H*,*S*, and *Z*.
		
- start_sheet/end_sheet: HGS models usually have multiple sheets. The variables from *start_sheet* to *end_sheet* are extracted. Note: the layer numbering in HGS counts from the botom. Sheet 1 means bottom layer.


### compare_gw. **head_to_depth()**

calcualte the depth of groundwater head. The elevation of the top sheet is used to calcualte depth from head. *end_sheet* from compare_gw. **reorder_raw2column()** should be set as the number of the top sheet.

### compare_gw. **to_realtime(t0 = '2002-01-01T00:00:00Z')**

convert simulation time to real time. 
- t0: the starting date of the simulation in ISO8601 format

### compare_gw. **avg_weekly(date_format = None)**
take the weekly average of all the variables. 

if date_format is provided, the following variables are produced:
- date_mid_week: [Gregorian Calender](https://www.staff.science.uu.nl/~gent0113/calendar/isocalendar.htm) year month and mid of week
- date_mid_week_numeric: date_mid_week expressed in Excel date format
```
compare_gw.avg_weekly(date_format= 'YYYYMMDD')

output:
"date_mid_week" : 20020102
"date_mid_week_numeric": 37258
```
### compare_gw. op(op_folder, zone_name = None, float_format = '%.6f')
output the data in Tecplot format
- op_folder: a directory of the output.
- zone_name: output file name, also zone name in Tecplot
- float_format: digit number for float

# Examples
## reorder *.observation_well_flow.*
```
file_directory = r'./test_data/Obs_well_hgs'
file_name = 'ARB_QUAPo.observation_well_flow.Baildon059.dat'
test = Obs_well_hgs( file_directory = file_directory, file_name=file_name)
# read 'ARB_QUAPo.observation_well_flow.Baildon059.dat'
test.read_raw_obs()
# extract variables H, Z, and S from sheet 3 to sheet 6. Then reorder the data to column format
test.reorder_raw2column(var_names = ['H', 'Z', 'S'], start_sheet = 3, end_sheet = 6, ldebug=False)
# save data in tecplot format
test.op(op_folder = r'./test_data/Obs_well_hgs/output', zone_name = 'Baildon059_reorder')
```
## convert head(H) to depth 
```
file_directory = r'./test_data/Obs_well_hgs'
file_name = 'ARB_QUAPo.observation_well_flow.Baildon059.dat'
test = Obs_well_hgs( file_directory = file_directory, file_name=file_name)
test.read_raw_obs()
test.reorder_raw2column(var_names = ['H', 'Z', 'S'], start_sheet = 3, end_sheet = 6, ldebug=False)
test.head_to_depth()
test.op(op_folder = r'./test_data/Obs_well_hgs/output', zone_name = 'Baildon059_head_2_depth')
```
## convert simulation time to real time
```
file_directory = r'./test_data/Obs_well_hgs'
file_name = 'ARB_QUAPo.observation_well_flow.Baildon059.dat'
test = Obs_well_hgs( file_directory = file_directory, file_name= file_name)
test.read_raw_obs()
test.reorder_raw2column(var_names = ['H', 'Z', 'S'], start_sheet = 3, end_sheet = 6, ldebug=False)
test.to_realtime(t0 = '2002-01-01T00:00:00Z')
test.op(op_folder = r'./test_data/Obs_well_hgs/output', zone_name = 'Baildon059_realtime')
```
## take weekly average of soil moisture
```
file_directory = r'./test_data/Obs_well_hgs'
file_name = 'ARB_QUAPo.observation_well_flow.Baildon059.dat'
test = Obs_well_hgs( file_directory = file_directory, file_name= file_name)
test.read_raw_obs()
test.reorder_raw2column(var_names = ['H', 'Z', 'S'], start_sheet = 5, end_sheet = 6, ldebug=False)
test.to_realtime(t0 = '2002-01-01T00:00:00Z')
test.avg_weekly(date_format= 'YYYYMMDD')
test.op(op_folder = r'./test_data/Obs_well_hgs/output', zone_name = 'Baildon059_weekly_soil_moisture')
```

## Tests
A set of tests are provided: `test_compare_gw.py`. These are based on a set of output files from the Qu'Appelle sub-basin model.

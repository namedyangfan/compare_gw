from convert_tecplot import hgs_loadfile as hl
from convert_tecplot import csv_tecplot
import os, errno, re, arrow
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

class Obs_well_hgs():

    def __init__(self, file_directory, file_name):
        ''' 
        HGS generate observation well output provides measurements like head, soil moisture, and elevation for 
        each simulation time step in block format. The purpose of this script is to post process the data into
        column format and perform transformation including:
        
            convert head to depth
            convert simulation time to real time
            average data on weekly average
    
        Usage:

            read_raw_obs: read hgs observation well output (block format)

            reorder_raw2column: convert bloc format to column format
            
            head_to_depth: convert head to depth from surface elevation
            
            to_realtime: convert simulation time (in seconds) to ISO time 

            avg_weekly: averge all the columns on ISO calender week

            op: output the processed data as CSV format
        '''

        self.file_directory = file_directory
        self.file_name = file_name
        self.file_path = os.path.join(self.file_directory, self.file_name)
        if not os.path.exists(self.file_path):
            print("Folder not found: {0}".format(self.file_path))
        return None

    def read_raw_obs (self, ldebug=False):
        ''' read block formatted observation well data'''
        ## initialize number of sheet in the file
        num_sheet = 0
        ## initialize variable names 
        var_name = []
        ## initialize 
        line_start = None
        line_end = None

        ## read the variable name and calcualte the number of layers
        with open(self.file_path, 'r') as handl:
            for num,line in enumerate(handl):
                line = line.strip()
                if line.lower().startswith ("variable"):
                    header = line.strip() [11:]
                else:
                    if re.match(r"^\d+.*$",line) and not line_start:
                        line_start = num
                    elif line_start and not re.match(r"^\d+.*$",line):
                        line_end = num
                        break

        column_names = header.replace('"'," ").replace(','," ").split(' ')
        self.column_names = [x for x in column_names if x]
        self.num_sheets = line_end - line_start
        if ldebug: print('number of sheets: {}'.format(line_end - line_start))

        ## read chunk as list
        with open(self.file_path, 'r') as handl:
            chunk = list(line.strip().split() for line in handl if re.match(r"^\d+.*$",line.strip()))
            # convert chunk to dataframe
            # data frame is easier for sheet slicing
            self.chunk_df = pd.DataFrame(chunk)
            self.chunk_df.columns = self.column_names
        with open(self.file_path, 'r') as handl:
            self.timeseries = list( float(line.split()[-1]) for line in handl if line.strip().startswith('zone') )

    def reorder_raw2column (self, var_names = ['H', 'S', 'Z'], start_sheet = None, end_sheet = None, ldebug=False):
        ''' reorder the simulated well data to column format
        hgs counts sheet bottom up, the observation well output is bottom up as well
        start_sheet: sheet number count from model bottom
        end_sheet: sheet number count from model bottom
        '''
        ## take all the sheets if start_sheet or end sheet is not specified
        if not start_sheet: start_sheet = 1

        if not end_sheet: end_sheet = self.num_sheets

        if end_sheet<start_sheet: raise ValueError('start_sheet "{}" and end_sheet"{}" are incorrect'.format(start_sheet, end_sheet))
        
        if end_sheet>self.num_sheets: raise ValueError('end_sheet"{}" are incorrect'.format(end_sheet))
        
        ## convert dataframe to matrix easier for slicing
        chunk_array = self.chunk_df.values
        ## slice row by the from start sheet to end sheet for each variable 
        ## sheet start from '1' and index start from '0'
        n = ((chunk_array[sheet::self.num_sheets,self.column_names.index(var)]) for sheet in range(start_sheet-1,end_sheet) for var in var_names)
        ## convert to datafrmae and change column name
        col_name = list('{}{}'.format(var,sheet) for sheet in range(start_sheet, end_sheet+1) for var in var_names)
        self.df = pd.DataFrame.from_records(list(n)).T
        self.df = self.df.apply(pd.to_numeric)
        self.df.columns = col_name
        ## add timestamp 
        self.df.insert(0,'time', self.timeseries)
        if ldebug: print(self.df.head())
        

    def open_obs(self):
        
        self.df = hl.read_tecplot(file_directory=self.file_directory, file_name=self.file_name, sep='\s')

    def head_to_depth(self, ldebug=False):
        '''calcualte the depth of groundwater head
        Assumptions:
        1 df is either opened via open_obs or processed via reorder_raw2column
        2 df has column format as "time" "H5" "Z5" "H6" "Z6"
        3 in the above case, two layer is detected and Z6 is the surface elevation
        '''
        try:
            self.df.columns
        except:
            self.df = self.df

        ## get the head columns
        head_sheets = list(x for x in self.df.columns if re.search('H', x))
        if len(head_sheets) <1: raise ValueError('Head:(H) is not found. {}'.format(self.df.head()))
        self.num_sheet = head_sheets[-1][-1]
        if ldebug: print('Surface Layer Number: {}'.format(self.num_sheet))

        #get the surface elevation
        top_elev_var = 'Z' + self.num_sheet
        if ldebug: print('Top elevation: \n {}'.format(self.df[top_elev_var].head()))
        
        for sheet in head_sheets:
            depth_var = 'depth_' + sheet
            self.df[depth_var] = self.df[top_elev_var].astype(float) - self.df[sheet].astype(float)
        if ldebug: print(self.df.head())

    def to_realtime(self, t0 = '2002-01-01T00:00:00Z', ldebug=False):
        ''' convert simulation time to realtime. t0: start of the simulation '''
        if not 'time' in self.df.columns: raise ValueError('"time" is not found \n {}'.format(self.df.head()))
        self.t0 = t0
        self.df['elapsed_time']  = self.df['time']
        self.df['time']  = self.df['time'].map(lambda t: arrow.get(t0).shift(seconds=+t)) # ".replace" is replaced by ".shift"

    def avg_weekly(self, date_format = None, ldebug=False):
        ''' take the weekly average of all the variables
            if date_format is provided, the following variables are produced:
                date_mid_week: Gregorian Calender year month and mid of week
                date_mid_week_numeric: date_mid_week expressed in Excel date format
        '''
        ## check if time has been converted to ISO format
        ## defination of ISO calender https://www.staff.science.uu.nl/~gent0113/calendar/isocalendar.htm
        if not isinstance(self.df['time'][0], arrow.Arrow):
            print('time is not instance of arrow. \n{} '.format(self.df['time'].head()))

        ## convert date to year week
        self.df['ISO_week'] = self.df['time'].map(lambda t: t.isocalendar()[1])
        self.df['ISO_year'] = self.df['time'].map(lambda t: t.isocalendar()[0])
        if ldebug: print('Data before aggregation: \n {}'.format(self.df.head(10)))

        ## This is to show ISO year can be different from nomal year
        # list(print(i) for i in self.df.time if i.isocalendar()[0] != i.year) 

        ## weekly mean for each year
        self.df = self.df.groupby(['ISO_year','ISO_week'], sort=False, as_index=False).mean()
        if ldebug: print('Data after aggregation: \n {}'.format(self.df.head(10)))

        ## write date_mid_week '20020102' and its numeric form
        if date_format: 
            ## assume: Wednesday (middle of week)
            self.df.insert(0,'date_mid_week', self.df['ISO_year'].astype(str) + '-' + self.df['ISO_week'].astype(str) + '-3' )
            try:
                ## arrow.Arrow.strptime(x, "%G-%V-%w") takes ISO_year and ISO_week produce regular date. 
                self.df['date_mid_week'] = self.df['date_mid_week'].apply(lambda x: arrow.Arrow.strptime(x, "%G-%V-%u").format(date_format))
            except:
                raise ValueError('Not able to write date format {}. \n {}'.format(date_format, self.df['date_mid_week'].head()))
            ## write numeric date
            try:
                self.df['date_mid_week_numeric']= hl.time_to_numeric(self.df['date_mid_week'], format = date_format)
            except:
                raise ValueError('Not able to write date format {}. \n {}'.format(date_format, self.df['date_mid_week'].head()))
            
    def op (self, op_folder, zone_name = None, float_format = '%.6f'):
        if not zone_name:
            zone_name = os.path.splitext(self.file_name)[0]
        csv_tecplot(df = self.df, save_folder = op_folder, zone_name = zone_name, float_format=float_format)

class Compare_simu2obs():

    def __init__(self,obs_direct,obs_fn,simu_direct,simu_fn,obs_var = ['date' ,'DTGS'],t0="2002-01-01"):
        ''' 
        plot the simulated groundwater head versus the modeled groundwater head

        Assumption:
            Observed gw data:
                1. file is in tecplot format and comma seperated
                1. variable 'date' and 'DTGS' will be used
                2. file name must include or match the filename of the modeled data
                3. 'time' is in excel format
            Modeled gw data:
                1. variable 'time' and 'depth_H[1-7]' will be used 
                2. file name must be included in the file name of 
                3. 'time' is in simulation time
        '''
        self.obs_var = obs_var
        self.obs_direct = obs_direct
        self.obs_fn = obs_fn
        self.obs_path = os.path.join(self.obs_direct, self.obs_fn)
        self.simu_direct = simu_direct
        self.simu_fn = simu_fn
        self.simu_path = os.path.join(self.simu_direct, self.simu_fn)
        self.t0 = t0

    def read_files(self, ldebug=False):
        self.obs_df = hl.read_tecplot(file_directory=self.obs_direct, file_name=self.obs_fn, sep=',')
        if ldebug: print(self.obs_df.head())
        self.simu_df = hl.read_tecplot(file_directory=self.simu_direct, file_name=self.simu_fn, sep=',')
        if ldebug: print(self.simu_df.head())

        ## get the H_depth variable from simulated data
        ## the simulated data contain many variables, but only the depth need to be compared
        depth_var = [x for x in self.simu_df.columns if 'depth' in x]
        try: self.simu_df = self.simu_df [['time'] + depth_var]
        except: raise ValueError('Not able to read "time" from: {}'.format(self.simu_path))
        ## changde time to date
        t0_numeric = hl.time_to_numeric(self.t0, format='%Y-%m-%d')
        self.simu_df['time'] = self.simu_df['time'] /86400 + t0_numeric
        if ldebug:
            print(self.simu_df.head())
            print(self.obs_df.head())

    def plot_depth(self, o_folder,ldebug=False):
        ''' Plot the observed versus the simulated '''
        ## assume: plotting depth_H2 and depth_H3 in the simulation files
        if not os.path.exists(o_folder):
            print("Folder not found: {0}".format(o_folder))
            return None
        o_path = os.path.join(o_folder, os.path.splitext(self.obs_fn)[0])
        if ldebug:
            print(os.path.splitext(self.obs_fn)[0])
            print(o_folder)
            print(o_path)
        ## set minimum number of lines  
        minline= 50
        ## check if there is enough data to plot
        if self.obs_df.shape[0] >= minline:
            fig = plt.figure()
            plt.plot(self.simu_df['time'], self.simu_df['depth_H2'])
            plt.plot(self.simu_df['time'], self.simu_df['depth_H3'])
            plt.plot(self.obs_df['date'], self.obs_df['DTGS'])
            plt.xlim([self.simu_df['time'].min(), self.simu_df['time'].max()])
            plt.legend()
            plt.xlabel('Date')
            plt.ylabel('Depth')
            plt.savefig(o_path)
            plt.close()
        else:
            print('{} has less than {} lines \n no plot is generated for this station'.format(self.obs_fn, minline))

if __name__ == "__main__":
    file_directory = r'./test_data/Obs_well_hgs'
    file_name = 'G05MD001.dat'


    # test2 = Compare_simu2obs(obs_direct = r"./test_data/Compare_simu2obs",
    #                         obs_fn = "38973_G05MH030.dat",
    #                         simu_direct = r"./test_data/Compare_simu2obs",
    #                         simu_fn = "G05MH030.dat")
    # test2.read_files()
    # test2.plot_depth(o_folder=r"./test_data/Compare_simu2obs")

    ## test Obs_well_hgs
    test2 = Obs_well_hgs( file_directory = file_directory, file_name='ARB_QUAPo.observation_well_flow.Baildon059.dat')
    test2.read_raw_obs( ldebug=False)
    test2.reorder_raw2column(var_names = ['S'], start_sheet = 5, end_sheet = 6, ldebug=False)
    test2.to_realtime()
    test2.avg_weekly(date_format= 'YYYYMMDD')
    # test2.head_to_depth(ldebug=False)
    test2.op(op_folder = r"D:\git\HGS_tools\compare_data\test_data\Obs_well_hgs\output")

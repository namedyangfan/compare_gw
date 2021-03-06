from compare_data.compare_gw import Obs_well_hgs
import unittest
import os

file_directory = os.path.join(os.getcwd(), 'test_data')
output_folder = os.path.join(file_directory, "output")
if not os.path.exists(output_folder):
    os.mkdir(output_folder)

class TestStringMethods(unittest.TestCase):

    def test_reorder_hgsoutput(self):
        file_name = 'ARB_QUAPo.observation_well_flow.Baildon059.dat'
        test = Obs_well_hgs( file_directory = file_directory, file_name=file_name)
        test.read_raw_obs()
        test.reorder_raw2column(var_names = ['H', 'Z', 'S'], start_sheet = 3, end_sheet = 6, ldebug=False)
        test.op(op_folder = output_folder, zone_name = 'Baildon059_reorder')

    def test_reorder_hgsoutput_heat2depth(self):
        file_name = 'ARB_QUAPo.observation_well_flow.Baildon059.dat'
        test = Obs_well_hgs( file_directory = file_directory, file_name=file_name)
        test.read_raw_obs()
        test.reorder_raw2column(var_names = ['H', 'Z', 'S'], start_sheet = 3, end_sheet = 6, ldebug=False)
        test.head_to_depth()
        test.op(op_folder = output_folder, zone_name = 'Baildon059_head_2_depth')

    def test_simutime2realtime(self):
        file_name = 'ARB_QUAPo.observation_well_flow.Baildon059.dat'
        test = Obs_well_hgs( file_directory = file_directory, file_name= file_name)
        test.read_raw_obs()
        test.reorder_raw2column(var_names = ['H', 'Z', 'S'], start_sheet = 3, end_sheet = 6, ldebug=False)
        test.to_realtime(t0 = '2002-01-01T00:00:00Z')
        test.op(op_folder = output_folder, zone_name = 'Baildon059_realtime')

    def test_weekly_soilmoisture(self):
        file_name = 'ARB_QUAPo.observation_well_flow.Baildon059.dat'
        test = Obs_well_hgs( file_directory = file_directory, file_name= file_name)
        test.read_raw_obs()
        test.reorder_raw2column(var_names = ['H', 'Z', 'S'], start_sheet = 5, end_sheet = 6, ldebug=False)
        test.to_realtime(t0 = '2002-01-01T00:00:00Z')
        test.avg_weekly(date_format= 'YYYYMMDD')
        test.op(op_folder = output_folder, zone_name = 'Baildon059_weekly_soil_moisture')

if __name__ == '__main__':
    unittest.main()
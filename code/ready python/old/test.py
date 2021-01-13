import pandas as pd

test_output = pd.read_pickle('output_files/robot_moves_wh1.p')

test_output.to_csv('test.csv')
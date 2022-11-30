
import pandas as pd
import numpy as np



def running_mean(x, N):
    cumsum = np.cumsum(np.insert(x, 0, 0)) 
    return (cumsum[N:] - cumsum[:-N]) / float(N)


def convolve_dataframe(dataframe , column_list , window):
    conv_df = pd.DataFrame()
    for column in range(0,len(column_list)):
        n_array = dataframe[column_list[column]].to_numpy()
        conv_df[column_list[column]] = running_mean(n_array , window)
    
    return conv_df




from unittest import result
from EnbPI import EnbPI
import numpy as np
import pandas as pd
from EnCQR import EnCQR
from MIMONaive import MIMONaive
from MIMOCQR import MIMOCQR
from AutoArima import auto_arima
import warnings
warnings.filterwarnings("ignore")

def train_cal_val_split(X,y):
    N=X.shape[0]
    ntrain=int(N/2)
    ncal=int((N-ntrain)/2)
    nval=N-ntrain-ncal

    X_train,y_train,X_cal,y_cal,X_val,y_val=X[:ntrain],y[:ntrain],X[ntrain:ntrain+ncal],y[ntrain:ntrain+ncal],X[-nval:],y[-nval:]

    return X_train,y_train,X_cal,y_cal,X_val,y_val

def phi(arr):
    return np.mean(arr)

def to_supervised(timeseries,n_lags,n_output=1):
    
    N=len(timeseries)
    X=np.zeros((N-n_lags-n_output+1,n_lags))
    y=np.zeros((X.shape[0],n_output))
    
    for i in range(N-n_lags):
        aux=np.zeros(n_lags)
        for j in range(i,i+n_lags,1):
            aux[j-i]=timeseries[j]
        if i+n_lags+n_output<=N:
            X[i,:]=aux
            y[i,:]=timeseries[i+n_lags:i+n_lags+n_output]

    return X,y

def summary_coverage_widths(conf_PIs,y_test_rec):
    interval_width=np.ones(len(conf_PIs))

    counter=0
    for i in range(len(conf_PIs)):
        lower_bound=conf_PIs[i][0]
        upper_bound=conf_PIs[i][1]

        if y_test_rec[i]>lower_bound and y_test_rec[i]<upper_bound:
            counter+=1
            interval_width[i]=np.abs(upper_bound-lower_bound)
    
    #interval_width=(interval_width-np.min(interval_width))/(np.max(interval_width)-np.min(interval_width))

    return counter/len(y_test_rec),summary_statistics(interval_width)

def summary_statistics(arr):
    # calculates summary statistics from array
    
    return [np.quantile(arr,0.5),np.quantile(arr,0.75)-np.quantile(arr,0.25)]

def normalize(arr):

    return (arr-np.min(arr))/(np.max(arr)-np.min(arr))



if __name__=='__main__':
    data=pd.read_csv('NN5.csv')
    data=data.fillna(0)
    timesteps=40
    H=30
    alpha=0.1
    cols=data.columns
    aux1=[]
    aux2=[]
    aux3=[]
    aux4=[]
    aux5=[]
    results_cols=['coverage','median','IQR']


    for col in cols:
        print(col)
        
        ts=normalize(data[col].values)
        arima=auto_arima(ts[:-H],ts[-H:],timesteps,H,alpha)
        results=arima.calculate_metrics()
        aux5.append([results[0],results[1][0],results[1][1]])

        X,y=to_supervised(normalize(data[col].values),n_lags=timesteps,n_output=H)
        X_train,y_train,X_cal,y_cal,X_val,y_val=train_cal_val_split(X,y)
        mimonaive=MIMONaive(X_train,y_train,X_cal,y_cal,X_val,y_val,alpha)
        results=mimonaive.calculate_coverage()
        aux1.append([results[0],results[2][0],results[2][1]])
        mimocqr=MIMOCQR(X_train,y_train,X_cal,y_cal,X_val,y_val,100,alpha)
        results=mimocqr.calculate_coverage()
        aux2.append([results[0],results[2][0],results[2][1]])

        X_rec,y_rec=to_supervised(normalize(data[col].values),n_lags=timesteps,n_output=1)
        X_train_rec,y_train_rec,X_test_rec,y_test_rec=X_rec[:-H],y_rec[:-H],X_rec[-H:],y_rec[-H:]
        enbpi=EnbPI(10,alpha,1,X_train_rec,y_train_rec,X_test_rec,y_test_rec,timesteps,H,phi)
        conf_PIs=enbpi.Conf_PIs()
        results=summary_coverage_widths(conf_PIs,y_test_rec)
        aux3.append([results[0],results[1][0],results[1][1]])
        encqr=EnCQR(10,alpha,1,X_train_rec,y_train_rec,X_test_rec,y_test_rec,timesteps,H,phi)
        conf_PIs=encqr.Conf_PIs()
        results=summary_coverage_widths(conf_PIs,y_test_rec)
        aux4.append([results[0],results[1][0],results[1][1]])
        

        lst_results=[]
        lst_results.append(np.median(aux5,axis=0))
        lst_results.append(np.median(aux1,axis=0))
        lst_results.append(np.median(aux2,axis=0))
        lst_results.append(np.median(aux3,axis=0))
        lst_results.append(np.median(aux4,axis=0))
        df_results=pd.DataFrame(lst_results,columns=results_cols)
        print(df_results.to_latex())



 
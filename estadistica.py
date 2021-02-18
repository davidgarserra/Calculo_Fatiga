# -*- coding: utf-8 -*-
"""
Created on :

@author: David García Serrano
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt 
from sklearn.linear_model import LinearRegression

def regresion(par,vida_estimada, vida_experimental):
    """Cálculo de la recta de regresion entre la vida estimada y la vida experimental
    INPUTS:
        par: parámetro de los cálculos (SWT o FS)   

        vida_estimada: ubicación del archivo.dat con los resultados de todos los experimentos

        vida_experimental: ubicacion del archivo.xlsx con los datos de todos los experimentos de
    
    OUTPUTS:
        figura: Gráfica con la representación de los puntos, la recta de regresion y los
        datos de los coeficientes.

    """

    data_exp = pd.read_excel(vida_experimental,index_col=0) #datos de vida experimental

    #podemos cargar los datos en formato .dat o .xlsx
    try:
        data_est =pd.read_table(vida_estimada,sep=r"\s+",skiprows =1, names =["exp_id", "param","N_t_min","N_i_min", "N_p_min","N_i_perc","N_p_perc","a_inic" ])
        
    except:
        data_est = pd.read_excel(vida_experimental)
        
    data_est =data_est[data_est.param==par] #Filtramos solo para ese parámetro 
    dict_est = {} #Diccionario con las datos estimados


    for j,exp in enumerate(data_est.exp_id): #Rellenamos los diccionarios con el valor N_t_min
        dict_est[exp]=data_est.iloc[j].N_t_min

    exps = data_exp.columns.values[1:] #vector de columnas de data_exp menos el primer elemento que es el 6629_971_70

    #Cargamos el Dataframe con todos los datos.
    Df_est_exp = pd.DataFrame() 
    Df_est_exp["exp_id"]=exps
    Df_est_exp["vida_estimada"]=[dict_est[i] for i in exps]
    Df_est_exp["vida_experimental1"]=[data_exp[i].values[0] for i in exps]
    Df_est_exp["vida_experimental2"]=[data_exp[i].values[1] for i in exps]
    Df_est_exp["vida_est_log"] =np.log10(Df_est_exp.vida_estimada)
    Df_est_exp["vida_exp_log1"] =np.log10(Df_est_exp.vida_experimental1)
    Df_est_exp["vida_exp_log2"] =np.log10(Df_est_exp.vida_experimental2)
    
    
    
    #Hacemos la regresion con los logaritmos 
    x =np.concatenate((Df_est_exp.vida_est_log.values,Df_est_exp.vida_est_log.values))
    y =np.concatenate((Df_est_exp.vida_exp_log1.values,Df_est_exp.vida_exp_log2.values))
    
    #Modelo de regresión lineal
    Lm= LinearRegression(fit_intercept=True)
    try:
        Lm.fit(x.reshape(-1,1),y.reshape(-1,1))
    except:
        Lm.fit(x.reshape(-1,1),y.reshape(-1,1))

    a= Lm.coef_[0] #Pendiente de la recta de regresión
    b = Lm.intercept_ #Residual de la recta de regresión
    r =Lm.score(x.reshape(-1,1),y.reshape(-1,1)) # Coeficiente de correlación
    xs = np.array([0,10]) 
    ys = a*xs+b #Recta de regresión

    #Deshacemos logaritmos
    xs = 10**xs
    ys =10**ys 

    x = 10**x
    y =10**y

    # plt.figure(figsize =(5,5))
    plt.plot(x,y,"ob")
    plt.xscale("log")
    plt.yscale("log")
    plt.xlim([np.min(x)*0.5,np.max(x)*2])
    plt.ylim([np.min(x)*0.5,np.max(x)*2])
    plt.xlabel('Vida estimada')
    plt.ylabel('Vida experimental')
    plt.plot([1e1,1e10],[1e1,1e10],'--r',label ="Recta de equivalencia") #recta
    plt.plot(xs,ys,"--g",label ="Recta de regresión")
    plt.plot([1e1,1e10],[0.5e1,0.5e10], "--y")
    plt.plot([1e1,1e10],[2e1,2e10], "--y")
    plt.legend()
    plt.grid()
   
def grafica_lon_vida(par,vida_estimada):
    """Función que representa la vida estimada en una grafica la longitud de inciación 
    con respecto a los ciclos
    INPUTS: 
        -par: criterio FS o SWT
        -vida estimada: datos con los resultados de cálculos de vida a fatiga
    
    OUTPUTS:
        -fig: Figura

    """

    #Carga de datos
    try:

        data_est =pd.read_table(vida_estimada,sep=r"\s+",skiprows =1, names =["exp_id", "param","N_t_min","N_i_min", "N_p_min","N_i_perc","N_p_perc","a_inic" ])
    except:
        data_est = pd.read_excel(vida_estimada)

    data_est = data_est[data_est.param == par]

    x = data_est.N_i_min.values
    y = data_est.a_inic.values

    fig = plt.figure(figsize=(5,3))

    plt.plot(x,y,'ob')
    plt.xscale('log')
    plt.ylim([0,1])
    plt.xlim([1e2,1e5])
    plt.xlabel('Vida estimada')
    plt.ylabel('a_inic(mm)')
    plt.grid(which = 'major', color = 'k', linestyle='-', linewidth=0.4)
    plt.grid(which = 'minor', color = 'gray', linestyle=':', linewidth=0.2)

    return fig


def grafica_per_vida(par,vida_estimada):
    """Función que representa la vida estimada en una grafica el porcentaje
    de vida que se lleva la iniciación. 
    INPUTS: 
        -par: criterio FS o SWT
        -vida estimada: datos con los resultados de cálculos de vida a fatiga
    
    OUTPUTS:
        -fig: Figura


    """
    
    try:
        data_est =pd.read_table(vida_estimada,sep=r"\s+",skiprows =1, names =["exp_id", "param","N_t_min","N_i_min", "N_p_min","N_i_perc","N_p_perc","a_inic" ])
    except:
        data_est = pd.read_excel(vida_estimada)
    data_est = data_est[data_est.param == par]

    x = data_est.N_i_min.values
    y = data_est["N_i_perc"].values
    y =np.array([float(i[:-1]) for i in y])

    fig = plt.figure(figsize=(5,3))

    plt.plot(x,y,'ob')
    plt.xscale('log')
    plt.ylim([0,100])
    plt.xlim([1e2,1e5])
    plt.xlabel('Vida estimada')
    plt.ylabel('Porcentaje de iniciación %')
    plt.grid(which = 'major', color = 'k', linestyle='-', linewidth=0.4)
    plt.grid(which = 'minor', color = 'gray', linestyle=':', linewidth=0.2)

    return fig



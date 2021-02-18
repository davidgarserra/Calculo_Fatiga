# -*- coding: utf-8 -*-
"""
Created on:

@author: David García y Alejandro Quirós
"""

import os
# import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import ticker
from scipy.optimize import minimize
from scipy.interpolate import interp2d, interp1d
from propagacion import fase_propagacion,MAT
import pandas as pd
from time import time
import re

def lectura_datos(ruta, exp_max, exp_min):
    
    """Carga los datos experimentales.
    
    INPUT:   ruta    = ruta para cargar los datos experimentales
             exp_max = nombre del archivo con la tensiones y defs maximas
             exp_min = nombre del archivo con la tensiones y defs minimas
             
    OUTPUTS: x       = (m) vector de distancias a la superficie de la grieta
             sxx_max = (MPa) vector de tensiones máximas en la direccion x
             s_max   = (MPa) vector de tensiones máximas
             e_max   = vector de deformaciones máximas
             e_min   = vector de deformaciones minimas"""

    cols = ["X", "Y", "s_xx", "s_yy","s_zz", "s_xy", "s_xz","s_yz", "e_xx", "e_yy", "e_zz", "e_xy", "e_xz", "e_yz"]
             
    #Cargamos los datos de distancias. Cambiamos el vector para
    #que sea positivo y empiece en 0
    datos_max = pd.read_csv(f"{ruta}/{exp_max}.dat",skiprows=1,sep=' ',names=cols) #todos los datos para las tracciones
    datos_min = pd.read_csv(f"{ruta}/{exp_min}.dat",skiprows=1,sep =' ',names=cols) #todos los datos para las compresiones
    
    x = datos_max.Y.to_numpy()*(-1e-3)-0.1
  
    #Cargamos el resto de datos
    sxx_max = datos_max.s_xx.to_numpy().tolist()
    
    s_max = datos_max[["s_xx", "s_yy","s_zz", "s_xy", "s_xz","s_yz"]].to_numpy()
    
    e_max = datos_max[["e_xx", "e_yy", "e_zz", "e_xy", "e_xz", "e_yz"]].to_numpy()
        
    e_min = datos_min[["e_xx", "e_yy", "e_zz", "e_xy", "e_xz", "e_yz"]].to_numpy()
    return x, sxx_max, s_max, e_max, e_min

###############################################################################    
###############################################################################

def indice_a(a, x):
    """Devuelve el indice asociado a una longitud de grieta.
    
    INPUT:   a     = longitud de grieta de iniciacion
             x     = vector de distancias a la superficie
             
    OUTPUTS: ind_a = indice asociado a la longitud de grieta de iniciacion"""
    a = round(a,8)
    #Calculamos el índice para el cual tenemos esa longitud de grieta
    for i,x0 in enumerate(x):
        if round(x0,8) >= a:
            ind_a = i
            break    
    
    return ind_a

###############################################################################    
###############################################################################
def rotar_matriz(alfa,matriz):
        """Devuelve una matriz rotada según los angulos almacenados en  alfa.

        -alfa: array de 3 componentes con los ángulos
        -matriz: matriz de 3x3"""
        matriz = np.array(matriz)
        R_x   = np.array([[1.0,         0.0,                  0.0],
                          [0.0, np.cos(alfa[0]), -np.sin(alfa[0])], 
                          [0.0, np.sin(alfa[0]), np.cos(alfa[0])]])
        
        R_y   = np.array([[np.cos(alfa[1]), 0.0, -np.sin(alfa[1])],
                          [0.0,             1.0,             0.0], 
                          [np.sin(alfa[1]), 0.0, np.cos(alfa[1])]])
        
        R_z   = np.array([[np.cos(alfa[2]), -np.sin(alfa[2]), 0.0], 
                          [np.sin(alfa[2]), np.cos(alfa[2]), 0.0],
                          [0.0,              0.0,            1.0]])
        R = R_x @ R_y @ R_z

        return (R.T @ matriz @ R)

def hacer_matriz(vector,i=0):
    """Devuelve una matriz a partir del vector de tensiones o                deformaciones.

    INPUT:   
    - vector: array de seis componentes
    - i: fila del vector

    OUTPUT:
    - m: matriz de componentes del vector
    """
    vector = np.array(vector)
    m = np.array([[vector[i,0], vector[i,3], vector[i,4]],
                              [vector[i,3], vector[i,1], vector[i,5]],
                              [vector[i,4], vector[i,5], vector[i,2]]])
    return m
    

def parametro(par, MAT, x, s_max, e_max, e_min):
    """Calcula el vector para el modelo de iniciacion asociado 
    a un experimento.
    
    INPUT:   par    = parametro para el modelo de iniciacion      
             MAT    = indice asignado al material
             x      = (m) vector de distancias a la superficie de la grieta
             s_max  = (MPa) vector de tensiones máximas
             e_max  = vector de deformaciones máximas
             e_min  = vector de deformaciones minimas

    OUTPUTS: FS/SWT = vector con los Fatemi-Socie o Smith-Watson-Topper en cada
             punto"""    
        
    def func_FS(alfa, j):
        """"Devuelve delta_gamma_max/2 en un punto concreto. Se utiliza en el
        calculo del Fatemi-Socie."""
        E_xyz_max = hacer_matriz(e_max,j)
        E_xyz_min = hacer_matriz(e_min,j)
        E_max = rotar_matriz(alfa,E_xyz_max)
        E_min = rotar_matriz(alfa,E_xyz_min)
        
        
        #El signo negativo se debe a que la función minimiza en vez de
        #maximizar.
        return -(E_max[0,1] - E_min[0,1])
        
        
    def func_SWT(alfa, j):
        """"Devuelve el Smith-Watson-Topper asociado a un punto."""
        E_xyz_max = hacer_matriz(e_max,j)
        E_xyz_min = hacer_matriz(e_min,j)
        E_max = rotar_matriz(alfa,E_xyz_max)
        E_min = rotar_matriz(alfa,E_xyz_min)
        S_xyz_max = hacer_matriz(s_max,j)
        S_max = rotar_matriz(alfa,S_xyz_max)

        #El signo negativo se debe a que la función minimiza en vez de
        #maximizar.
        return -(S_max[0,0]*(E_max[0,0]-E_min[0,0])/2.0)
    
    #Inicializamos variables
    alfa0 = [0.0, 0.0, 0.0] #Ángulo para primera iteracion de la funcion de
                           #minimizacion
    #Limites para el angulo
    bnds = ((-np.pi, np.pi), (-np.pi, np.pi), (-np.pi, np.pi))
    
    sigma_y = MAT["sigma_y"]
    sigma_f = MAT["sigma_f"]
    k       = sigma_y/sigma_f
    
    alfa            = np.zeros((len(x),3))
    delta_gamma_max = np.zeros_like(x)
    s_norm          = np.zeros_like(x)
    FS              = np.zeros_like(x)
    SWT             = np.zeros_like(x)
    
    #Calculamos en cada punto el Fatemi-Socie o el Smith-Watson-Topper asociado
    if par == 'FS':
        for j in range(len(x)):
            fs = minimize(func_FS, alfa0, bounds = bnds, args=(j),
                            options={'disp': False})
            delta_gamma_max[j]=-fs.fun*2.0
            S_xyz_max = hacer_matriz(s_max,j)
            S_max = rotar_matriz(alfa[j,:],S_xyz_max)
            s_norm[j]=S_max[2,2]          
            FS[j]= delta_gamma_max[j]/2.0*(1.0 + k*s_norm[j]/sigma_y)
        return FS

    elif par == 'SWT':
        for j in range(len(x)):
            swt  = minimize(func_SWT, alfa0, bounds = bnds,  args=(j),
                            options={'disp': False})
            alfa[j,:]=swt.x
            SWT[j]=-swt.fun
        return SWT

###############################################################################
###############################################################################

def principal(par, W, MAT,ac,exp_max, exp_min,ruta_exp,ruta_curvas=None,main_path=""):
    """Estima la vida a fatiga.
    
    INPUTS:  par     = parametro para el modelo de iniciacion
             W       = (m) anchura del especimen        
             MAT     = indice asignado al material
             ac      = propagacion plana o eliptica
             exp_max = nombre del archivo con la tensiones y defs maximas
             exp_min = nombre del archivo con la tensiones y defs minimas
             ruta_curvas = ubicación de las curvas de iniciación
            
    OUTPUTS: resultados.dat = actualiza el archivo de resultados con la
             longitud de iniciacion y los ciclos de iniciacion, propagacion y 
             total para que se produzca el fallo
             a_inic         = longitud de grieta de iniciación
             v_ai_mm        = vector de longitudes de grietas en mm 
             N_t_min        = Ciclos de iniciación
             N_t            = Vector de ciclos totales
             N_p            = Vector de ciclos de propagación   
             N_i            = Vector de ciclos de iniciación
             N_a            = Vector de ciclos de propagación a partir de la iniciación
             exp_id.dat     = archivo con los datos de las curvas de vida"""

             
    print('Datos Experimentales:\n    {}.dat\n    {}.dat\n'.format(exp_max,
                                                                   exp_min))
    #exp_id obtiene a partir del nombre del archivo con los datos un
    #identificador del experimento. Dependiendo del nombre del archivo debe
    #modificarse.
    pattern =r"\d+_\d+_\d+"
    exp_id      = re.search(pattern,exp_max).group()

    #Obtenemos las rutas a las carpetas necesarias para los calculos 
    # cwd         = os.getcwd()
    # ruta_exp    = cwd + '/datos_experimentales'
    ruta_datos  = main_path+ '/resultados/datos/{}'.format(par)
    if ruta_curvas is None:
        ruta_curvas = main_path + '/curvas_inic/{}'.format(ac)
        data_interp = np.loadtxt("{}/MAT_{}.dat".format(ruta_curvas, par)) 
    else: 
        data_interp = np.loadtxt(ruta_curvas)
    
             
    #Cargamos los datos de las curvas de iniciación del material
 
    
    #Separamos las curvas en las variables necesarias
    x_interp = data_interp[0,1:] #Eje x de la matriz de interpolación 
    y_interp = data_interp[1:,0]          #Eje y de la matriz de interpolación
    m_N_i    = data_interp[1:,1:]          #Matriz con los ciclos de iniciación
    
    
    
    #Creamos la función de interpolación
    function_interp = interp2d(x_interp, y_interp, m_N_i, kind='quintic', 
                               bounds_error=False)
                       
    #Cargamos los datos experimentales y generamos el vector de FS o SWT
    x, sxx_max, s_max, e_max, e_min = lectura_datos(ruta_exp, exp_max,
                                                             exp_min)
    param = parametro(par, MAT, x, s_max, e_max, e_min)
    
    a_i_min = round(x[1], 8) #Tamaño mínimo de longitud de grieta de
                             #iniciacion. Redondeamos para evitar errores
                             #numericos.
    a_i_max = round(x[-1], 8) #Tamaño máximo de longitud de grieta de iniciacion
    da      = a_i_min      #Paso entre longitudes de grietas
    
    #Creamos el vector de longitudes de grieta de iniciacion
    
    v_ai = np.arange(a_i_min,a_i_max, da)#Vector de longitudes de grieta en m
    v_ai_mm = v_ai*1e3          #Vector de longitudes de grieta en mm
    
    #Calculamos los ciclos de iniciación, de propagación y totales para cada
    #longitud de grieta de iniciacion   
    #Inicializamos los ciclos
    N_i= np.zeros_like(v_ai)
    N_p= np.zeros_like(v_ai)
    N_t= np.zeros_like(v_ai)

    for i,a in enumerate(v_ai):
        ind_a     = indice_a(a, x) #Indice asociado a esa longitud de grieta
        param_med = np.mean(param[:ind_a + 1]) #Valor medio del parametro para la interpolacion
                           
        #Realizamos la interpolacion para calcular los ciclos de iniciacion
        N_i[i] = function_interp(a, param_med)[0] 

        #La interpolacion puede dar valores menores que 0 para ciclos muy bajos
        if N_i[i] < 0:
            N_i[i] = 0
        
        #Calculamos los ciclos de propagacion
        N_p[i] = fase_propagacion(sxx_max, ind_a, a,ac, da, W, MAT) 
        
        #Ciclos totales
        N_t[i] = N_i[i]+N_p[i]
        
    
    #Calculamos el numero de ciclos hasta el fallo y la longitud de iniciación
    #de la grieta, que se producen en el mínimo de la curva de ciclos totales
    N_t_min   = np.min(N_t)
    i_N_t_min = np.argmin(N_t)
    N_i_min   = N_i[i_N_t_min]
    N_p_min   = N_p[i_N_t_min]
    a_inic    = v_ai_mm[i_N_t_min]
    

    #Pintamos la figura con la evolucion de la longitud de grieta y guardamos
    #en un archivo los datos
    ciclos = open(ruta_datos + '/{}.dat'.format(exp_id), 'w')
    ciclos.write('{:<5}\t{:<12}\t{:<12}\t{:<12}\t{:<12}'.format('a_i', 'N_t', 
                                                                'N_i', 'N_p', 
                                                                'N_a'))
    
    N_a = []               #Vector de ciclos con la evolución de la grieta

    for i,ai in enumerate(v_ai):
        #Hasta la longitud de iniciacion crece como los ciclos de iniciacion
        if ai <= a_inic*1e-3:
            n_a = N_i[i]
            N_a.append(n_a)
        #A partir de la longitud de iniciacion crece de acuerdo con los ciclos
        #de propagacion
        else:
            n_a = N_a[-1] + N_p[i-1] - N_p[i]
            N_a.append(n_a)
        n_i = N_i[i]
        n_p = N_p[i]
        
        ciclos.write('\n{:.3f}\t{:.6e}\t{:.6e}\t{:.6e}\t{:.6e}'.format(ai*1e3,
                     n_i+n_p, n_i, n_p, n_a))            
    ciclos.close()

    cols = ['exp_id','param', 'N_t_min', 'N_i_min', 'N_p_min', 'N_i_perc', 'N_p_perc', 'a_inic(mm)']
    values =[exp_id, par, N_t_min, N_i_min, N_p_min, str(float(N_i_min)/N_t_min*100)+"%", str(float(N_p_min)/N_t_min*100)+"%", a_inic]

    result_dict = dict(zip(cols,values))
    if os.path.isfile(main_path+"/resultados_generales/resultados.xlsx"):
        df = pd.read_excel(main_path+"/resultados_generales/resultados.xlsx")
        if len(df[df["exp_id"] ==exp_id][df["param"]==par])>0:
            df = df.drop(df[df["exp_id"] ==exp_id][df["param"]==par].index[0])
            
        df =df.append(result_dict,ignore_index=True)
        
    else: 
        df= pd.DataFrame([result_dict])
    
    df.to_excel(main_path+"/resultados_generales/resultados.xlsx",index=False)

 
      
    print('Longitud de iniciación de la grieta: {} mm'.format(a_inic))
    print('Numero de ciclos hasta el fallo: {}\n'.format(N_t_min))

    return a_inic,v_ai_mm, N_t_min,N_t,N_p, N_i, N_a
    
def pintar_grafica_a_N(N_a, v_ai_mm,par,exp_id):
    fig = plt.figure('Longitud de grieta_{}_{}'.format(par,exp_id))
    plt.xscale('log')
    plt.xlabel('Ciclos')
    plt.ylabel('Longitud de grieta (mm)')
    plt.xlim([5e2,1e6])
    plt.grid()
    plt.plot(N_a, v_ai_mm, 'k')
    return fig
    
def pintar_grafica_a_N_todas(N_a, v_ai_mm):
    # fig = plt.figure('Longitud de grieta')
    plt.xscale('log')
    plt.xlabel('Ciclos')
    plt.ylabel('Longitud de grieta (mm)')
    plt.xlim([5e2,1e6])
    plt.grid()
    plt.plot(N_a, v_ai_mm, "k")
    
    
    
def pintar_grafica_iniciacion(a_inic,v_ai_mm, N_t_min,N_t,N_p, N_i,par, exp_id,main_path="" ):
    
    fig = plt.figure(f"{exp_id}_{par}")
    plt.title("Punto de Iniciación")
    plt.xlabel('Longitud de iniciacion (mm)')
    plt.ylabel('Ciclos')
    plt.yscale("log")
    plt.grid()
    plt.plot(v_ai_mm, N_i, 'b')
    plt.plot(v_ai_mm, N_p, 'k')
    plt.plot(v_ai_mm, N_t, 'r')
    plt.plot(a_inic, N_t_min, 'g^')
    plt.ylim([1e3,1e8])
    plt.legend(["Iniciación","Propagación" , "Total","Punto de iniciación"])
    plt.annotate(text="a_inic: {:.3f} mm\nN_inic: {:.0f}".format(a_inic,np.floor(N_t_min)),
                xy =(a_inic,N_t_min),
                xytext =(1,1e7), 
                arrowprops=dict(facecolor ="blue",width=0.1,headwidth =0.2))
    plt.savefig(main_path+"/resultados/grafs/{}/{}.png".format(par,exp_id))
    return fig
    

   
###############################################################################
###############################################################################

if __name__ == "__main__":

    par  = 'SWT'
    W     = 10e-3
    tracc = 'TENSOR_TRACCION_'
    comp  = 'TENSOR_COMPRESION_'
    exp   = ['6629_971_70', '5429_971_110',
             '5429_1257_110', '4217_1543_110',
             '5429_1543_110', '3006_971_150',
             '4217_971_150', '5429_971_150',
             '3006_1543_150', '4217_1543_150',
             '5429_1543_150', '3006_2113_150', 
             '4217_2113_150', '5429_2113_150',
             '3006_971_175', '4217_971_175', 
             '5429_971_175', '3006_1543_175', 
             '4217_1543_175', '5429_1543_175',
             '3006_2113_175', '4217_2113_175', '5429_2113_175']
             
    exp =['3006_2113_175']
    t0 = time()
    ac ="eliptica"
    # trat ="shot_peening"
    ruta_exp ="datos_exp"
    ruta_curvas = r"curvas_inic\eliptica\MAT_FS.dat"
    # pintar_grafica_a_N()
    for i in exp:
        exp_max = tracc + i
        exp_min = comp + i
        a_inic,v_ai_mm, N_t_min,N_t,N_p, N_i, N_a=principal(par, W,MAT,ac, exp_max, exp_min,ruta_curvas=ruta_curvas)
        # pintar_grafica_a_N(N_a, v_ai_mm)
        # fig =pintar_grafica_iniciacion(a_inic,v_ai_mm, N_t_min,N_t,N_p, N_i,par,trat, i)
    # fig.show()
    tf = time()
    print(f"Tiempo empleado {tf-t0}")

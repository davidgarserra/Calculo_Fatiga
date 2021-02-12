# -*- coding: utf-8 -*-
"""
Created on:

@author:  David García y Alejandro Quirós
"""

import os
import matplotlib.pyplot as plt
from scipy.optimize import fsolve
from propagacion import fase_propagacion,MAT
import numpy as np
import time

def ciclos_totales(param, crit, MAT):
    """Devuelve los ciclos totales en funcion del criterio usado, utilizando 
    un fsolve().
    
    INPUTS: param = Fatemi-Socie o Smith-Watson-Topper en un punto 
            crit  = parametro a utilizar
            MAT   = indice asignado al material
            
    OUTPUT: N_t   = ciclos totales"""
    
    #Constantes del material necesarias 
    sigma_y = MAT["sigma_y"]
    sigma_f = MAT["sigma_f"]
    k       = sigma_y/sigma_f
    E       = MAT["E"]
    nu      = MAT["nu"]
    b       = MAT["b"]

    def fsolve_FS(x):
        """Funcion que utiliza el fsolve para calcular los ciclos de vida
        cuando se utiliza el Fatemi-Socie."""
        expr = param - ((1+nu)*sigma_f/E*(2.0*x)**b + k/2.0*(1.0 
                     + nu)*sigma_f**2.0/(E*sigma_y)*(2.0*x)**(2.0*b))
        
        return expr
        
    def fsolve_SWT(x):
        """Funcion que utiliza el fsolve para calcular los ciclos de vida
        cuando se utiliza el Smith-Watson-Topper."""        
        expr = param - (sigma_f**2.0/E*(2*x)**(2.0*b))
        
        return expr
        
    if crit == 'FS':        
        N_t = fsolve(func=fsolve_FS, x0=10, xtol=1e-10)[0]
    
    elif crit == 'SWT':
        N_t = fsolve(func=fsolve_SWT, x0=100, xtol=1e-10)[0]
    
    return N_t
    
###############################################################################
###############################################################################

def fase_iniciacion(param, sigma, crit, a_i,ac, da, W, MAT):
    """Devuelve los ciclos de la fase de iniciacion de una grieta, conocida
    la tension media desde la superficie hasta la punta de la misma.
    
    INPUTS: param = Fatemi-Socie o Smith-Watson-Topper en un punto 
            sigma = tension x en ese punto
            crit  = parametro a utilizar
            a_i   = (m) tamaño de la grieta de iniciacion
            ac    = plana o eliptica (0 o 0.5)
            da    = paso para realizar los calculos 
            W     = (m) anchura del especimen
            MAT   = indice asignado del material
                  
    OUTPUT: N_i   = ciclos de la fase de iniciacion"""
    
    #Calcula los ciclos totales hasta el fallo
    N_t = ciclos_totales(param, crit, MAT)
    
    #ind_a se utiliza para la propia fase de propagacion por lo 
    #que en la fase de iniciacion no es una variable relevante y puede tomar 
    #cualquier valor
    ind_a = 0
    
    #Calculos los ciclos que necesita la grieta para propagarse
    N_p = fase_propagacion(sigma, ind_a, a_i,ac, da, W, MAT)
    
    #Calculamos los ciclos de iniciacion
    N_i = N_t - N_p
    
    #Si el numero es negativo devuelve 0
    if N_i < 0:
        N_i = 0.0
        
    #Para ciclos muy altos solo se tiene en cuenta la iniciación para evitar 
    #errores que se producen en la integración de la propagación
    if N_t > 1.5e7:
        N_i = N_t
    
    return N_i
    
###############################################################################
############################################################################### 
    
def curvas_iniciacion(par, da,ac, W, MAT):
    """Escribe un archivo de texto con las curvas de
    iniciación para distintas longitudes de grieta para un material.
    
    INPUT:   par   = parametro para el modelo de iniciacion
             ac      =plana o eliptica (0 o 0.5)
             da    = paso para realizar los calculos 
             W     = (m) anchura del especimen
             MAT   = indice asignado al material
        
    OUTPUTS: MATX_par.dat = archivo con las curvas de iniciacion
             figura.png   = imagen con las curvas de iniciacion"""
             
    print(('\nCurvas de iniciacion del material '
           +'utilizando el parametro {}\n').format(par))
    
    #Abrimos el archivo donde se van a escribir los datos,
    #escribimos la cabecera del mismo y creamos los vectores con las tensiones
    #y los tamaños de grieta para crear las curvas de iniciación
    cwd      = os.getcwd()
    ruta     = cwd + '/curvas_inic/{}/'.format(ac)
    ruta_fig = cwd + '/grafs/{}/'.format(ac)
    if(os.path.isdir(ruta_fig)):
        pass
    else:
        os.mkdir(ruta_fig)

    archivo  = open('{}/MAT_{}.dat'.format(ruta, par), 'w')
        
    archivo.write('{:.3e} '.format(0.0000))
    
    v_sigma     = []       #Vector de tensiones
    v_param     = []       #Vector de Fatemi-Socie o Smith-Watson-Topper
    n_sigma     = 45          #Discretizaciones de la curva de iniciacion
    
    sigma_max   = 500.0    #(MPa) tension maxima
    sigma_min   = 50.0     #(MPa) tension minima
        
    delta_sigma = 10.0      #Paso de tensiones

    #Cargamos propiedades del material
    sigma_y = MAT["sigma_y"]
    sigma_f = MAT["sigma_f"]
    k       = sigma_y/sigma_f
    E       = MAT["E"]
    G       = MAT["G"]

    #Generamos el vector de Fatemi-Socie o Smith-Watson-Topper
         
    v_sigma = np.arange(sigma_min,sigma_max,delta_sigma)
    n_sigma = len(v_sigma)
    v_def = v_sigma/E 
    v_gamma = v_sigma/2/G 
    v_param = v_gamma*(1.0+k*v_sigma/2.0/sigma_y) if par =='FS' else v_sigma*v_def
                                    
    n_a   = 100        #Número de curvas de iniciacion por material
    a_min = 5e-5           #Tamaño más pequeño grieta
    ex    = 1.2		   #Variable para controlar como crece la diferencia
    					   #entre longitudes de grieta
       
    v_a = [a_min*(i+1.0)**ex for i in range(n_a)] #Vector de tamaños de grietas
    for a in v_a:
        archivo.write('{:.3e} '.format(a))

    N_i = np.zeros((n_sigma,n_a)) #inicializamos la matriz de ciclos de iniciación

    # proceso = 0.0
    t1 = time.time()
    for i in range(len(v_param)):
        archivo.write('\n{:.3e} '.format(v_param[i]))
        for j,a in enumerate(v_a):
            N_i[i,j]  = fase_iniciacion(v_param[i], v_sigma[i], par, a,ac, da, W, MAT)
            archivo.write('{:.3e} '.format(N_i[i,j]))
        #Pintamos en la consola el porcentaje realizado
        print('\r{:.2%} completado'.format((i+1.0)/len(v_param)), end = '')
        # proceso =(i+1.0)/len(v_param)
        # return proceso
    #Cerramos el archivo
    
    archivo.close()   
    t2= time.time()
    print("\nSe han requerido {:.2f}s".format(t2-t1))  
    
    #Pintamos las curvas de iniciación
    
    plt.figure()
    for i in range(n_a):
        plt.plot(N_i[:,i],v_sigma)
    plt.grid()
    plt.title(f"Curvas de iniciación para el parámetro {par}")
    plt.xscale("log")
    plt.xlabel("Ciclos")
    plt.ylabel("$\sigma (MPa)$")

    # #Guardamos la figura y la cerramos
    plt.savefig(ruta_fig+f'curvas_inic_{par}.png')

    return N_i,n_a,v_sigma

def plot_N_i(par,N_i,v_sigma,n_a):
    plt.figure()
    for i in range(n_a):
        plt.plot(N_i[:,i],v_sigma)
    plt.grid()
    plt.title(f"Curvas de iniciación para el parámetro {par}")
    plt.xscale("log")
    plt.xlabel("Ciclos")
    plt.ylabel("$\sigma (MPa)$")
    plt.show()

   
    
###############################################################################
###############################################################################    

if __name__ == "__main__":
    pars =["SWT","FS"]
    acs =["plana","eliptica"]
    
    for par in pars:
        for ac in acs:
            N_i,n_a,v_sigma =curvas_iniciacion(par = par, da=1e-5,ac=ac, W = 10e-3, MAT=MAT)
    
    
    

   
    
  
    

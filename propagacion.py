# -*- coding: utf-8 -*-
"""
Created on:

@author: David García y Alejandro Quirós
"""


import numpy as np
from scipy.integrate import quad

MAT = {"C"     :8.83e-11,
    "n"        : 3.322,
    "f"        : 2.5,
    "l_0"      : 25e-6,
    "sigma_fl" : 169.0,
    "K_th"     : 2.2,
    "K_IC"     : 29.0,
    "sigma_y"  : 503.0,
    "sigma_f"  : 1610.0,
    "E"        : 71000.0,
    "nu"       : 0.33,
    "b"        : -.1553}
MAT["G"]= MAT["E"]/(2.0*(1.0 + MAT["nu"]))
MAT["a_0"] =1/np.pi*(MAT["K_th"]/(MAT["sigma_fl"]))**2.0
   

###############################################################################
###############################################################################

def K_I(sigma, a, ds, W):
    """Devuelve el factor de instensidad de tensiones para un tamaño de grieta
    determinado utilizando una función de peso propuesta por Bueckner.
    
    INPUTS: sigma = (MPa) tension perpendicular al plano de la grieta
                    (float) --> fase de iniciación
                    (list)  --> fase de propagación
            a     = (m) longitud de la grieta
            ds    = (m) paso de longitudes de grieta
            W     = (m) espesor del especimen
            
    OUTPUT: K_I   = (MPa m^0.5) factor de intensidad de tensiones"""

    #Funciones de peso
    m1 = 0.6147 + 17.1844*(a/W)**2.0 + 8.7822*(a/W)**6.0
    m2 = 0.2502 + 3.2889*(a/W)**2.0 + 70.0444*(a/W)**6.0

    def integr_KI(s, sx):
        """Realiza el cálculo de la integral del FIT"""
        
        res = sx/s**0.5*(1.0 + m1*s/a + m2*(s/a)**2.0)
        
        return res
        
    #Si sigma es de tipo float, el cálculo es para la fase de iniciación
    if type(sigma) is not list:
        
        integral = 0.0
        s        = ds/2.0
        N        = int(round(a/ds, 8))
        
        for i in range(N - 1):
            integral += integr_KI(s, sigma)*ds
            s        += ds       
        
        K_I      = (2.0/np.pi)**0.5*integral

    #Si sigma es de tipo list, el cálculo es para la fase de propagación
    else:
        integral = 0.0
        s        = ds/2.0
        
        for i in sigma[:-1]:
            j = sigma[sigma.index(i)+1]
            integral += integr_KI(s, (i+j)/2.0)*ds
            s        += ds
            
        K_I = (2.0/np.pi)**0.5*integral
    
    return K_I
        
###############################################################################
###############################################################################

def Phi(ac = 0.5):
    """Devuelve el factor Phi calculado por Irwin para el caso de una grieta
    elíptica.
    
    INPUT:  ac  = a/c | relacion entre los semiejes

    OUTPUT: Phi = factor de la grieta eliptica"""
    
    #Calculo del factor para grietas elíptica
    int_phi = lambda phi: np.sqrt(1.0 - (1.0 - (ac)**2.0)*(np.sin(phi))**2.0)
    phi = quad(int_phi,0,np.pi/2)[0]
    return phi       
        
    
    
###############################################################################
###############################################################################

def fase_propagacion(sigma, ind_a, a_i, ac,da, W, MAT):
    """Devuelve los ciclos de propagacion de la grieta.
    
    INPUTS: sigma    = (MPa) tensión maxima perpendicular al plano de la grieta
                       (float) --> fase de iniciación
                       (list)  --> fase de propagación       
            ind_a   = indice asociado a la longitud de grieta
            a_i     = (m) longitud inicial de la grieta
            ac      = plana o eliptica (0 o 0.5)
            da      = (m) paso de longitudes de grietas
            W       = (m) anchura del especimen
            MAT     = indice asignado al material

    OUTPUT: N_p     = ciclos de la fase de propagacion"""
    
    #Obtenemos las constantes del material
    # mat_props = constantes_material(MAT)
    
    C    = MAT["C"]
    n    = MAT["n"]
    f    = MAT["f"]
    l_0  = MAT["l_0"]
    K_th = MAT["K_th"]
    a_0  = MAT["a_0"]
    K_IC = MAT["K_IC"]
    

    def integr_prop(x, s, ac):
        """Realiza el cálculo de la integral de los ciclos de propagación"""
        phi = Phi(ac)
        ki = K_I(s, x, da, W)/phi

        if ki < K_th*(x**f/(x**f + a_0**f - l_0**f))**(0.5*f):
            res = 1e20
        else:
            res = 1.0/(C*(ki**n
                          - (K_th*(x**f/(x**f + a_0**f - l_0**f))**(0.5*f))**n))
        
        return ki, res            
    
    #Si sigma es de tipo float, el cálculo es para la fase de iniciación
    # ac  = 0.5

    if ac == "plana":
        ac = 0.0
    elif ac == "eliptica":
        ac =0.5
    
    N_p = 0.0
    a   = a_i 
    ki  = 0.0
    if type(sigma) is not list:
        while ki < K_IC:
            N_p += integr_prop(a, sigma, ac)[1]*da
            ki   = integr_prop(a, sigma, ac)[0]
            a   += da

    #Si sigma es de tipo list, el cálculo es para la fase de propagación.
    #Se empieza la integral en la longitud de iniciacion requerida y se va 
    #aumentando la longitud, utilizando la variable i, de forma que en cada
    #vuelta del bucle aumenta en 1 el tamaño del vector de tensiones y la
    #longitud de grieta consecuentemente con el paso.    
    else:
        i =0
        while ki < K_IC:
            #Invertimos los vectores de tensiones, ya que para el calculo de 
            #K_IC la integral se inicia al fondo de la grieta acabando en 
            #la superficie. Seleccionamos del vector completo de tensiones, las
            #componentes del mismo que van desde la superficie hasta el tamaño
            #de grieta asociado al indice ind_a            
            sxx_max  = np.flipud(sigma[:ind_a + 1 + i]).tolist()
            N_p     += integr_prop(a, sxx_max, ac)[1]*da
            ki       = integr_prop(a, sxx_max, ac)[0]
            a       += da
            i       += 1
        
    return N_p
    

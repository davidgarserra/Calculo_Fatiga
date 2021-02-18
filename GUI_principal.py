# -*- coding: utf-8 -*-
"""
Created on :

@author: David García Serrano
"""
###Importacion de módulos
import os
import  tkinter as tk
from tkinter import ttk
import numpy as np
from iniciacion import curvas_iniciacion
from propagacion import MAT
from principal import *
from estadistica import*
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,NavigationToolbar2Tk
import pandas as pd
import re

class programa(tk.Tk):
    def __init__(self):
        super().__init__()
        ###Configuración de inicio
        self.title("Cálculo de Fatiga")
        self.state("zoomed")
        self.geometry("800x600+10+10")
        self.iconbitmap("icon.ico")
        self.protocol("WM_DELETE_WINDOW", self.preguntar_salir)

        ### variables 

        self.props = ["C","n","f","l_0","K_th","sigma_fl","a_0","K_IC","sigma_y","sigma_f","E","nu","b","G"]
        self.units = ["","","","m","MPa m^0.5","MPa","m","MPa m^0.5","MPa","MPa","MPa","","","MPa"]
        self.dict_prop = {}#Diccionario con los valores del material
        self.mat_values ={}
        self.material ="" #Material elegido en el combobox de material
        self.dict_units = dict(zip(self.props,self.units))

        self.N_i=[]     #vector con N_i
        self.n_a=1      #número de longitudes de grieta
        self.v_sigma=[] #vector de tensiones
        self.par =""    #parámetro
        self.W =0.0     #anchura
        self.da =0.0    #paso de grieta
        self.ini_file ="" #Ubicación de archivo de iniciación
        self.df =pd.DataFrame() #Dataframe de iniciación
        self.df_materiales =pd.DataFrame() #Dataframe de materiales
        
        self.dir_exp ="" #Directorio de datos de tensiones y deformaciones
        self.files_exp =[]#Lista de datos de tensiones y deformaciones
        self.file_path ="" #ubicación de los datos
      
        self.lista_exp =[]  #Lºista de experimentos sin especificar traccion o compresion
        self.df_datos =pd.DataFrame()

        self.ubi_dat_exp ="" #ubicacion de los datos experimentales para pestaña gráficas
        self.ubi_dat_est ="" #ubicacion de los datos estimados para pestaña gráficas

        self.ruta_principal = os.getcwd() #ruta de ejecución principal

        for prop in self.props:
            self.mat_values[prop] = tk.StringVar()
        
        ### Menu
        self.menu = tk.Menu(self)
        self.file_menu = tk.Menu(self.menu, tearoff=0)
        self.file_menu.add_command(label="Nuevo",command= self.abrir_nuevo)
        self.file_menu.add_command(label="Seleccionar nueva carpeta",command= self.seleccionar__nueva_carpeta)
        self.file_menu.add_command(label="Seleccionar carpeta existente",command= self.seleccionar_carpeta)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Abrir datos experimentales",command=self.carga_datos)
        self.file_menu.add_command(label="Abrir resultados de iniciación",command=self.abrir_resultados_iniciacion)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Salir", command=self.preguntar_salir)
        self.menu.add_cascade(label="Archivo", menu=self.file_menu)
        self.menu.add_command(label="Acerca de",command =self.mostrar_info)
        
        self.config(menu=self.menu)

        #Pestañas 
        self.pestanas = ["Material","Iniciación","Datos","Cálculo","Gráficas"]
        self.tabControl = ttk.Notebook(self)
        self.tabs ={}
        for pestana in self.pestanas:
            self.tabs[pestana] = ttk.Frame(self.tabControl)
        
            self.tabControl.add(self.tabs[pestana], text =pestana)

        self.tabControl.pack(expand=1,fill= "both")

        #Label Frame de propiedades del material
        props_lf = ttk.Labelframe(self.tabs["Material"],text = "Propiedades") 
        props_lf.grid(column = 0,row =0,padx =20,pady=30)

        # props_lf.place(width=180,height=500)
        self.props_entries = {}
        for prop in self.props:
            self.props_entries[prop] = ttk.Entry(props_lf,textvariable = self.mat_values[prop],width = 20,justify = "right",font =("Arial",10)) 
        props_labels = [ttk.Label(props_lf,text = f"{p}({self.dict_units[p]})",font =("Arial",10)) for p in self.props]
        self.props_entries["C"].focus_set()
        self.props_entries["G"].config(state=tk.DISABLED)
        self.props_entries["a_0"].config(state=tk.DISABLED)

        for i,prop in enumerate(self.props):
            self.props_entries[prop].grid(column = 1, row = i, padx = 5,pady = 5,sticky=tk.W)
            props_labels[i].grid(column = 0, row = i, padx = 8,pady = 5,sticky= tk.W)
        
        #Botones de las propiedades
        self.boton_borrar = ttk.Button(props_lf,width = 20,text="Borrar todo",command = self.borrar_campos)
        self.boton_borrar.grid(column = 0,row =len(self.props),padx =5, pady =5,sticky= tk.W)
        self.boton_guardar= ttk.Button(props_lf,text="Confirmar",width=20,command = lambda: self.guardar_campos(None))
        self.boton_guardar.grid(column = 1,row =len(self.props),padx =5, pady =5,sticky= tk.W)
        self.tabs["Material"].bind("<Return>",self.guardar_campos)

        #Guardar y borrar material 
        self.btn_guardar_material = ttk.Button(props_lf,width =20, text = "Guardar Material", command = self.guardar_material)
        self.btn_borrar_material = ttk.Button(props_lf,width =20, text = "Borrar Material",command = self.borrar_material)
        self.btn_guardar_material.grid(column =1, row = len(self.props)+1, padx = 5, pady =5,sticky= tk.W)
        self.btn_borrar_material.grid(column =0, row = len(self.props)+1, padx = 5, pady =5,sticky= tk.W)
       
        #combobox
        self.comb_val = []
        self.cargar_materiales()
        
        self.combo_mat = ttk.Combobox(props_lf,width = 30,value =self.comb_val,font =("Arial",12,"bold"))
        self.combo_mat.bind("<<ComboboxSelected>>",self.combosel) 
        self.combo_mat.grid(column = 0, row = len(self.props)+2,columnspan=2,padx = 5, pady = 8)
        
        ### Label Frame del resumen 
        self.resum_lf =ttk.Labelframe(self.tabs["Material"],text = "Resumen")
        self.resum_lf.grid(column = 1,row =0,padx =20,pady=30,sticky=tk.NW)
        
        self.intro_resumen = ttk.Label(self.resum_lf, text = "Datos que se van a utilizar para la realización de los cálculos:",font = ("Arial",12))
        self.intro_resumen.grid(column = 0, row =0,padx = 20)
        
        self.resum_label ={}

        for i,prop in enumerate(self.props):
            self.resum_label[prop] = ttk.Label(self.resum_lf,text = prop+": ",font =("Arial",12,"bold")) 
            self.resum_label[prop].grid(column = 0,row =i+1, padx = 5,pady = 5,sticky=tk.W)

        ### Pestaña de Iniciación
        self.vars_iniciacion_frame = ttk.Labelframe(self.tabs["Iniciación"],text ="Variables para el cálculo de la iniciación",width=1200,height= 600)
        self.vars_iniciacion_frame.place(relx= 0.01,rely =0.01,relwidth=0.975,relheight=0.25)
        
        self.var_param = tk.StringVar()
        self.var_param.set("SWT")

        self.ac_param = tk.StringVar()
        self.ac_param.set("eliptica")
        
        self.CB_param_SWT =ttk.Radiobutton(self.vars_iniciacion_frame,text ="\tSWT",variable= self.var_param,value="SWT")
        self.CB_param_SWT.grid(column = 0, row= 0 , columnspan= 2,pady = 5, padx = 5,sticky = tk.W)
        self.CB_param_FS =ttk.Radiobutton(self.vars_iniciacion_frame,text ="\tFS",variable = self.var_param,value="FS")
        self.CB_param_FS.grid(column = 0, row= 1 , columnspan= 2,pady = 5, padx = 5,sticky = tk.W)
        
        self.W_entry = ttk.Entry(self.vars_iniciacion_frame,width = 6,justify=tk.RIGHT,font =("Arial",10))
        self.W_entry.grid(column = 2, row =0, sticky= tk.W,padx=20,pady=5)
        self.W_label = ttk.Label(self.vars_iniciacion_frame,text = "W",font =("Arial",10))
        self.W_label.grid(column =3, row = 0, sticky= tk.W)
        self.W_entry.insert(0,"10e-3")
        
        self.da_entry = ttk.Entry(self.vars_iniciacion_frame,width = 6,justify=tk.RIGHT)
        self.da_entry.grid(column = 2, row =1, sticky= tk.W,padx=20,pady=5)
        self.da_label = ttk.Label(self.vars_iniciacion_frame,text = "da")
        self.da_label.grid(column =3, row = 1, sticky= tk.W)
        self.da_entry.insert(0,"1e-5")

        self.rb_plana = ttk.Radiobutton(self.vars_iniciacion_frame,text ="Propagación plana",variable =self.ac_param, value ="plana")
        self.rb_plana.grid(column = 4, row = 0, columnspan =2, padx =20, pady =5,sticky = tk.W)
        self.rb_eliptica = ttk.Radiobutton(self.vars_iniciacion_frame,text ="Propagación eliptica",variable =self.ac_param, value ="eliptica")
        self.rb_eliptica.grid(column = 4, row = 1, columnspan =2, padx =20, pady =5,sticky = tk.W)
        
        #boton de probar
        self.ini_btn = ttk.Button(self.vars_iniciacion_frame,text = "Ejecutar iniciación",command =self.ejecutar_curvas)
        self.ini_btn.grid(column = 0,row=2 ,columnspan=6 ,sticky=tk.W,padx = 5, pady = 5)

        #TreeFrame 
        self.tree_frame = tk.LabelFrame(self.tabs["Iniciación"],text = "Datos de Iniciación")
        self.tree_frame.place(relx =0.51,rely =0.27,relwidth=0.475,relheight=0.7)
        
        self.tree_scrollbarx = ttk.Scrollbar(self.tree_frame,orient =tk.HORIZONTAL)
        self.tree_scrollbary = ttk.Scrollbar(self.tree_frame,orient =tk.VERTICAL)
    
        self.tree_view =ttk.Treeview(self.tree_frame,xscrollcommand = self.tree_scrollbarx.set,yscrollcommand =self.tree_scrollbary.set)
        
        self.tree_scrollbarx.pack(side= tk.BOTTOM,fill =tk.X)
        self.tree_scrollbary.pack(side= tk.RIGHT,fill =tk.Y)
        self.tree_scrollbarx.config(command =self.tree_view.xview)
        self.tree_scrollbary.config(command =self.tree_view.yview)
        
        #chart
        self.canvas_chart = tk.LabelFrame(self.tabs["Iniciación"],text = "gráfica de Iniciación")
        self.canvas_chart.place(relx =0.01,rely =0.27,relwidth=0.475,relheight=0.7)
        
        ### Pestaña Datos 

        #Label frame de datos experimentales
        self.dat_exp_lf = ttk.LabelFrame(self.tabs["Datos"],text = "Datos de tensiones y deformaciones")
        self.dat_exp_lf.place(relx = 0.01,rely = 0.01,relwidth=0.98,relheight=0.2)
        
        #combobox 
        self.combo_exp = ttk.Combobox(self.dat_exp_lf,width =50)
        self.combo_exp.bind("<<ComboboxSelected>>",self.sel_exp) 
        self.combo_exp.grid(column = 0, row =0,padx = 5, pady = 5)
        
        #Boton Cargar datos 
        self.cargar_dat_btn  = ttk.Button(self.dat_exp_lf, text = "Cargar Datos",command= self.carga_datos)
        self.cargar_dat_btn.grid(column = 2, row= 0, padx = 5, pady = 5)

        # Label Frame Gráficas 
        self.graf_lf = ttk.Labelframe(self.tabs["Datos"],text = "Gráficas")
        self.graf_lf.place(relx = 0.01, rely =0.22,relheight=0.75,relwidth= 0.48)

        self.graf_frame =tk.Frame(self.graf_lf)
        self.graf_frame.place(x = 5,rely = 0.16, relheight=0.83,relwidth =0.98)

        self.graf_opt_frame = tk.Frame(self.graf_lf,)
        self.graf_opt_frame.place(x = 5, y = 5, relwidth =0.98,relheight=0.15)

        self.combo_eje_x = ttk.Combobox(self.graf_opt_frame,width =40)
        self.combo_eje_y = ttk.Combobox(self.graf_opt_frame,width =40)
        self.combo_eje_x.grid(column =1, row=0, pady = 5, padx = 5)
        self.combo_eje_y.grid(column =1, row=1, pady = 5, padx = 5)

        self.label_eje_x = ttk.Label(self.graf_opt_frame ,text = "Eje X")
        self.label_eje_y =ttk.Label(self.graf_opt_frame ,text = "Eje Y")
        self.label_eje_x.grid(column =0, row =0, padx = 5)
        self.label_eje_y.grid(column =0, row = 1, padx = 5, pady =5)

        self.btn_graf =ttk. Button(self.graf_opt_frame,text = "Actualizar",command =self.actualizar_grafica)
        self.btn_graf.grid(column = 2, row = 0, rowspan= 2, padx = 5, pady = 5)


        # Label Frame Treeview
        self.dat_tree_lf = ttk.Labelframe(self.tabs["Datos"],text = "Datos")
        self.dat_tree_lf.place(relx = 0.5, rely =0.22,relheight=0.75,relwidth= 0.48)

        self.dat_scrollbarx = ttk.Scrollbar(self.dat_tree_lf,orient=tk.HORIZONTAL)
        self.dat_scrollbary = ttk.Scrollbar(self.dat_tree_lf,orient=tk.VERTICAL)

        self.dat_tv =ttk.Treeview(self.dat_tree_lf,xscrollcommand = self.dat_scrollbarx.set,yscrollcommand =self.dat_scrollbary.set)
        
        self.dat_scrollbarx.config(command =self.dat_tv.xview)
        self.dat_scrollbary.config(command =self.dat_tv.yview)
        self.dat_scrollbarx.pack(side= tk.BOTTOM,fill =tk.X)
        self.dat_scrollbary.pack(side= tk.RIGHT,fill =tk.Y)

        ### Pestaña Cálculo 
        self.ejec_lf = ttk.Frame(self.tabs["Cálculo"],relief = tk.GROOVE)
        self.ejec_lf.place(x = 10, y = 10,relheight = 0.15,relwidth =0.48)

        ## ejecucion 
        self.combo_ejec = ttk.Combobox(self.ejec_lf,width = 50)
        self.combo_ejec.grid(column = 0, row = 0,padx =25,pady =25,sticky=tk.W)

        self.btn_ejec = ttk.Button(self.ejec_lf,text = "Ejecutar",command = self.ejecutar_calculo)
        self.btn_ejec.grid(column = 1, row =0, padx = 5,pady =25,sticky =tk.S)

        self.btn_ejec_todo =ttk.Button(self.ejec_lf,text = "Ejecutar todos",command = self.ejecutar_calculo_todo)
        self.btn_ejec_todo.grid(column = 2, row =0, padx = 5,pady =25,sticky =tk.S)

        ## Resultados
        self.result_ini_lf = tk.LabelFrame(self.tabs["Cálculo"],text = "Resultados")
        self.result_ini_lf.place(relx = 0.5,y =10,relheight = 0.15,relwidth =0.48)

        self.lbl_lon_ini = ttk.Label(self.result_ini_lf, text = "Longitud de iniciación de la grieta: ",justify =tk.LEFT)
        self.lbl_lon_ini.pack(padx = 5, pady =5,anchor = tk.W)

        self.lbl_cicl = ttk.Label(self.result_ini_lf, text = "Número de ciclos hasta el fallo: ",justify =tk.LEFT)
        self.lbl_cicl.pack(padx = 5, pady =5,anchor = tk.W)
        
        self.lbl_ubi = ttk.Label(self.result_ini_lf, text = "Resultados guardados en: ",justify =tk.LEFT)
        self.lbl_ubi.pack(padx = 5, pady =5,anchor = tk.W)

        self.graf_ini_lf = tk.LabelFrame(self.tabs["Cálculo"],text = "Gráfica de iniciación")
        self.graf_ini_lf.place(x =10 ,rely =0.18,relheight = 0.8,relwidth =0.48)

        self.graf_cicl_lf = tk.LabelFrame(self.tabs["Cálculo"],text = "Gráfica de ciclos totales")
        self.graf_cicl_lf.place(relx=0.5 ,rely =0.18,relheight = 0.8,relwidth =0.48)
        
        ### Pestaña Gráficas
        self.carga_graf_lf = ttk.Labelframe(self.tabs["Gráficas"],text = "Carga de datos")
        self.carga_graf_lf.place(x = 10,y =10, relwidth =0.48,relheight=0.2)

        self.reg_graf_lf = ttk.Labelframe(self.tabs["Gráficas"],text = "Gráfica de comparación")
        self.reg_graf_lf.place(x = 10, rely =0.22,relwidth =0.48,relheight=0.76)

        self.lon_vida_graf_lf =ttk.Labelframe(self.tabs["Gráficas"],text = "Vida estimada - Longitud inicial")
        self.lon_vida_graf_lf.place(relx =0.49,y = 10,relwidth =0.48,relheight = 0.48)

        self.per_vida_graf_lf = ttk.Labelframe(self.tabs["Gráficas"],text = "Vida estimada - Porcentaje de vida inicial")
        self.per_vida_graf_lf.place(relx =0.49,rely =0.50,relwidth =0.48,relheight = 0.48)

        ## Carga de datos
        self.lbl_dat_exp = ttk.Label(self.carga_graf_lf,text = "Datos experimentales: ",width =85)
        self.lbl_dat_exp.grid(column =0, row=0, padx =5, pady =2,sticky =tk.W)

        self.lbl_dat_est =ttk.Label(self.carga_graf_lf,text = "Datos estimados: ",width =85)
        self.lbl_dat_est.grid(column =0, row =1,padx =5, pady =2,sticky =tk.W)

        self.btn_carga_exp =ttk.Button(self.carga_graf_lf,text ="Cargar datos experimentales",width =30,command =self.cargar_graf_dat_exp)
        self.btn_carga_exp.grid(column=1,row =0,padx =5, pady =2,sticky =tk.E)

        self.btn_carga_est =ttk.Button(self.carga_graf_lf,text ="Cargar datos estimados",width=30, command = self.cargar_graf_dat_est)
        self.btn_carga_est.grid(column=1,row =1,padx =5, pady =2,sticky =tk.E)

        self.btn_ejecuta_graficas= ttk.Button(self.carga_graf_lf,text ="Ejecutar gráficas",width=60,command = self.ejecutar_graficas)
        self.btn_ejecuta_graficas.grid(column =0, row =2, padx =5,pady =5,columnspan =2,sticky=tk.W)

        self.mostrar_info()
        
        ### Funciones
    def combosel(self,event):
        """Selecciona un valor de la lista y completa los campos con los valores asignados.
        """
        self.material = self.combo_mat.get() 
        cols = self.df_materiales.columns.values.tolist()[1:]

        self.props_entries["a_0"].delete(0,tk.END)
        self.props_entries["G"].delete(0,tk.END)

        self.props_entries["a_0"].config(state=tk.DISABLED)
        self.props_entries["G"].config(state=tk.DISABLED)
        
        for prop in cols:
        #Cambiamos lo que hubiera en las entradas por las propiedas del material 
        #seleccionado
            self.props_entries[prop].delete(0,tk.END)
            self.props_entries[prop].insert(0,self.df_materiales[self.df_materiales["Material"]==self.material][prop].values[0])   
    
    def borrar_campos(self):
        """Elimina los valores de los campos.
        """
        for prop in self.props:
            self.props_entries[prop].delete(0,tk.END)
        
        self.props_entries["G"].config(state=tk.DISABLED)
        self.props_entries["a_0"].config(state=tk.DISABLED)
        self.dict_prop = {}
        for prop in self.props:
            self.resum_label[prop].config(text =prop+": ")
        
    def guardar_campos(self,event):
        """Guarda los valores en un diccionario que posteriormente se utiliza para la realización
        de los cálculos.
        """
        for prop in self.props:
            #Rellenamos el diccionario con los datos de las entradas
            try:
                self.dict_prop[prop] = float(self.mat_values[prop].get())
            except ValueError:
                #sino son validos no los guardamos y los borramos de las entradas
                self.props_entries[prop].delete( 0,tk.END)

        #Cambia la configuración de G y a_0 a normal
        self.props_entries["G"].config(state=tk.NORMAL)
        self.props_entries["a_0"].config(state=tk.NORMAL)

        #Calculamos los valores de G y a_0 y los insertamos en las 
        #entradas correspondientes.
        self.dict_prop["G"]=self.dict_prop["E"]/(2.0*(1.0 + self.dict_prop["nu"]))
        self.mat_values["G"].set(self.dict_prop["G"])
        self.props_entries["G"].insert(0,self.mat_values["G"].get())

        self.dict_prop["a_0"]=1/np.pi*(self.dict_prop["K_th"]/(self.dict_prop["sigma_fl"]))**2.0
        self.mat_values["a_0"].set(self.dict_prop["a_0"])
        self.props_entries["a_0"].insert(0,self.mat_values["a_0"].get())
        
        if len(self.dict_prop)==len(self.props):
            #Cambia las etiquetas del resumen de los datos si 
            # el diccionario está completo
            for prop in self.props:
                self.resum_label[prop].config(text = "{}:\t{:.3e}\t{}".format(prop,self.dict_prop[prop],self.dict_units[prop]))
        
    def cargar_materiales(self):
        """Carga los materiales guardados en el excel materiales 
        al inicio del programa

        """
        #Guardamos los materiales en el dataframe de materiales
        self.df_materiales = pd.read_excel("materiales.xlsx",index_col=0)
        
        #Añadimos a la lista de materiales del combobox
        self.comb_val = list(self.df_materiales["Material"])

    
    def guardar_material(self):
        """Guarda las propiedades de un material y lo agrega 
        al combobox de material

        """
        #Obtenemos el material
        self.material =self.combo_mat.get()

        #Añadimos el material a la lista de materiales
        self.comb_val.append(self.material)
        self.combo_mat.config(values=self.comb_val)

        #Obtenemos las columnas del dataframe de materiales
        self.df_mat_cols = self.df_materiales.columns.values[1:]
        
        #Añadimos un diccionario con los datos del material
        self.datos_materiales ={"Material":self.material}

        try:
            for prop in self.df_mat_cols: 
                self.datos_materiales[prop] = float(self.props_entries[prop].get())

            #Añadimos la fila al dataframe y lo exportamos al archivo excel
            self.df_materiales= self.df_materiales.append(self.datos_materiales,ignore_index =True)
            self.df_materiales.to_excel("materiales.xlsx")

        except ValueError:
            tk.messagebox.showerror("ERROR","Algún valor no es válido")
            self.comb_val.pop()
            self.combo_mat.config(values=self.comb_val)


    def borrar_material(self):
        """Borra un material específico del combobox de materiales

        """
        #Obtiene el nombre del material
        self.material =self.combo_mat.get()

        #Elimina del dataframe de materiales el material especificado
        self.df_materiales = self.df_materiales.drop(self.df_materiales[self.df_materiales["Material"]==self.material].index)
        self.df_materiales.to_excel("materiales.xlsx")

        #Lo eliminamos de la lista de materiales
        self.comb_val.remove(self.material)
        self.combo_mat.config(values=self.comb_val)

        #Borramos todos los campos
        self.borrar_campos()

    def seleccionar__nueva_carpeta(self):
        """Selecciona una carpeta nueva y crea las carpetas necerias 
        para guardar los archivos necesarios.

        """
        #Preguntamos al usuario la carpeta y se cambia a ella
        self.ruta_principal = tk.filedialog.askdirectory(title = "Abrir carpeta")
        os.chdir(self.ruta_principal)

        acs_list = ["eliptica","plana"]
        par_list =["SWT","FS"]
        opt_list = ["datos","grafs"]
        
        ruta_curva_inic = os.path.join(self.ruta_principal,"curvas_inic")
        
        #lista con las rutas de las carpetas
        lista_path =[]
        lista_path.append("resultados_generales")

        for ac in acs_list: 
            lista_path.append("curvas_inic/{}".format(ac))
            lista_path.append("grafs/{}".format(ac))
        
        for opt in opt_list:
            for par in par_list: 
                lista_path.append("resultados/{}/{}".format(opt,par))
                                            
        for path in lista_path: 
            if not os.path.exists(path):
                os.makedirs(path)   

    def seleccionar_carpeta(self):
        """Selecciona la carpeta principal de ejecución del programa
        y se cámbia a ella. Esta carpeta debe contener todas las carpetas 
        necesarias para el cálculo.
        """
        #Preguntamos al usuario la carpeta
        self.ruta_principal = tk.filedialog.askdirectory(title = "Abrir carpeta")
        os.chdir(self.ruta_principal)

    def mostrar_info(self):
        """Muestra la información del programa en una alerta.
        """
        text ="""Este programa ha sido desarrollado por David García Serrano
                para el Trabajo de Fin de Máster en Ingeniería Aeronáutica. Año 2021.
                Para dudas acerca del programa consultar el documento del TFM.
                Se trata de un programa en fase de desarrollo por lo que pueden existir
                errores de implementación."""
        tk.messagebox.showinfo("Información", text)

    def plot_iniciacion(self):
        """Representa las curvas de iniciación. 
        Sólo las pinta en el caso de que el archivo de iniciación no 
        exista con anterioridad.

        """
        #Borramos el contenido que hubiera con anterioridad
        if len(self.canvas_chart.winfo_children())>=1:
            for widget in self.canvas_chart.winfo_children():
                widget.destroy()
        
        #Cargamos una figura
        self.figure = plt.figure(figsize =(6,4),dpi=100)
        self.figure.add_subplot(111)

        #Representamos todas las curvas de iniciación
        for i in range(self.n_a):
            plt.plot(self.N_i[:,i],self.v_sigma)
        
        plt.grid()
        plt.title(f"Curvas de iniciación para el parámetro {self.par}")
        plt.xscale("log")
        plt.xlabel("Ciclos")
        plt.ylabel("$\sigma (MPa)$")
        self.chart = FigureCanvasTkAgg(self.figure,self.canvas_chart)
        self.chart.draw()
        self.toolbar  = NavigationToolbar2Tk(self.chart,self.canvas_chart)
        self.toolbar.update()
        self.chart.get_tk_widget().pack(side = tk.TOP,padx =5,pady =5,fill= tk.BOTH,expand = 1)
        

    def ejecutar_curvas(self):
        """Ejecuta las curvas de iniciación

        """

        #Obtenemos los datos del parámetro, paso de grieta y anchura.
        self.par =self.var_param.get()
        self.da =float(self.da_entry.get())
        self.W= float(self.W_entry.get())
        #Establecemos la ruta donde se encuentra el archivo de iniciación
        self.ini_file =self.ruta_principal+"/curvas_inic/{}/MAT_{}.dat".format(self.ac_param.get(),self.par)
        
        #Comprobamos que no existe
        if not os.path.isfile(self.ini_file):
            
            #Ejecutamos las curvas y las representamos
            self.N_i,self.n_a,self.v_sigma =curvas_iniciacion(par = self.par, da=self.da,ac=self.ac_param.get(), W = self.W, MAT=self.dict_prop,main_path=self.ruta_principal)
            self.plot_iniciacion()

        else:
            #Si existe no realiza el cálculo y carga automáticamente los datos
            #de iniciación
            tk.messagebox.showwarning("Atención","Ya se ha realizado la ejecución de las curvas de iniciación con estos parámetros, No es necesario ejecutar la iniciación")
       
        self.cargar_csv()
      
        
    def cargar_csv(self):
        """Carga los datos de iniciación

        """
        try: 
            self.df  =pd.read_table(self.ini_file,sep="\s+")
        
        except ValueError:
            tk.message.showerror("ERROR","Error al cargar el archivo")
        except FileNotFoundError:
            tk.message.showerror("ERROR","No se encuentra el archivo")

        self.tree_view.delete(*self.tree_view.get_children())

        self.tree_view["column"] = list(self.df.columns.values)
        self.tree_view["show"] = "headings"

        for column in self.tree_view["column"] :
            self.tree_view.heading(str(column), text= str(column))

        df_rows = self.df.to_numpy().tolist()
        
        for row in df_rows:
            self.tree_view.insert("","end",values = tuple(row))
    
        self.tree_view.pack(fill =tk.BOTH, expand=1)

    def carga_datos(self):
        """Carga los datos de tensiones y deformaciones

        """
        #Preguntamos al usuario la ubicación de los datos
        self.dir_exp= tk.filedialog.askdirectory(title= "Abrir carpeta",initialdir="/")
        
        try:
            #Añadimos los datos al combobox
            self.files_exp = os.listdir(path=self.dir_exp)
            self.combo_exp.config(value= self.files_exp)
            self.combo_exp.set(self.files_exp[0])

            
        except FileNotFoundError:
            tk.messagebox.showerror("ERROR","En esta ruta no se encuentran experimentos. Selecciona otra carpeta")
        except IndexError: 
            tk.tk.messagebox.showerror("ERROR","En esta ruta no se encuentran experimentos. Selecciona otra carpeta")
        self.nombre_experimentos()
     
    def sel_exp(self,event):
        """Selecciona los datos de tensiones y deformaciones del combobox
        """
        #Obtenemos la ruta completa de los datos
        self.file_path = os.path.join(self.dir_exp,self.combo_exp.get())
        
        #Cargamos los datos en un data frame y nos deshacemos de la fila %X
        self.df_datos = pd.read_table(self.file_path,sep="\s+")
        self.df_datos.Y = -self.df_datos.Y*1e-3-0.1
        self.df_datos = self.df_datos.drop(r"%X",axis=1)
        
        #Borramos los datos que hubiera anteriormente en el treeview
        self.dat_tv.delete(*self.dat_tv.get_children())

        #Cargamos en los combobox las columnas del dataframe y establecemos 
        #Y e s_xx por defecto
        self.combo_eje_x.config(value=list(self.df_datos.columns.values))
        self.combo_eje_y.config(value=list(self.df_datos.columns.values))
        self.combo_eje_x.set("Y")
        self.combo_eje_y.set("s_xx")

        self.actualizar_grafica()

        #Rellenamos el dataframe con los datos de tensión y deformación
        self.dat_tv["column"] = list(self.df_datos.columns.values)
        self.dat_tv["show"] = "headings"

        for column in self.dat_tv["column"] :
            self.dat_tv.heading(column, text= column)

        df_rows = self.df_datos.to_numpy().tolist()

        for row in df_rows:
            self.dat_tv.insert("","end",values = tuple(row))
    
        
        self.dat_tv.pack(fill =tk.BOTH, expand=1,padx = 5, pady = 5)


    def actualizar_grafica(self):
        """Genera una gráfica con los ejes especificados

        """
        #Borramos el contenido que hubiera anteriormente
        if len(self.graf_lf.winfo_children())>=1:
            for widget in self.graf_frame.winfo_children():
                widget.destroy()

        #creamos la figura
        self.dat_figure = plt.figure(figsize=(6,4),dpi = 100)
        self.dat_figure.add_subplot(111)
        plt.plot(self.df_datos[self.combo_eje_x.get()],self.df_datos[self.combo_eje_y.get()])
        plt.grid()
        plt.title(f"Gráfica de {self.combo_eje_y.get()} con respecto {self.combo_eje_x.get()}")
        plt.xlabel(f"{self.combo_eje_x.get()}")
        plt.ylabel(f"{self.combo_eje_y.get()}")
        self.dat_chart= FigureCanvasTkAgg(self.dat_figure,self.graf_frame)
        self.dat_chart.draw()
        self.toolbar_dat  = NavigationToolbar2Tk(self.dat_chart,self.graf_frame)
        self.toolbar_dat.update()
        self.dat_chart.get_tk_widget().pack(fill = tk.BOTH,expand=1)

    def abrir_resultados_iniciacion(self):
        """Abre directamente un archivo de iniciación ya existente sin
        tener que volver a ejecutar la iniciación

        """

        #Borramos el contenido que hubiera en el Treeview
        self.tree_view.delete(*self.tree_view.get_children())

        try: 
            #Preguntamos al usuario el nombre del archivo y lo almacenamos 
            #en el dataframe
            self.ini_file =tk.filedialog.askopenfilename(initialdir="curvas_inic/",title="Abrir archivo de iniciación",filetypes=(("archivo DAT","*.dat"),("archivo csv","*.csv"),("Todos los archivos","*.*")))
            self.df  =pd.read_table(self.ini_file,sep="\s+")
        
        #Mostramos los posibles errores al cargar
        except ValueError:
            tk.messagebox.showerror("ERROR","El archivo no es valido")
        except FileNotFoundError:
            tk.messagebox.showerror("ERROR","No se encuentra el archivo")

        self.tree_view["column"] = list(self.df.columns.values)
        self.tree_view["show"] = "headings"

        for column in self.tree_view["column"] :
            self.tree_view.heading(str(column), text= str(column))
        df_rows = self.df.to_numpy().tolist()
        
        for row in df_rows:
            self.tree_view.insert("","end",values = tuple(row))
    
        self.tree_view.pack(fill =tk.BOTH, expand=1)

    def nombre_experimentos(self):
        """
        Obtiene los nombres de los experimentos a partir del nombre de los archivos de experimentos 
        y rellena el combobox de cálculo.
        """
        pattern = r"\d+_\d+_\d+"
        self.lista_exp =[]
        for f in self.files_exp: 
            
            self.lista_exp.append(re.search(pattern,f).group())

        self.lista_exp =list(dict.fromkeys(self.lista_exp))
        self.combo_ejec.config(value =self.lista_exp)
        self.combo_ejec.set(self.lista_exp[0])
        

    def ejecutar_calculo(self):
        """Ejecuta el cálculo de los resultados para unos determinados
        datos de tensiones y deformaciones.

        """
        #Borramos el contenido que hubiera con anterioridad
        if len(self.graf_ini_lf.winfo_children())>=1:
            for widget in self.graf_ini_lf.winfo_children():
                widget.destroy()
        if len(self.graf_cicl_lf.winfo_children())>=1:
            for widget in self.graf_cicl_lf.winfo_children():
                widget.destroy()

        #Reiniciamos las etiquetas de la información del resultado
        self.lbl_lon_ini.config(text ="Longitud de iniciación de la grieta: ")
        self.lbl_cicl.config(text ="Número de ciclos hasta el fallo: ")
        self.lbl_ubi.config(text ="Resultados guardados en: ")

        #Obtenemos los datos del parámetro y anchura
        self.par =self.var_param.get()
        self.W = float(self.W_entry.get())

        #Filtramos por los patrones para obtener el archivo correspondiente
        pat_max =r'TENSOR_TRAC\S+_{}'.format(self.combo_ejec.get())
        pat_min  =r'TENSOR_COM\S+_{}'.format(self.combo_ejec.get())

        exp_max=    list(filter(lambda i: re.match(pat_max,i),self.files_exp))[0][:-4]
        exp_min  = list(filter(lambda i: re.match(pat_min,i),self.files_exp))[0][:-4]
        
        try:

            #Ejecutamos la función principal
            a_inic,v_ai_mm, N_t_min,N_t,N_p, N_i, N_a = principal(self.par,self.W,self.dict_prop,self.ac_param.get(),exp_max,exp_min,self.dir_exp,ruta_curvas=self.ini_file,main_path= self.ruta_principal)
            
            #Obtenemos la figuras y la incrustamos en el espacio reservado 
            #para ella.
            self.a_N_fig = pintar_grafica_a_N(N_a,v_ai_mm,self.par,self.combo_ejec.get())
            self.a_N_chart= FigureCanvasTkAgg(self.a_N_fig,self.graf_ini_lf)
            self.a_N_chart.draw()
            self.a_N_TB  = NavigationToolbar2Tk(self.a_N_chart,self.graf_ini_lf)
            self.a_N_TB.update()
            self.a_N_chart.get_tk_widget().pack(fill = tk.BOTH,expand=1,padx =5, pady = 5)

            self.cicl_fig = pintar_grafica_iniciacion(a_inic,v_ai_mm, N_t_min,N_t,N_p, N_i,self.par, self.combo_ejec.get(),main_path=self.ruta_principal)
            self.cicl_chart= FigureCanvasTkAgg(self.cicl_fig,self.graf_cicl_lf)
            self.cicl_chart.draw()
            self.cicl_TB  = NavigationToolbar2Tk(self.cicl_chart,self.graf_cicl_lf)
            self.cicl_TB.update()
            self.cicl_chart.get_tk_widget().pack(fill = tk.BOTH,expand=1,padx =5, pady = 5)

            #actualizamos la información de las etiquetas
            self.lbl_lon_ini.config(text = self.lbl_lon_ini["text"] +"{:.3f} mm".format(a_inic))
            self.lbl_cicl.config(text = self.lbl_cicl["text"]+" {:.0f}".format(N_t_min))
            self.lbl_ubi.config(text = self.lbl_ubi["text"]+"resultados/datos/{}/{}.dat".format(self.par,self.combo_ejec.get()))

            #Mostramos información sobre donde está guardado el resultdo
            tk.messagebox.showinfo("Atención","El resultado del cálculo ha sido añadido al final del archivo /resultados_generales/resultados.dat")
        
        except KeyError:
            #Mostramos error cuando existe un error en la carga
            tk.messagebox.showerror("ERROR","No se ha especificado el material. Por favor introduce las propiedades en la pestaña Material.")
       
        except FileNotFoundError:
            tk.messagebox.showerror("ERROR","No se ha encontrado el experimento. Por favor selecciona un experimento de los que se encuentran en la lista.")
        
    def ejecutar_calculo_todo(self):
        """Ejecuta todos los datos cargados en el combobox de una vez para
        obtener las gráficas y los resultados de la vida a fatiga

        """

        #Borramos el contenido que hubiera anteriormente en los frames
        if len(self.graf_ini_lf.winfo_children())>=1:
            for widget in self.graf_ini_lf.winfo_children():
                widget.destroy()
        #Reiniciamos las etiquetas de las pestañas
        self.lbl_lon_ini.config(text ="Longitud de iniciación de la grieta: ")
        self.lbl_cicl.config(text ="Número de ciclos hasta el fallo: ")
        self.lbl_ubi.config(text ="Resultados guardados en: ")
        #Obtenemos los datos del parámetro y anchura.
        self.par =self.var_param.get()
        self.W = float(self.W_entry.get())

        #Creamos una figura
        self.a_N_fig =plt.figure()

        for exp in self.lista_exp:
            
            #Obtenemos los experimentos que empiecen por estos patronees
            pat_max =r'TENSOR_TRAC\S+_{}'.format(exp)
            pat_min  =r'TENSOR_COM\S+_{}'.format(exp)

            exp_max=    list(filter(lambda i: re.match(pat_max,i),self.files_exp))[0][:-4]
            exp_min  = list(filter(lambda i: re.match(pat_min,i),self.files_exp))[0][:-4]

            #ejecutamos la función principal para obtener los resultados
            a_inic,v_ai_mm, N_t_min,N_t,N_p, N_i, N_a = principal(self.par,self.W,self.dict_prop,self.ac_param.get(),exp_max,exp_min,self.dir_exp,ruta_curvas = self.ini_file,main_path=self.ruta_principal)

            pintar_grafica_a_N_todas(N_a,v_ai_mm)
            
            #Cargamos los datos en un chart y ponemos la barra de navegación
            #para interactuar con la gráfica
            self.a_N_chart= FigureCanvasTkAgg(self.a_N_fig,self.graf_ini_lf)
            self.a_N_chart.draw()
            self.a_N_TB  = NavigationToolbar2Tk(self.a_N_chart,self.graf_ini_lf)
            self.a_N_TB.update()
            self.a_N_chart.get_tk_widget().pack(fill = tk.BOTH,expand=1,padx =5, pady = 5)
            self.graf_ini_lf.update()

            if exp != self.lista_exp[-1]:
                for widget in self.graf_ini_lf.winfo_children():
                    widget.destroy()
            

    
    def cargar_graf_dat_exp(self):
        """Carga los datos de tensiones y deformaciones

        """

        self.lbl_dat_exp.config(text ="Datos experimentales: ")
        self.ubi_dat_exp = tk.filedialog.askopenfilename(title ="Abrir datos experimentales",initialdir="/",filetypes=(("Archivos excel","*.xlsx"),("Todos los archivos","*.*")))
        self.lbl_dat_exp.config(text =self.lbl_dat_exp["text"]+"/..."+self.ubi_dat_exp[-60:])

    def cargar_graf_dat_est(self):
        """Carga los datos estimados
        """
        self.lbl_dat_est.config(text ="Datos estimados: ")

        self.ubi_dat_est = tk.filedialog.askopenfilename(title ="Abrir datos estimados",initialdir="/",filetypes=(("Archivos dat","*.dat"),("Archivos excel","*.xlsx"),("Todos los archivos","*.*")))
        self.lbl_dat_est.config(text =self.lbl_dat_est["text"]+"/..."+self.ubi_dat_est[-60:])

        
    def ejecutar_graficas(self):
        """Imprime los resultados en las graficas en la pestaña Gráfica

        """
        #Borramos lo que haya dentro del widjet para no sobreponer el
        #siguiente cálculo
        if len(self.reg_graf_lf.winfo_children())>=1:
            for widget in self.reg_graf_lf.winfo_children():
                widget.destroy()
        if len(self.lon_vida_graf_lf.winfo_children())>=1:
            for widget in self.lon_vida_graf_lf.winfo_children():
                widget.destroy()
        if len(self.per_vida_graf_lf.winfo_children())>=1:
            for widget in self.per_vida_graf_lf.winfo_children():
                widget.destroy()
        try:
            #Gráfica de regresión
            self.par = self.var_param.get()
            self.fig_reg = plt.figure(figsize =(5,5))
            regresion(self.par,self.ubi_dat_est,self.ubi_dat_exp)
            self.reg_chart= FigureCanvasTkAgg(self.fig_reg,self.reg_graf_lf)
            self.reg_chart.draw()
            self.reg_TB  = NavigationToolbar2Tk(self.reg_chart,self.reg_graf_lf)
            self.reg_TB.update()
            self.reg_chart.get_tk_widget().pack(fill = tk.BOTH,expand=1,padx =5, pady = 5)

            #Gráfica de longitud - número de ciclos
            self.fig_lon_vida = grafica_lon_vida(self.par,self.ubi_dat_est)
            self.lon_vida_chart = FigureCanvasTkAgg(self.fig_lon_vida, self.lon_vida_graf_lf)
            self.lon_vida_chart.draw() 
            self.lon_vida_TB = NavigationToolbar2Tk(self.lon_vida_chart,self.lon_vida_graf_lf)
            self.lon_vida_TB.update() 
            self.lon_vida_chart.get_tk_widget().pack(fill = tk.BOTH,expand=1,padx =5, pady = 5)
            
            #Gráfica de porcentaje de iniciación- número de ciclos
            self.fig_per_vida = grafica_per_vida(self.par,self.ubi_dat_est)
            self.per_vida_chart = FigureCanvasTkAgg(self.fig_per_vida, self.per_vida_graf_lf)
            self.per_vida_chart.draw() 
            self.per_vida_TB = NavigationToolbar2Tk(self.per_vida_chart,self.per_vida_graf_lf)
            self.per_vida_TB.update() 
            self.per_vida_chart.get_tk_widget().pack(fill = tk.BOTH,expand=1,padx =5, pady = 5)
    
        except:
            tk.messagebox.showerror("ERROR","Archivo/s no válidos. Asegurese de que se han cargado correctamente los archivos.")

    def abrir_nuevo(self):
        """Reinicia el programa
        """
        self.destroy()
        self.__init__()
    
    def preguntar_salir(self):
        """Pregunta al usuario si quiere salir del programa.
        """
        resp = tk.messagebox.askokcancel("Atención","¿Estás seguro de querer salir?")
        if resp:
            self.destroy()

if __name__ =="__main__":
    app = programa() 
    app.mainloop()
    






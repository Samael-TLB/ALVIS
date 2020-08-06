import re
import traceback
import json

from kivy.app import App
from kivy.core.window import Window

from kivy.uix.button import Button
from kivy.uix.popup import Popup

from kivy.properties import *
from kivy.uix.settings import *
from kivy.animation import Animation
from kivy.config import Config
from kivy.clock import Clock

from threading import Thread,Event

from alvis_gui import Alvis
from algfilechooser import AlgFileChooser
from algorithm import AlgorithmBase
from graph import Graph
from color_settings import SettingColor


Window.minimum_height=100
Window.minimum_width=100
Window.maximize()

import threading 

class AlvisApp(App):
    use_kivy_settings=True
    
    settings_display_type = OptionProperty('normal', options=['normal', 'popup','fullwindowed'])
    
    settings_popup = ObjectProperty(None, allownone=True)

    re=[]
    alg_file,alg_sourcecode,alg,alg_fn,t_e=StringProperty(),None,None,None,None
    compiled=False
    graph=None
    
    def build(self):
        return Alvis()

    def build_config(self, config):
        self.config = config
        
        self.config.setdefaults('graph',{'category':'Planar','weighted':1})
        
        self.config.setdefaults('Planar',{'g_type':'Triangulation','n':10000,'c_dist':0.15,\
                                          'fn':'laplace','keep_same':0,'sparse':0,\
                                          'degree_max':5,'seed':0})
        
        self.config.setdefaults('Tree',{'g_type':'Random Tree'})

        self.config.setdefaults('Lattice',{'g_type':'Hexagonal Lattice','m':100,'n':100})

        self.config.setdefaults('theme',{'node':'0.2,0.2,0.2,0.8','edge':'0.21,0.2,0.2,0.8',\
                                         'start':'1,0,1,1','goal':'1,0.5,0.5,1',\
                                         'open':'1,0,0,1','closed':'0,1,0,1',\
                                         'relay':'0.5,0.3,0.9,0.8',\
                                         'path':'1,1,1,1','point size':0})
        
    def build_settings(self,settings):
        self.settings=settings
        self.settings.register_type('color', SettingColor)
        
        self.settings.add_json_panel('Graph ', self.config,
                                     filename='assets/settings_json/settings_graph.json')
    
        value=self.config.get('graph','category')
        for panel in list(self.settings.walk()):
                if isinstance(panel,SettingItem):
                    panel.disabled = False if value== panel.section or \
                                     "graph"==panel.section else True
                    
        self.settings.add_json_panel('Theme', self.config,
                                     filename='assets/settings_json/settings_theme.json')

         
    def close_settings(self, *args):
        if self.settings_display_type == 'popup':
            p = self.settings_popup
            if p is not None:
                p.dismiss()
        #elif self.settings_display_type=='normal':
            #pass
        else:
            super(AlvisApp, self).close_settings()
            
    def display_settings(self, settings):
        if self.settings_display_type == 'popup':
            p = self.settings_popup
            if p is None:
                self.settings_popup = p = Popup(content=settings,
                                                title='Settings',
                                                size_hint=(0.8, 0.8))
            if p.content is not settings:
                p.content = settings
            p.open()
        #elif self.settings_display_type=='normal':
            size_hint=0.8,1
        else:
            super(AlvisApp, self).display_settings(settings)

    def load_alg(self):
        f=AlgFileChooser()
        self.alg_file_popup=p=Popup(content=f,
                                title='Algorithm File Loader',
                                size_hint=(0.8, 0.8),size_hint_max=(800,600))
        p.open()


    def on_alg_file(self,obj,value):
        screen=self.root.get_screen('MainScreen')
        if value[-3:]=='.py':
            with open(self.alg_file) as fd:
                try:self.alg_sourcecode=fd.read()
                except:self.alg_sourcecode=''
            screen.ids['code panel'].text=self.alg_sourcecode
            u=screen.ids['menubar']
            u.ids['sn'].disabled=False
            u.ids['gn'].disabled=False
            self.toggle_code_panel('open')
            
    def on_config_change(self, config, section, key, value):
        screen=self.root.get_screen('MainScreen')

        if key=='fullscreen':
            self._app_window.toggle_fullscreen()
            
            
        elif section=='graph':
            if key=='category':
                self.graph.category=value
                
                for panel in list(self.settings.walk()):
                    if isinstance(panel,SettingItem):
                        panel.disabled = False if value== panel.section or "graph"==panel.section else True
                        if not panel.disabled and panel.key=="g_type":
                            self.graph.g_type=panel.value

            elif key=='weighted':self.graph.weighted=int(value)
                
                
        elif key=='g_type':
            self.graph.g_type=value
            
            
        elif section=='Lattice':
            if key=='m':self.graph.lattice_params[0]=int(value)
            elif key=='n':self.graph.lattice_params[1]=int(value)

        elif section=='Planar':
            if key=='n':self.graph.planar_params[0]=int(value)
            elif key=='c_dist':self.graph.planar_params[1]=float(value)
            elif key=='fn':self.graph.planar_params[2]=value
            elif key=='keep_same':self.graph.planar_params[3]=int(value)
            elif key=='sparse':self.graph.planar_params[4]=int(value)
            elif key=='degree_max':self.graph.planar_params[5]=int(value)
            elif key=='seed':self.graph.planar_params[6]=int(value)

        elif section=='theme':
            u=self.graph
            if key=='node':
                u.node_color=list(map(float,value.split(',')))
                if u.drew:
                    screen.ids.viewspace_canvas.canvas.get_group('nodes')[0].rgba=u.node_color

            elif key=='edge':
                u.edge_color=list(map(float,value.split(',')))
                if u.drew:
                    screen.ids.viewspace_canvas.canvas.get_group('edges')[0].rgba=u.edge_color
    
            elif key=='start':
                u.start_node_color=list(map(float,value.split(',')))

            elif key=='goal':
                u.goal_node_color=list(map(float,value.split(',')))

            elif key=='open':
                u.color_dict['open']=list(map(float,value.split(',')))

            elif key=='closed':
                u.color_dict['closed']=list(map(float,value.split(',')))

            elif key=='relay':
                u.color_dict['relay']=list(map(float,value.split(',')))

            elif key=='path':
                u.color_dict['path']=list(map(float,value.split(',')))

            elif key=='point size':
                u.point_size=int(value)
                point_size=u.point_size*(0.00008 if self.graph.category=='Planar' else 0.01)
                if u.drew:
                    l=screen.ids.viewspace_canvas.canvas.get_group('nodes')
                    for i in range(2,len(l),2):
                        l[i].pointsize=point_size

                    l=screen.ids.viewspace_canvas.canvas.get_group('algorithm_runtime_activity')[0]
                    if l:
                        for i in l.children:
                            print( type(i))
                    
            else:
                u.color_dict[key]=list(map(float,value.split(',')))
            
##            for panel in list(self.settings.walk()):
##                if isinstance(panel,SettingItem) and panel.section!='graph' and (panel.section not in (value.lower()) or value in panel.title):
##                    parent=panel.parent
##                    index=parent.children.index(panel)
##                    self.re.append((panel,parent))
##                    parent.remove_widget(panel)
##                    
##
##            for ex_panel in self.re:
##                if value.lower() in ex_panel[0].section or value in panel.title:
##                    ex_panel[0].disabled=False
##                    ex_panel[-1].add_widget(ex_panel[0])
##                    self.re.pop(self.re.index(ex_panel))
                    
            
            
    def on_settings_cls(self, *args):
        self.destroy_settings()
        self.create_settings()

    def on_start(self):
##        Clock.schedule_interval(lambda x: print(threading.active_count()),0)
        self.graph=Graph(self,self.root.get_screen('MainScreen'))
        
    def set_settings_cls(self, panel_type):
        self.settings_cls = panel_type

    def set_settings_display_type(self, settings_display_type):
        self.destroy_settings()
        self.settings_display_type = settings_display_type
        self.create_settings()
        
    def start_alg(self):
        
        def f(node_type):
                    self.graph.show_info("No {} node selected".format(node_type))
                    self.graph.remove_info()

        screen=self.root.get_screen('MainScreen')
        try:
            if not self.compiled:
                x=re.search('class \w*[(]AlgorithmBase[)]:',screen.ids['code panel'].text)
                if x:
                    exec(screen.ids['code panel'].text,globals())
                    self.alg_fn=eval(x.group()[6:-16])
                    self.compiled=True
                else:
                    screen.ids['error msg'].text="No class defined using AlgorithmBase Class"
                    self.toggle_error_msg_panel('open')
                    self.toggle_code_panel('open')
                    
            if self.alg_fn and self.graph.graph \
            and self.graph.start_nodes and self.graph.goal_nodes:
                self.t_e=Event()
                self.alg=alg=self.alg_fn(self.graph,\
                           self.graph.start_nodes,\
                           self.graph.goal_nodes,\
                           self.t_e)

                
                screen.ids['menubar'].ids['del'].disabled=True
                screen.ids['controlpanel'].ids['start'].disabled=True
                p=screen.ids['controlpanel'].ids['pause']
                p.text='Pause'
                p.state='normal'
                u=screen.ids['menubar']
                u.ids['sn'].disabled=True
                u.ids['gn'].disabled=True
                u.ids['del'].disabled=True
                u.ids['gen_graph'].disabled=True

                Thread(target=alg.execute,daemon=True).start()
                
            elif not self.graph.start_nodes and self.graph.goal_nodes:
                Thread(target=f,args=('start',)).start()
            elif self.graph.start_nodes and not self.graph.goal_nodes:
                Thread(target=f,args=('goal',)).start()
            else:             
                Thread(target=f,args=('start and goal',)).start()
                
                
        except:
            txt=traceback.format_exc()
            s,e=txt.index('File'),txt.rindex("File")
            screen.ids['error msg'].text=txt[:s]+txt[e:]
            self.toggle_error_msg_panel('open')
            self.toggle_code_panel('open')
            screen.ids['controlpanel'].ids['start'].disabled=True
            
                
    def restart_alg(self):
        screen=self.root.get_screen('MainScreen')
        if not screen.ids['menubar'].ids['del'].disabled:
            screen.ids['controlpanel'].ids['start'].disabled=False
            u=screen.ids['menubar']
            u.ids['sn'].disabled=False
            u.ids['gn'].disabled=False
            u.ids['gen_graph'].disabled=False
            screen.ids['viewspace_canvas'].canvas.get_group(
                'algorithm_runtime_activity')[0].clear()
            
        screen.ids['error msg'].text=''
        self.toggle_error_msg_panel('close')
        
    def toggle_code_panel(self,order=''):
        screen=self.root.get_screen('MainScreen')
        if screen.ids.menubar.ids['cp'].state=='down' or order=='open':
            width = self.root.width * .35
            if order=='open':screen.ids.menubar.ids['cp'].state='down'
            
        else:
            width = 0
        Animation(width=width, d=.3, t='out_quart').start(screen.ids.codespace)

    def toggle_error_msg_panel(self,order='close'):
        screen=self.root.get_screen('MainScreen')
        if order=='open':
            height = screen.ids.codespace.height * .3
        elif order=='close':
            height = 0
        Animation(height=height, d=.3, t='out_quart').start(screen.ids['error msg'])
       
        
AlvisApp().run()


import re
import traceback

from kivy.app import App
from kivy.core.window import Window

from alvis_gui import Alvis
from algfilechooser import AlgFileChooser
from algorithm import AlgorithmBase

from kivy.uix.button import Button
from kivy.uix.popup import Popup

from kivy.properties import *


from kivy.uix.settings import *

from kivy.animation import Animation
from kivy.config import Config
from kivy.clock import Clock

from color_settings import SettingColor

from threading import Thread,Event
import json


Window.minimum_height=100
Window.minimum_width=100
Window.maximize()



class AlvisApp(App):
    use_kivy_settings=True

    settings_display_type = OptionProperty('normal', options=['normal', 'popup','fullwindowed'])
    
    settings_popup = ObjectProperty(None, allownone=True)

    re=[]
    alg_file,alg_sourcecode,alg,alg_fn,t_e=StringProperty(),None,None,None,None
    compiled=False
    
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
                                         'relay':'0.5,0.3,0.9,0.8','path':'1,1,1,1','point size':0})
        
    def build_settings(self,settings):
        self.settings=settings
        self.settings.register_type('color', SettingColor)
        
        self.settings.add_json_panel('Graph ', self.config, filename='Data\\settings_graph.json')
    
        value=self.config.get('graph','category')
        for panel in list(self.settings.walk()):
                if isinstance(panel,SettingItem):
                    panel.disabled = False if value== panel.section or \
                                     "graph"==panel.section else True
                    
        self.settings.add_json_panel('Theme', self.config, filename='Data\\settings_theme.json')

         
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
        if value[-3:]=='.py':
            with open(self.alg_file) as fd:
                try:self.alg_sourcecode=fd.read()
                except:self.alg_sourcecode=''
            self.root.ids['code panel'].text=self.alg_sourcecode
            self.toggle_code_panel('open')
            
    def on_config_change(self, config, section, key, value):
       
        if key=='fullscreen':
            self._app_window.toggle_fullscreen()
            
            
        elif section=='graph':
            if key=='category':
                self.root.ids['graph'].category=value
                
                
                for panel in list(self.settings.walk()):
                    if isinstance(panel,SettingItem):
                        panel.disabled = False if value== panel.section or "graph"==panel.section else True
                        if not panel.disabled and panel.key=="g_type":self.root.ids['graph'].g_type=panel.value

            elif key=='weighted':self.root.ids['graph'].weighted=int(value)
                
                
        elif key=='g_type':
            self.root.ids['graph'].g_type=value
            
            
        elif section=='Lattice':
            if key=='m':self.root.ids['graph'].lattice_params[0]=int(value)
            elif key=='n':self.root.ids['graph'].lattice_params[1]=int(value)

        elif section=='Planar':
            if key=='n':self.root.ids['graph'].planar_params[0]=int(value)
            elif key=='c_dist':self.root.ids['graph'].planar_params[1]=float(value)
            elif key=='fn':self.root.ids['graph'].planar_params[2]=value
            elif key=='keep_same':self.root.ids['graph'].planar_params[3]=int(value)
            elif key=='sparse':self.root.ids['graph'].planar_params[4]=int(value)
            elif key=='degree_max':self.root.ids['graph'].planar_params[5]=int(value)
            elif key=='seed':self.root.ids['graph'].planar_params[6]=int(value)

        elif section=='theme':
            u=self.root.ids['graph']
            if key=='node':u.node_color=list(map(float,value.split(',')))
            elif key=='edge':u.edge_color=list(map(float,value.split(',')))
            elif key=='start':u.start_node_color=list(map(float,value.split(',')))
            elif key=='goal':u.goal_node_color=list(map(float,value.split(',')))
            elif key=='open':u.color_dict['open']=list(map(float,value.split(',')))
            elif key=='closed':u.color_dict['closed']=list(map(float,value.split(',')))
            elif key=='relay':u.color_dict['relay']=list(map(float,value.split(',')))
            elif key=='path':u.color_dict['path']=list(map(float,value.split(',')))
            elif key=='point size':u.point_size=int(value)
            else:u.color_dict[key]=list(map(float,value.split(',')))
            print(u.start_node_color)
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
        
    def set_settings_cls(self, panel_type):
        self.settings_cls = panel_type

    def set_settings_display_type(self, settings_display_type):
        self.destroy_settings()
        self.settings_display_type = settings_display_type
        self.create_settings()
        
    def start_alg(self):
                
        try:
            if not self.compiled:
                x=re.search('class \w*[(]AlgorithmBase[)]:',self.root.ids['code panel'].text)
                if x:
                    exec(self.root.ids['code panel'].text,globals())
                    self.alg_fn=eval(x.group()[6:-16])
                    self.compiled=True
                else:
                    self.root.ids['error msg'].text="No class defined using AlgorithmBase Class"
                    self.toggle_error_msg_panel('open')
                    self.toggle_code_panel('open')
                    
        except:
            txt=traceback.format_exc()
            s,e=txt.index('File'),txt.rindex("File")
            self.root.ids['error msg'].text=txt[:s]+txt[e:]
            self.toggle_error_msg_panel('open')
            self.toggle_code_panel('open')
            self.root.ids['control'].ids['start'].disabled=True            
        else:
            if self.alg_fn and self.root.ids['graph'].graph\
               and self.root.ids['graph'].start_node in self.root.ids['graph'].graph.nodes\
               and self.root.ids['graph'].goal_node in self.root.ids['graph'].graph.nodes:
                self.t_e=Event()
                self.alg=b=self.alg_fn(self.root.ids['graph'].graph,\
                           self.root.ids['graph'].start_node,\
                           self.root.ids['graph'].goal_node,\
                           self.root.ids['graph'],self.t_e)

                
                self.root.ids['menu'].ids['del'].disabled=True
                self.root.ids['control'].ids['start'].disabled=True
                p=self.root.ids['control'].ids['pause']
                p.text='Pause'
                p.state='normal'
                u=self.root.ids['menu']
                u.ids['sn'].disabled=True
                u.ids['gn'].disabled=True
                u.ids['gen_graph'].disabled=True
                
                Thread(target=b.execute,daemon=True).start()
            if self.root.ids['graph'].start_node not in self.root.ids['graph'].graph.nodes or \
               self.root.ids['graph'].goal_node not in self.root.ids['graph'].graph.nodes:
                
                def f():
                    self.root.ids['graph'].show_info("No start and/or goal node selected")
                    self.root.ids['graph'].remove_info()
                Thread(target=f).start()
                
    def restart_alg(self):
        if not self.root.ids['menu'].ids['del'].disabled:
            self.root.ids['control'].ids['start'].disabled=False
            u=self.root.ids['menu']
            u.ids['sn'].disabled=False
            u.ids['gn'].disabled=False
            u.ids['gen_graph'].disabled=False
            t=Thread(target=self.root.ids['graph'].draw)
            t.start()
            t.join()
        self.root.ids['error msg'].text=''
        self.toggle_error_msg_panel('close')
        
    def toggle_code_panel(self,order=''):
        if self.root.ids['menu'].ids['cp'].state=='down' or order=='open':
            width = self.root.width * .35
            if order=='open':self.root.ids['menu'].ids['cp'].state='down'
            
        else:
            width = 0
        Animation(width=width, d=.3, t='out_quart').start(self.root.ids['sv'])

    def toggle_error_msg_panel(self,order='close'):
        if order=='open':
            height = self.root.ids['sv'].height * .3
        elif order=='close':
            height = 0
        Animation(height=height, d=.3, t='out_quart').start(self.root.ids['error msg'])
       
        
AlvisApp().run()

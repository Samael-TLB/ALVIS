import networkx as nx

from kivy.properties import *
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from time import sleep,time


class AlgorithmBase(Widget):
    
    def __init__(self,graph,start,goal,wid,t_e,**kwargs):
        super().__init__(**kwargs)
        self.graph=graph
        self.dct={'open':[],'closed':[],'path':[],'relay':[]}
        self.start=start
        self.goal=goal
        self.state=None
        self.scale=wid.draw_scale
        self.wid=wid
        self.ev=Clock.create_trigger(lambda x:wid.update(self.dct),0)
        app=App.get_running_app()
        self.val=app.root.ids['control'].ids['slider'].value
        self.found_goal=False
        self.t_e=t_e
        
    def alg_iteration_start(self):
        if self.state=='pause':
            self.t_e.wait()
            self.t_e.clear()

    def alg_iteration_end(self):
        if self.state!='pause':self.ev()
        sleep(1/self.val)

    def execute(self):
        pass

    def execute_end(self):
        self.wid.parent.parent.ids['menu'].ids['del'].disabled=False
        self.wid.parent.parent.ids['menu'].ids['gen_graph'].disabled=False
    def genpath(self):
        path=[]
        i=self.goal
        while i!=self.start:
            path.append(i)
            i=self.get_parent(i)
            
        path.append(self.start)
        self.dct['path']=path
        self.ev()
        
    def get_edge_weight(self,u,v):
        return self.graph[u][v].get('weight',0)

    def get_list(self,name):
        return self.dct.setdefault(name,[])

    def get_nodes(self):
        return self.graph.nodes
    
    def get_parent(self,node):
        return self.graph.nodes[node]['parent']

    def heuristic(self,u,v,fn=None,f_name='euclidean'):
        u,v=self.graph.nodes[u]['pos'],self.graph.nodes[v]['pos']
        if fn:return fn(u,v)
        
        elif f_name:
            if f_name not in('euclidean','manhattan'):f_name='euclidean'
            
            if f_name=='euclidean':
                return ((u[0]-v[0])**2+(u[1]-v[1])**2)**0.5
            elif f_name=='manhattan':
                return abs(u[0]-v[0])+abs(u[1]-v[1])
            
        
    
    def neighbors(self,node):
        return list(self.graph[node])
        
    def set_parent(self,node,parent):
        self.graph.nodes[node]['parent']=parent

    def show_info(self,info):
        self.wid.show_info(info)
        self.wid.remove_info()
        


        

        


        

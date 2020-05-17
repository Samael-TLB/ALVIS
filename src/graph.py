import threading
import networkx as nx
from time import sleep
import numpy as np
from scipy.spatial import Delaunay

from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import *
from kivy.graphics import *
from kivy.graphics.transformation import Matrix
from kivy.core.window import Window

from kivy.factory import Factory
from kivy.animation import Animation
from kivy.config import ConfigParser
from kivy.uix.label import Label

from networkx import (grid_2d_graph,hexagonal_lattice_graph,triangular_lattice_graph,
                    random_tree,balanced_tree,binomial_tree,full_rary_tree,barabasi_albert_graph,\
                    complete_graph,circulant_graph)



###circular,spectral,spring,kamada_kawai,fruchterman_reingold_layout
##[nx.grid_2d_graph(m,n),nx.hexagonal_lattice_graph(m,n),nx.triangular_lattice_graph(m,n)\
## nx.barabasi_albert_graph(n,1),nx.random_tree(n,seed),nx.balanced_tree(r,h)\
## nx.full_rary_tree(r,n),nx.binomial_tree(n),nx.complete_graph(n)/circulant_graph(n)


class Graph(AnchorLayout):
    
    l_size=ListProperty([100,100])
    drew=BooleanProperty(False)
    config=ConfigParser('alvis')
    config.read('alvis.ini')

    def __init__(self,**kwargs):
        super().__init__(**kwargs)

        self.graph,self.n_pos=None,None
        config=self.config
        self.edge_color,self.node_color=list(map(float,config.getdefault('theme','edge','0.2,0.2,0.2,0.8').split(','))),list(map(float,config.getdefault('theme','node','0.21,0.2,0.2,0.8').split(',')))
        self.start_node_color,self.goal_node_color=list(map(float,config.getdefault('theme','start','1,0,1,1').split(','))),list(map(float,config.getdefault('theme','goal','1,0.5,0.5,1').split(',')))
        self.color_dict={'open':list(map(float,config.getdefault('theme','open','1,0,0,1').split(','))),'closed':list(map(float,config.getdefault('theme','closed','0,1,0,1').split(','))),'relay':list(map(float,config.getdefault('theme','relay','0.5,0.3,0.9,0.8').split(','))),'path':list(map(float,config.getdefault('theme','path','1,1,1,1').split(',')))}
        self.graph_build_fn_dict={'Planar':{'Triangulation':self.planar_triangulation,'Quadrangulation':self.planar_quadrangulation},\
                             'Tree':{'Random Tree':random_tree,'Balanced Tree':balanced_tree,'Binomial Tree':binomial_tree,'Full Rary Tree':full_rary_tree,'Barabasi Albert':barabasi_albert_graph},\
                             'Lattice':{'2d Grid/Lattice':grid_2d_graph,'Hexagonal Lattice':hexagonal_lattice_graph,'Triangular Lattice':triangular_lattice_graph}}
        
        self.category=self.config.getdefault('graph','category','Planar')
        self.g_type=self.config.getdefault(self.category,'g_type','Delaunay')
        self.weighted=self.config.getdefaultint('graph','weighted',0)
        
        self.lattice_params=[self.config.getdefaultint('Lattice','m',0),self.config.getdefaultint('Lattice','n',0)]
        self.tree_params=None,None
        self.planar_params=[self.config.getdefaultint('Planar','n',0),float(self.config.getdefault('Planar','c_dist',0.15)),\
                            self.config.getdefault('Planar','fn','random'),self.config.getdefaultint('Planar','keep_same',0),\
                            self.config.getdefaultint('Planar','sparse',0),self.config.getdefaultint('Planar','degree_max',5),self.config.getdefaultint('Planar','seed',0)]
        self.old_params=[*self.planar_params] if self.category=='Planar'  else [*self.tree_params] if self.category=='Tree'  else [*self.lattice_params] 
        self.old_params+=[self.category,self.g_type]

        self.draw_scale=None
        self.point_size=config.getdefaultint('theme','point size',0)
        self.d=None
        self.graph_edit_mode=None
        self.start_node,self.goal_node=None,None
        self.tree_layout=self.config.getdefault('Tree','layout','Hierarchical')

        self.info=None
        
    def clear_screen(self):
        if self.drew:
            self.start_activity(self.parent.parent.ids['sl'].canvas.clear())
            self.drew=False

    def del_node(self,nodes):
        self.graph.remove_nodes_from(nodes)
        self.graph_edit_mode=None
        
        u=self.parent.parent.ids['menu']
        if self.start_node in nodes:
            self.start_node=None
            u.ids['sn'].disabled=False
        if self.goal_node in nodes:
            self.goal_node=None
            u.ids['gn'].disabled=False
        self.start_activity(self.draw)
        
    def draw(self):
        
        if not self.drew:self.drew=True

        scale=self.draw_scale
        
        pos=np.array([(*self.n_pos[i],0,0) for i in sorted(self.n_pos.keys())],dtype='float32')
        edges=self.get_modified_edges()
        
        self.parent.parent.ids['sl'].canvas.clear()
        
        with self.parent.parent.ids['sl'].canvas:     
            PushMatrix()
            Translate(1,1,0)
            Scale(self.size[1]/scale,self.size[1]/scale,1)

            Color(*self.edge_color)
            for i in range(0,len(pos),65536):
                Mesh(vertices=pos[i:i+65536].reshape(-1), indices=edges, mode="lines")

            pos=np.array([self.n_pos[i] for i in self.graph.nodes])
            Color(*self.node_color)
            for i in range(0,len(pos),2**13):
                Point(points=list(pos[i:i+2**13].reshape(-1)),pointsize=self.point_size/self.size[1]*scale)

            if self.start_node:
                Color(*self.start_node_color)
                Point(points=self.n_pos[self.start_node],pointsize=2*self.point_size/self.size[1]*scale)

            if self.goal_node:
                Color(*self.goal_node_color)
                Point(points=self.n_pos[self.goal_node],pointsize=2*self.point_size/self.size[1]*scale)
            print(self.edge_color,self.node_color,self.start_node_color,self.goal_node_color)
            PopMatrix()
            
    def draw_labels(self):
        pass
    
    def planar_quadrangulation(self):
        pass
    
    def graph_params_changed(self):
        category=self.category
        if category=='Tree':
            new_params=self.tree_params
        else:
            new_params=self.lattice_params
        new_params=[*new_params,self.category,self.g_type]
        if self.old_params!=new_params:
            self.old_params=[*new_params]
            return True
        else:
            return False
        
    def gen_graph(self):
        
        self.show_info('Generating Graph')
        
        if not self.drew or self.category=='Planar' or self.graph_params_changed():
            self.draw_scale=20 if self.category=='Lattice' else 0.5
            self.start_node,self.goal_node=None,None

            u=self.parent.parent.ids['menu']
            u.ids['load'].disabled=True
            u.ids['sn'].disabled=True
            u.ids['gn'].disabled=True
            u.ids['del'].disabled=True
            u.ids['clear'].disabled=True
            u.ids['cp'].disabled=True
            
            category=self.category
            
            if category=='Planar':
                if not self.point_size:self.point_size=6
                self.draw_scale=0.5      
            else:
                if not self.point_size:self.point_size=6
                self.draw_scale=20

                
            if category=='Planar':self.gen_planar_graph()
            
            elif category=='Tree':self.gen_tree_graph()

            else:self.gen_lattice_graph()
            
            
            self.draw()
            fn=lambda x,y:(((x[0]-y[0])**2+(x[1]-y[1])**2)**0.5)*(1+min(0.5,np.random.random()))
            if self.weighted:nx.set_edge_attributes(self.graph,{i:fn(self.n_pos[i[0]],self.n_pos[i[1]]) for i in self.graph.edges},'weight')
            self.graph_params_changed()

            
            u.ids['load'].disabled=False
            u.ids['sn'].disabled=False
            u.ids['gn'].disabled=False
            u.ids['del'].disabled=False
            u.ids['clear'].disabled=False
            u.ids['cp'].disabled=False
        
        self.remove_info()
        self.parent.parent.ids['menu'].ids['gen_graph'].disabled=False
        
        
    def gen_lattice_graph(self):
        self.graph=self.graph_build_fn_dict[self.category][self.g_type](*self.lattice_params)
        if self.g_type=='2d Grid/Lattice':nx.set_node_attributes(self.graph,{i:i for i in self.graph.nodes()},'pos')
        self.n_pos=nx.get_node_attributes(self.graph,'pos')
        
    def gen_planar_graph(self):
        self.graph=self.graph_build_fn_dict[self.category][self.g_type](*self.planar_params)
        self.n_pos = nx.get_node_attributes(self.graph,'pos')
        
    def gen_tree_graph(self):
        self.graph=self.graph_build_fn_dict[self.category][self.g_type](*self.tree_params)
        self.n_pos=self.get_tree_pos()

    def get_modified_edges(self):
        if self.category=='Lattice':
            m,n=self.lattice_params
            q=len(self.graph.nodes)
            #print(q)
            if self.g_type=='2d Grid/Lattice':
                a= np.array([[i[0][0]*n+i[0][1],i[1][0]*n+i[1][1]] for i in self.graph.edges]).reshape(-1)
                #else:a=np.array([[i[0][0]*256+i[0][1],i[1][0]*256+i[1][1]] for i in sorted(self.graph.edges)[:256]]).reshape(-1)

            elif self.g_type=='Triangular Lattice':
                n=(n+1)//2 if n%2 else n
                a=np.array([[i[0][0]*(m+1)+i[0][1] if i[0][0]!=n else i[0][0]*(m+1)+i[0][1]//2 ,i[1][0]*(m+1)+i[1][1] if i[1][0]!=n else i[1][0]*(m+1)+i[1][1]//2] for i in self.graph.edges]).reshape(-1)
                
                
            else:
                m=2*m+1
                n=n+1 if n%2 else n
                p={i:i[0]*m+i[1] if i[0]==0 else i[0]*m+i[1]+i[0]-1 if i[0]!=n else i[0]*m+i[1]+i[0]-2 for i in sorted(self.graph.nodes)}
                a=np.array([[p[i[0]],p[i[1]]] for i in self.graph.edges]).reshape(-1)
                del p

        else:
            a=np.array([i for i in self.graph.edges]).reshape(-1)
        return a
        
    def get_tree_pos(self):
        pass
    
    def tree(self):
        pass
        
        
    
    def on_size(self,*args):
        scale=self.size[1]/self.l_size[1]
        self.l_size=self.size
        
        if self.drew:
            new_scale = scale * self.parent.parent.ids['sl'].scale
            if new_scale < self.parent.parent.ids['sl'].scale_min:
                scale = self.parent.parent.ids['sl'].scale_min / self.parent.parent.ids['sl'].scale
            elif new_scale > self.parent.parent.ids['sl'].scale_max:
                scale = self.parent.parent.ids['sl'].scale_max / self.parent.parent.ids['sl'].scale
            
            #self.parent.parent.ids['sl'].apply_transform(Matrix().scale(scale,scale,scale))
            
            
    def on_touch_down(self,touch):
        self.parent.parent.ids['sl'].on_touch_down(touch)

        def get_selected_node(touch):
            x,y=self.parent.parent.ids['sl'].to_local(touch.x,touch.y)
            scale=self.draw_scale    
            x=x/self.size[1]*scale
            y=y/self.size[1]*scale
            v=0.002 if self.category=='Planar' else 0.1
            l=list(filter(lambda i:round(x-v,3)<=self.n_pos[i][0]<=round(x+v,3) and round(y-v,3)<=self.n_pos[i][1]<=round(y+v,3),self.graph.nodes)) 
            if len(l)!=0:
                if self.graph_edit_mode=='select_start':
                    self.select_start_node(l[0])
                elif self.graph_edit_mode=='select_goal':
                    self.select_goal_node(l[0])
                elif self.graph_edit_mode=='del_node':
                    self.del_node([l[0]])
                   
            else:
                sleep(0.2)
                self.show_info('Retry')
                self.remove_info()
            
        if not self.parent.parent.ids['menu'].ids['gen_graph'].disabled and self.graph_edit_mode and self.graph:self.start_activity(get_selected_node,touch)

    def planar_quadrangulation(self,n,c_dist,fn,keep_same,sparse,degree_max,seed=None):
        if seed:
            np.random.seed(seed)
            
        G=nx.grid_2d_graph(int(n**0.5),int(n**0.5))

        fn=eval('np.random.'+fn)
        if not keep_same or self.d is None or len(self.graph.nodes)!=n:
            pos=fn(size=(n,2)).astype('f')
        
        nx.set_node_attributes(G,{j:(pos[i,0],pos[i,1]) for i,j in zip(range(n),G.nodes) },'pos')
    
        cdst=(c_dist)**2
        #G.add_edges_from(((i[j],i[j+1]) for j in [0,1,-1] for i in self.d.simplices if (pos[i[j]][0]-pos[i[j+1]][0])**2+(pos[i[j]][1]-pos[i[j+1]][1])**2<=cdst))
        
        return G
    
    def planar_triangulation(self,n,c_dist,fn,keep_same,sparse,degree_max,seed=0):
        if seed:
            np.random.seed(seed)
            
        degree_max=max(2,degree_max)

        rng=range(n)
        G = nx.Graph()
        G.add_nodes_from(rng)

        fn=eval('np.random.'+fn)
        if not keep_same or self.d is None or len(self.graph.nodes)!=n:self.d=Delaunay(fn(size=(n,2)))

        pos=self.d.points.astype('f')
        nx.set_node_attributes(G,{i:(pos[i][0],pos[i][1]) for i in G.nodes},'pos')

        f=lambda x,y: G.degree(x)<=np.random.randint(1,degree_max) and G.degree(y)<=np.random.randint(1,degree_max) if sparse else lambda x,y:True
        
        cdst=(c_dist)**2
        G.add_edges_from(((i[j],i[j+1]) for j in [0,1,-1] for i in self.d.simplices \
                          if (pos[i[j]][0]-pos[i[j+1]][0])**2+(pos[i[j]][1]-pos[i[j+1]][1])**2<=cdst and f(i[j],i[j+1])))
        
        return G             

    def remove_info(self):
        sleep(1)
        if self.info:
            self.parent.parent.ids['control'].remove_widget(self.info)
            self.info=None
            
    def start_activity(self,fn,*args):
        threading.Thread(target=fn,args=args,daemon=True).start()

    def select_start_node(self,node):
        if self.start_node!=node:
            scale=self.draw_scale
            with self.parent.parent.ids['sl'].canvas:
                PushMatrix()
                Translate(1,1,0)
                Scale(self.size[1]/scale,self.size[1]/scale,1)
                Color(*self.start_node_color)
                Point(points=self.n_pos[node],pointsize=2*self.point_size/self.size[1]*scale)            
                if self.start_node:
                    Color(0,0,0,0.8)
                    Point(points=self.n_pos[self.start_node],pointsize=2*self.point_size/self.size[1]*scale)            
                
                    Color(*self.node_color)
                    Point(points=self.n_pos[self.start_node],pointsize=self.point_size/self.size[1]*scale)            
                PopMatrix()
                
            self.start_node=node
        self.graph_edit_mode=None
        
    def select_goal_node(self,node):
        if self.goal_node!=node:
            scale=self.draw_scale
            with self.parent.parent.ids['sl'].canvas:
                PushMatrix()
                Translate(1,1,0)
                Scale(self.size[1]/scale,self.size[1]/scale,1)
                Color(*self.goal_node_color)      
                Point(points=self.n_pos[node],pointsize=2*self.point_size/self.size[1]*scale)            
                if self.goal_node:
                    Color(0,0,0,0.8)      
                    Point(points=self.n_pos[self.goal_node],pointsize=2*self.point_size/self.size[1]*scale)            
                
                    Color(*self.node_color)      
                    Point(points=self.n_pos[self.goal_node],pointsize=self.point_size/self.size[1]*scale)            
                PopMatrix()
                
            self.goal_node=node
        self.graph_edit_mode=None
        
    def set_edit_mode(self,mode):
        self.graph_edit_mode=mode if self.graph_edit_mode!=mode else None
        
    def show_info(self,info):
        if not self.info:
            anim_bar = Label(text=info,center=self.center,size_hint=(None,None))
            anim_bar.size=anim_bar.texture_size

            anim = Animation(opacity=0.3, duration=0.6)
            anim += Animation(opacity=1, duration=0.8)
            anim.repeat = True
            self.parent.parent.ids['control'].add_widget(anim_bar,-1)
            anim.start(anim_bar)
            self.info=anim_bar
            
    def update(self,dct):
        pos=np.array([self.n_pos[i] for i in self.graph.nodes]).astype('f').reshape(-1)

        scale=self.draw_scale
        
        with self.parent.parent.ids['sl'].canvas:     
            PushMatrix()
            Translate(1,1,0)
            Scale(self.size[1]/scale,self.size[1]/scale,1)

            Color(*self.node_color)
            for i in range(0,len(pos),2**13):
                Point(points=list(pos[i:i+2**13].reshape(-1)),pointsize=self.point_size/self.size[1]*scale)
            Color(*self.goal_node_color)
            Point(points=self.n_pos[self.goal_node],pointsize=2*self.point_size/self.size[1]*scale)

            for key in dct:
                if key!='path' and len(dct[key])!=0:
                    pos=np.array([self.n_pos[i] for i in dct[key]]).astype('f').reshape(-1)
                    Color(*self.color_dict.setdefault(key,[0.1,0.5,0.2,0]))
                    for i in range(0,len(pos),2**13):
                        Point(points=list(pos[i:i+2**13]),pointsize=self.point_size/self.size[1]*scale)
                
            path=dct.get('path',[])
            if path:
                p_pos=np.array([(*self.n_pos[i],0,0) for i in path]).astype('f')
                edges=np.array([(i,i+1) for i in range(len(path)-1)]).reshape(-1)
                
                Color(*self.color_dict['path'])
                for i in range(0,len(p_pos),2**13):
                    Point(points=list(p_pos[i:i+2**13,:2].reshape(-1)),pointsize=self.point_size/self.size[1]*scale)
                Point(points=[*self.n_pos[self.goal_node],*self.n_pos[self.start_node]],pointsize=self.point_size/self.size[1]*scale)

                for i in range(0,len(p_pos),65536):
                    Mesh(vertices=p_pos[i:i+65536].reshape(-1), indices=edges, mode="lines")
            PopMatrix()
                
            
        

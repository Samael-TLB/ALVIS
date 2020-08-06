import threading
import networkx as nx
from time import sleep
import numpy as np
from triangle import delaunay,voronoi

from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import *
from kivy.graphics import *
from kivy.graphics.transformation import Matrix
from kivy.core.window import Window

from kivy.factory import Factory
from kivy.animation import Animation
from kivy.config import ConfigParser
from kivy.uix.label import Label
from kivy.clock import Clock, mainthread

from networkx import (grid_2d_graph,hexagonal_lattice_graph,triangular_lattice_graph,
                    random_tree,balanced_tree,binomial_tree,full_rary_tree,barabasi_albert_graph,\
                    complete_graph,circulant_graph)




###circular,spectral,spring,kamada_kawai,fruchterman_reingold_layout
##[nx.grid_2d_graph(m,n),nx.hexagonal_lattice_graph(m,n),nx.triangular_lattice_graph(m,n)\
## nx.barabasi_albert_graph(n,1),nx.random_tree(n,seed),nx.balanced_tree(r,h)\
## nx.full_rary_tree(r,n),nx.binomial_tree(n),nx.complete_graph(n)/circulant_graph(n)


class Graph:
    
    l_size=ListProperty([100,100])
    drew=False
    config=ConfigParser('alvis')
    config.read('alvis.ini')
    
    def __init__(self,app,root,**kwargs):
        self.app=app
        self.root=root
        self.canvas=root.ids.viewspace_canvas.canvas
        
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
                            self.config.getdefaultint('Planar','sparse',0),self.config.getdefaultint('Planar','degree_max',5),self.config.getdefaultint('Planar','seed',0),True]

        self.old_params=[*self.planar_params] if self.category=='Planar'  else [*self.tree_params] if self.category=='Tree'  else [*self.lattice_params] 
        self.old_params+=[self.category,self.g_type]

        self.draw_scale=None
        self.point_size=config.getdefaultint('theme','point size',6)
        
        self.graph_n_gulation=None
        self.graph_edit_mode=None
        self.start_nodes,self.goal_nodes=[],[]
        self.tree_layout=self.config.getdefault('Tree','layout','Hierarchical')

        self.info=None
        
            
    def clear_screen(self):
        if self.drew:
            self.start_activity(self.canvas.clear())
            self.drew=False
    
    def del_node(self,nodes):
        node_pos=nx.get_node_attributes(self.graph,'pos')        
        node_arrays=self.canvas.get_group('nodes')
        edge_inst=[i for i in self.canvas.get_group('edges') if type(i)==Mesh][0]
       
        edges_to_remove=[]
        indices=edge_inst.indices
        for node in nodes:
            point=node_pos[node]
            if self.category=='Planar':
                   edges=[(node,i) for i in self.graph[node]]
            elif self.category=='Lattice':
                m,n=self.lattice_params
                if self.g_type=='2d Grid/Lattice':
                    edges=[(node[0]*n+node[1],i[0]*n+i[1]) for i in self.graph[node]]
                elif self.g_type=='Triangular Lattice':
                    n=(n+1)//2 if n%2 else n
                    edges=[(node[0]*(m+1)+node[1] if node[0]!=n else node[0]*(m+1)+node[1]//2 ,i[0]*(m+1)+i[1] if i[0]!=n
                            else i[0]*(m+1)+i[1]//2) for i in self.graph[node]]
                else:
                    m=2*m+1
                    n=n+1 if n%2 else n
                    ps=node[0]*m+node[1] if node[0]==0 else node[0]*m+node[1]+node[0]-1 if node[0]!=n else node[0]*m+node[1]+node[0]-2
                    edges=[((ps,i[0]*m+i[1]) if i[0]==0 else (ps,i[0]*m+i[1]+i[0]-1) if i[0]!=n else (ps,i[0]*m+i[1]+i[0]-2))
                           for i in self.graph[node]]
                    
                        
            for i in range(0,len(indices),2):
                edge=indices[i],indices[i+1]
                for j in edges:
                    if j[0] in edge and j[1] in edge:
                        edges.remove(j)
                        edges_to_remove.append(i)
                        break
            
                    
            for i in edges_to_remove[::-1]:
                edge_inst.indices.pop(i)
                edge_inst.indices.pop(i)
            
            brk=0
            for i in range(2,len(node_arrays),2):
                arr=node_arrays[i]
                for j in range(0,len(arr.points),2):
                    node_point=arr.points[j],arr.points[j+1]
                    if np.allclose(point,node_point):
                        arr.points.pop(j)
                        arr.points.pop(j)
                        brk=1
                        break
                if brk:break         

            if node in self.start_nodes:
                strt_nodes=self.canvas.get_group('start_nodes')[-1]
                for i in range(0, len(strt_nodes.points),2):
                    strt_pos=strt_nodes.points[i],strt_nodes.points[i+1]
                    if np.allclose(point,strt_pos):
                        strt_nodes.points.pop(i)
                        strt_nodes.points.pop(i)
                        self.start_nodes.remove(node)
                        strt_nodes.flag_update()
                        break
                    
            elif node in self.goal_nodes:
                goal_nodes=self.canvas.get_group('goal_nodes')[-1]
                for i in range(0, len(goal_nodes.points),2):
                    goal_pos=goal_nodes.points[i],goal_nodes.points[i+1]
                    if np.allclose(point,goal_pos):
                        goal_nodes.points.pop(i)
                        goal_nodes.points.pop(i)
                        self.goal_nodes.remove(node)
                        goal_nodes.flag_update()
                        break
                    
            
            self.canvas.insert(self.canvas.indexof(edge_inst),
                               Mesh(vertices=edge_inst.vertices,
                                    indices=edge_inst.indices, mode="lines",group='edges'))
                               
            self.canvas.remove(edge_inst)
            arr.flag_update()   
               
        self.graph.remove_nodes_from(nodes)        
        self.graph_edit_mode=None
        
        
#to optimize
    @mainthread
    def draw(self):
        
        point_size=self.point_size*(0.00008 if self.category=='Planar' else 0.01)
        scale=self.draw_scale
        invariate_scale=self.root.ids.viewspace_canvas.scale
#to optimize       
        pos=np.array([(*self.n_pos[i],0,0) for i in sorted(self.graph.nodes)],dtype='float32')
        
        edges=self.get_modified_edges()
        
        self.canvas.clear()
        
        with self.canvas:     
            PushMatrix()
            Translate(1,1,0)
            Scale(scale,scale,1)
            
            Color(*self.edge_color,group='edges')
            for i in range(0,len(pos),65536):
                Mesh(vertices=pos[i:i+65536].reshape(-1),
                     indices=edges, mode="lines",group='edges')
            
            #to optimize
            pos=pos[:,:2]

            Color(*self.node_color,group='nodes')
            for i in range(0,len(pos),16383):#16383):
                Point(points=list(pos[i:i+16383].reshape(-1)),
                      source='assets/images/textures/circle.png',
                      pointsize=point_size,group='nodes')
            
            Color(*self.start_node_color,group='start_nodes')
            Point(points=[],source='assets/images/textures/circle.png',
                  pointsize=point_size/min(1,invariate_scale),group='start_nodes')

            
            Color(*self.goal_node_color,group='goal_nodes')
            Point(points=[],source='assets/images/textures/circle.png',
                  pointsize=point_size/min(1,invariate_scale),group='goal_nodes')

            InstructionGroup(group='algorithm_runtime_activity')
            InstructionGroup(group='overlay_algorithm')

            PopMatrix()

        if not self.drew:self.drew=True
        
    def draw_labels(self):
        pass
        
    def gen_graph(self):
        
        self.show_info('Generating Graph')
        
        if not self.drew or self.category=='Planar' or self.graph_params_changed():
            
            self.start_nodes,self.goal_nodes=[],[]

            u=self.root.ids['menubar']
            u.ids['load'].disabled=True
            u.ids['sn'].disabled=True
            u.ids['gn'].disabled=True
            u.ids['del'].disabled=True
            u.ids['clear'].disabled=True
            u.ids['cp'].disabled=True
            
            category=self.category
            self.draw_scale=10000  if category=='Planar' else 200
            
            if category=='Planar':self.gen_planar_graph()
            
            elif category=='Tree':self.gen_tree_graph()

            else:self.gen_lattice_graph()
            
            self.draw()
            #Clock.schedule_once(lambda *x:self.draw(),1)
            fn=lambda x,y:(((x[0]-y[0])**2+(x[1]-y[1])**2)**0.5)*(1+0.2)#min(0.5,np.random.random()))
            if self.weighted:nx.set_edge_attributes(self.graph,
                                                    {i:fn(self.n_pos[i[0]],self.n_pos[i[1]])
                                                     for i in self.graph.edges},'weight')
            
            self.graph_params_changed()

            
            u.ids['load'].disabled=False
            u.ids['sn'].disabled=False
            u.ids['gn'].disabled=False
            u.ids['del'].disabled=False
            u.ids['clear'].disabled=False
            u.ids['cp'].disabled=False
        
        self.remove_info()
        self.root.ids['menubar'].ids['gen_graph'].disabled=False
        print(self.root.ids.viewspace_canvas.bbox,'lop')        
        
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

#to optimize
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
#to optimize
        else:
            a=np.array([i for i in self.graph.edges]).reshape(-1)
        return a
        

    def get_selected_nodes(self,x,y):
        
        if not self.root.ids['menubar'].ids['gen_graph'].disabled \
           and self.graph_edit_mode \
           and self.graph and (self.info==None or self.info.text!='Retry'):
            x,y=self.root.ids.viewspace_canvas.to_local(x,y)
            scale=self.draw_scale
            
            
            x/=scale
            y/=scale
            
            v=self.point_size*(0.00008 if self.category=='Planar' else 0.01)
        
            pos=nx.get_node_attributes(self.graph,'pos')
            
            l=list(filter(lambda i:round(x-v,3)<=pos[i][0]<=round(x+v,3) and round(y-v,3)<=pos[i][1]<=round(y+v,3),self.graph.nodes)) 

            if len(l)!=0:
                
                if self.graph_edit_mode.startswith('select_start_node'):
                    self.select_start_node(l[0])
                elif self.graph_edit_mode.startswith('select_goal_node'):
                    self.select_goal_node(l[0])
                elif self.graph_edit_mode.startswith('del_nodes'):
                    self.del_node([l[0]])
                   
            else:
                self.show_info('Retry')
                self.remove_info()

        
    def get_tree_pos(self):
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

    
    def planar_quadrangulation(self,n,c_dist,fn,keep_same,sparse,degree_max,seed=None):
        if seed:
            np.random.seed(seed)
            
        G=nx.grid_2d_graph(int(n**0.5),int(n**0.5))

        fn=eval('np.random.'+fn)
        if not keep_same or self.graph_n_gulation is None or len(self.graph.nodes)!=n:
            pos=fn(size=(n,2)).astype('f')
        
        nx.set_node_attributes(G,{j:(pos[i,0],pos[i,1]) for i,j in zip(range(n),G.nodes) },'pos')
    
        cdst=(c_dist)**2
        #G.add_edges_from(((i[j],i[j+1]) for j in [0,1,-1] for i in self.graph_n_gulation.simplices if (pos[i[j]][0]-pos[i[j+1]][0])**2+(pos[i[j]][1]-pos[i[j+1]][1])**2<=cdst))
        
        return G
    
    def planar_triangulation(self,n,c_dist,fn,keep_same,sparse,degree_max,seed=0,update=True):
        if seed:
            np.random.seed(seed)
            
        if not keep_same or self.graph_n_gulation is None or len(self.graph.nodes)!=n or self.old_params:
            
            fn=eval('np.random.'+fn)
            pos=fn(size=(n,2)).astype('float32')
            self.graph_n_gulation=delaunay(pos)

            G = nx.Graph()
            G.add_nodes_from(range(n))

            nx.set_node_attributes(G,{i:(pos[i][0],pos[i][1]) for i in G.nodes},'pos')

            update=True
            
        else:
            G=self.graph
            pos=self.n_pos
        
        if update:
            degree_max=max(2,degree_max)
            f=lambda x,y: G.degree(x)<=np.random.randint(1,degree_max) and G.degree(y)<=np.random.randint(1,degree_max) if sparse else lambda x,y:True
        
            cdst=(c_dist)**2
            G.add_edges_from(((i[j],i[j+1]) for j in [0,1,-1] for i in self.graph_n_gulation \
                          if (pos[i[j]][0]-pos[i[j+1]][0])**2+(pos[i[j]][1]-pos[i[j+1]][1])**2<=cdst and f(i[j],i[j+1])))

            update=False
        
        return G             

    def remove_info(self):
        sleep(1)
        if self.info:
            self.root.ids.viewspace.remove_widget(self.info)
            self.info=None

    def reposition_info(self):
        if self.info:
            center=self.root.ids.viewspace.center
            self.info.center=center[0],center[1]

    def rescale_special_nodes(self,scale):
        self.canvas.get_group('start_nodes')[2].pointsize=self.point_size\
                                                          *(0.00008 if self.category=='Planar' else 0.01)\
                                                          /min(1,scale)
        
        self.canvas.get_group('goal_nodes')[2].pointsize=self.point_size\
                                                          *(0.00008 if self.category=='Planar' else 0.01)\
                                                          /min(1,scale)
        print(self.root.ids.viewspace_canvas.bbox)

                
    def start_activity(self,fn,*args):
        threading.Thread(target=fn,args=args,daemon=True).start()

    def select_start_node(self,node):
        if self.start_nodes!=node:
            self.canvas.get_group('start_nodes')[2].add_point(*self.n_pos[node])
            
            self.start_nodes.append(node)
        self.graph_edit_mode=None
        
    def select_goal_node(self,node):
        if self.goal_nodes!=node:
            self.canvas.get_group('goal_nodes')[2].add_point(*self.n_pos[node])
                
            self.goal_nodes.append(node)
        self.graph_edit_mode=None

        
    def set_edit_mode(self,mode):
        self.graph_edit_mode=mode if self.graph_edit_mode!=mode else None

        
    def show_info(self,info):
        if not self.info:
            center=self.root.ids.viewspace.center
            anim_bar = Label(text=info,center=(center[0]+25,center[1]+25),size_hint=(None,None))
            anim_bar.size=anim_bar.texture_size

            anim = Animation(opacity=0.3, duration=0.6)
            anim += Animation(opacity=1, duration=0.8)
            anim.repeat = True
            self.root.ids.viewspace.add_widget(anim_bar)
            anim.start(anim_bar)
            self.info=anim_bar
            
    def update(self,dct):
        inst_group=self.canvas.get_group('algorithm_runtime_activity')[0]
        
        point_size=self.point_size*(0.00008 if self.category=='Planar' else 0.01)
        
        for key in dct:
            nodes=dct[key] if key!='closed' else dct[key][1:]
            #print(dct[key],nodes)
            if nodes and key!='path':
                pos=[j for i in nodes for j in self.n_pos[i]]
                for s in ('_edges','_nodes'):
                    insts=inst_group.get_group(key+s)
                    if insts:
                        inst=insts[-1]
                        if s=='_edges':
                            if len(inst.vertices)//4<65535:pass

                            else:pass
                                ##                for i in range(0,len(epos),65536):
        ##                    inst_group.add(Mesh(vertices=epos[4*i:4*(i+65536)],
        ##                         indices=range(len(epos)), mode="lines",group=key+'_edges'))
        ##                print(inst_group.get_group(key)[-1],key)#.vertices,inst_group.children[-1].indices)
        ## 
                        
                        else:
                            ind=32766-len(inst.points)
                            inst.points+=pos[:ind]
                            inst.flag_update()
                            for i in range(ind,len(pos[ind:]),32766):
                                inst_group.add(Point(points=pos[i:i+32766],
                                                    source='assets/images/textures/circle.png',
                                                    pointsize=point_size,
                                                    group=key+'_nodes'))
                    else:
                                      
                        inst_group.add(Color(
                            *self.color_dict.setdefault(key,[0.1,0.5,0.2,0]),
                            group=key))
                        
##                        if key=='closed':
##                            epos=[j for i in nodes for j in (*self.n_pos[i],0,0,*self.n_pos[self.graph.nodes[i]['parent']],0,0)]
##                        else:
##                            epos=[j for i in nodes for j in (*self.n_pos[i],0,0,*self.n_pos[self.graph.nodes[i]['parent']],0,0)]
##                        #print(epos,'l')
        ##                for i in range(0,len(epos),65536):
        ##                    inst_group.add(Mesh(vertices=epos[4*i:4*(i+65536)],
        ##                         indices=range(len(epos)), mode="lines",group=key+'_edges'))
        ##                print(inst_group.get_group(key)[-1],key)#.vertices,inst_group.children[-1].indices)
        ##            
                    
                    for i in range(0,len(pos),32766):
                        inst_group.add(Point(points=pos[i:i+32766],
                              source='assets/images/textures/circle.png',
                              pointsize=point_size,
                              group=key+'_nodes'))

            nodes=dct['path']
            if nodes:
                pos=[j for i in nodes for j in self.n_pos[i]]
                inst_group.add(Color(
                    *self.color_dict.setdefault('path',[0.1,0.5,0.2,0]),
                    group='path'))
                inst_group.add(Line(points=pos,group='path'))  
                        
                for i in range(0,len(pos),32766):
                        inst_group.add(Point(points=pos[i:i+32766],
                              source='assets/images/textures/circle.png',
                              pointsize=point_size,
                              group='path')) 
                    
            
        

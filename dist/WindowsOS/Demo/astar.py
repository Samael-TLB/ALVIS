import numpy as np

class astar(AlgorithmBase):
 
    def execute(self):
        start=self.start_nodes[0]
        goal=self.goal_nodes[0]
        queue,visited=self.get_list('open'),self.get_list('closed')
        queue.append(start)
        g={i:np.inf  for i in self.get_nodes()}
        g[start]=0
        f={start:self.heuristic(start,goal)}
        
        while queue:
            self.alg_iteration_start()
            node=min(filter(lambda x: x in queue,f),key=lambda x:f[x])
            queue.remove(node)
            visited.append(node)
            if node==goal:
                visited.append(node)
                self.found_goal=True
                break
            for neighbor in self.neighbors(node):
                t_g=g[node]+self.get_edge_weight(node,neighbor)
                if t_g<g[neighbor]:
                    self.set_parent(neighbor,node)
                    g[neighbor]=t_g
                    f[neighbor]=g[neighbor]+self.heuristic(neighbor,goal,)*2
                    if neighbor not in queue:
                        queue.append(neighbor)
                        
            self.alg_iteration_end()
    
        if self.found_goal:self.genpath()
        else: self.show_info('No path available')
        self.execute_end()

class dfs(AlgorithmBase):
    
    def execute(self):
        start=self.start
        goal=self.goal
        queue,visited=self.get_list('open'),self.get_list('closed')
        queue.append(start)

        while queue:
            self.alg_iteration_start()
            node=queue.pop(0)
            visited.append(node)
            if node==goal:
                visited.append(node)
                self.found_goal=True
                break
            for neighbor in self.neighbors(node):
                if neighbor not in visited and neighbor not in queue:
                    self.set_parent(neighbor,node)
                    queue.insert(0,neighbor)
            self.alg_iteration_end()
        
        if self.found_goal:self.genpath()
        else: self.show_info('No path available')
        self.execute_end()

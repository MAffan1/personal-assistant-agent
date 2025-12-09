"""
Graph-based Memory System for Personal Assistant
Uses NetworkX to build a knowledge graph of user information
"""

import networkx as nx
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
import json

logger = logging.getLogger(__name__)


class GraphMemory:
    """
    Knowledge graph for storing and retrieving user memories and relationships
    """
    
    def __init__(self):
        """Initialize an empty directed graph for memory storage"""
        self.graph = nx.DiGraph()
        logger.info("GraphMemory initialized with empty knowledge graph")
        
        # Track the user node (central node)
        self.user_node = "USER"
        self.graph.add_node(
            self.user_node,
            type="user",
            created_at=datetime.now().isoformat()
        )
        logger.info("User node created in graph")
    
    def add_entity(self, entity_name: str, entity_type: str, attributes: Optional[Dict] = None) -> None:
        """
        Add an entity (person, place, event, etc.) to the graph
        
        Args:
            entity_name: Name/identifier of the entity
            entity_type: Type (person, event, emotion, topic, etc.)
            attributes: Additional attributes for the entity
        """
        if attributes is None:
            attributes = {}
        
        # Add timestamp if not present
        if 'created_at' not in attributes:
            attributes['created_at'] = datetime.now().isoformat()
        
        # Store entity type
        attributes['type'] = entity_type
        
        # Add or update node
        if self.graph.has_node(entity_name):
            # Update existing node
            self.graph.nodes[entity_name].update(attributes)
            logger.debug(f"Updated entity: {entity_name} ({entity_type})")
        else:
            # Add new node
            self.graph.add_node(entity_name, **attributes)
            logger.info(f"Added new entity: {entity_name} ({entity_type})")
    
    def add_relationship(
        self, 
        from_entity: str, 
        to_entity: str, 
        relation_type: str,
        attributes: Optional[Dict] = None
    ) -> None:
        """
        Add a relationship between two entities
        
        Args:
            from_entity: Source entity
            to_entity: Target entity
            relation_type: Type of relationship (knows, attended, feels, etc.)
            attributes: Additional edge attributes
        """
        if attributes is None:
            attributes = {}
        
        # Add timestamp
        attributes['created_at'] = datetime.now().isoformat()
        attributes['relation_type'] = relation_type
        
        # Ensure both entities exist
        if not self.graph.has_node(from_entity):
            self.add_entity(from_entity, "unknown")
        if not self.graph.has_node(to_entity):
            self.add_entity(to_entity, "unknown")
        
        # Add edge
        self.graph.add_edge(from_entity, to_entity, **attributes)
        logger.info(f"Added relationship: {from_entity} --[{relation_type}]--> {to_entity}")
    
    def add_memory_from_message(
        self, 
        user_message: str, 
        extracted_info: Dict
    ) -> None:
        """
        Add memory to graph based on extracted information from user message
        
        Args:
            user_message: The original user message
            extracted_info: Dictionary with extracted entities and relationships
                Expected format: {
                    'keyword': str,
                    'entities': List[Dict],  # [{'name': str, 'type': str, 'attributes': Dict}]
                    'relations': List[Dict]  # [{'from': str, 'to': str, 'type': str}]
                }
        """
        keyword = extracted_info.get('keyword', 'general')
        
        # Add the message itself as a memory node
        message_id = f"memory_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.add_entity(
            message_id,
            "memory",
            {
                'content': user_message,
                'keyword': keyword,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Connect memory to user
        self.add_relationship(self.user_node, message_id, "has_memory")
        
        # Add extracted entities
        for entity in extracted_info.get('entities', []):
            entity_name = entity.get('name')
            entity_type = entity.get('type', 'unknown')
            attributes = entity.get('attributes', {})
            
            self.add_entity(entity_name, entity_type, attributes)
            
            # Connect entity to memory
            self.add_relationship(message_id, entity_name, "mentions")
            
            # Connect entity to user if it's a person or important entity
            if entity_type in ['person', 'family', 'friend']:
                self.add_relationship(self.user_node, entity_name, "knows")
        
        # Add relationships between entities
        for relation in extracted_info.get('relations', []):
            self.add_relationship(
                relation['from'],
                relation['to'],
                relation['type'],
                relation.get('attributes', {})
            )
        
        logger.info(f"Added memory graph for keyword '{keyword}' with {len(extracted_info.get('entities', []))} entities")
    
    def get_related_memories(self, entity: str, max_depth: int = 2) -> List[Dict]:
        """
        Get all memories related to an entity within max_depth hops
        
        Args:
            entity: Entity to search for
            max_depth: Maximum graph distance to search
            
        Returns:
            List of memory dictionaries
        """
        if not self.graph.has_node(entity):
            logger.debug(f"Entity '{entity}' not found in graph")
            return []
        
        memories = []
        
        # Find all memory nodes within max_depth
        try:
            # Get all nodes within max_depth hops
            nearby_nodes = nx.single_source_shortest_path_length(
                self.graph, entity, cutoff=max_depth
            )
            
            # Filter for memory nodes
            for node, distance in nearby_nodes.items():
                node_data = self.graph.nodes[node]
                if node_data.get('type') == 'memory':
                    memories.append({
                        'id': node,
                        'content': node_data.get('content', ''),
                        'keyword': node_data.get('keyword', ''),
                        'timestamp': node_data.get('timestamp', ''),
                        'distance': distance
                    })
            
            # Sort by distance and timestamp
            memories.sort(key=lambda x: (x['distance'], x['timestamp']), reverse=True)
            
            logger.debug(f"Found {len(memories)} memories related to '{entity}'")
            
        except nx.NodeNotFound:
            logger.warning(f"Node '{entity}' not found when searching for memories")
        
        return memories
    
    def get_context_for_query(self, query_text: str, top_k: int = 5) -> str:
        """
        Get relevant context from the graph for answering a query (RAG approach)
        
        Args:
            query_text: The user's query
            top_k: Maximum number of memories to retrieve
            
        Returns:
            Formatted context string
        """
        # Simple keyword matching for now
        # TODO: Use embeddings/semantic search for better retrieval
        query_lower = query_text.lower()
        relevant_memories = []
        
        # Search through all memory nodes
        for node, data in self.graph.nodes(data=True):
            if data.get('type') == 'memory':
                content = data.get('content', '').lower()
                keyword = data.get('keyword', '').lower()
                
                # Check if query words appear in memory
                if any(word in content or word in keyword for word in query_lower.split()):
                    relevant_memories.append({
                        'content': data.get('content', ''),
                        'keyword': data.get('keyword', ''),
                        'timestamp': data.get('timestamp', '')
                    })
        
        # Limit to top_k
        relevant_memories = relevant_memories[:top_k]
        
        # Format as context
        if not relevant_memories:
            return "No previous context found."
        
        context_parts = ["RELEVANT MEMORIES:"]
        for i, mem in enumerate(relevant_memories, 1):
            context_parts.append(
                f"{i}. [{mem['keyword']}] {mem['content']} (at {mem['timestamp']})"
            )
        
        context = "\n".join(context_parts)
        logger.debug(f"Retrieved {len(relevant_memories)} memories for query context")
        return context
    
    def get_all_entities_by_type(self, entity_type: str) -> List[Tuple[str, Dict]]:
        """
        Get all entities of a specific type
        
        Args:
            entity_type: Type to filter by (person, event, emotion, etc.)
            
        Returns:
            List of (entity_name, attributes) tuples
        """
        entities = [
            (node, data) 
            for node, data in self.graph.nodes(data=True)
            if data.get('type') == entity_type
        ]
        
        logger.debug(f"Found {len(entities)} entities of type '{entity_type}'")
        return entities
    
    def get_user_relationships(self) -> List[Dict]:
        """
        Get all direct relationships from the user node
        
        Returns:
            List of relationship dictionaries
        """
        relationships = []
        
        for neighbor in self.graph.neighbors(self.user_node):
            edge_data = self.graph.edges[self.user_node, neighbor]
            node_data = self.graph.nodes[neighbor]
            
            relationships.append({
                'entity': neighbor,
                'entity_type': node_data.get('type', 'unknown'),
                'relation_type': edge_data.get('relation_type', 'unknown'),
                'created_at': edge_data.get('created_at', '')
            })
        
        return relationships
    
    def get_graph_stats(self) -> Dict:
        """Get statistics about the knowledge graph"""
        stats = {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'entities_by_type': {},
            'total_memories': 0
        }
        
        # Count entities by type
        for node, data in self.graph.nodes(data=True):
            entity_type = data.get('type', 'unknown')
            stats['entities_by_type'][entity_type] = stats['entities_by_type'].get(entity_type, 0) + 1
            
            if entity_type == 'memory':
                stats['total_memories'] += 1
        
        return stats
    
    def export_graph(self, filepath: str) -> None:
        """
        Export graph to a JSON file
        
        Args:
            filepath: Path to save the graph
        """
        data = nx.node_link_data(self.graph)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Graph exported to {filepath}")
    
    def import_graph(self, filepath: str) -> None:
        """
        Import graph from a JSON file
        
        Args:
            filepath: Path to load the graph from
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        self.graph = nx.node_link_graph(data)
        logger.info(f"Graph imported from {filepath}")
    
    def visualize_graph(self, height: str = "600px", width: str = "100%") -> str:
        """
        Create an interactive HTML visualization of the knowledge graph using pyvis
        
        Args:
            height: Height of the visualization
            width: Width of the visualization
            
        Returns:
            HTML string containing the visualization
        """
        try:
            from pyvis.network import Network
        except ImportError:
            logger.error("pyvis not installed. Install with: pip install pyvis")
            return None
        
        # Create pyvis network
        net = Network(height=height, width=width, directed=True, notebook=True)
        
        # Color scheme for different entity types
        color_map = {
            'user': '#FF6B6B',      # Red
            'person': '#4ECDC4',     # Teal
            'event': '#95E1D3',      # Light green
            'emotion': '#F9A825',    # Yellow
            'topic': '#9B59B6',      # Purple
            'memory': '#74B9FF',     # Blue
            'unknown': '#CCCCCC'     # Gray
        }
        
        # Shape scheme for different entity types
        shape_map = {
            'user': 'star',
            'person': 'dot',
            'event': 'square',
            'emotion': 'triangle',
            'topic': 'diamond',
            'memory': 'box',
            'unknown': 'ellipse'
        }
        
        # Add nodes with attributes
        for node, data in self.graph.nodes(data=True):
            entity_type = data.get('type', 'unknown')
            color = color_map.get(entity_type, '#CCCCCC')
            shape = shape_map.get(entity_type, 'dot')
            
            # Create label
            if entity_type == 'memory':
                # Truncate memory content for display
                content = data.get('content', node)
                label = content[:30] + '...' if len(content) > 30 else content
                title = f"Memory: {content}"
            else:
                label = node
                title = f"{entity_type.title()}: {node}"
            
            # Adjust size based on type
            size = 30 if entity_type == 'user' else 20 if entity_type == 'person' else 15
            
            net.add_node(
                node,
                label=label,
                title=title,
                color=color,
                shape=shape,
                size=size
            )
        
        # Add edges with labels
        for source, target, data in self.graph.edges(data=True):
            relation_type = data.get('relation_type', 'related')
            net.add_edge(
                source,
                target,
                title=relation_type,
                label=relation_type,
                arrows='to'
            )
        
        # Configure physics for better layout
        net.set_options("""
        {
          "physics": {
            "enabled": true,
            "barnesHut": {
              "gravitationalConstant": -8000,
              "centralGravity": 0.3,
              "springLength": 95,
              "springConstant": 0.04,
              "damping": 0.09
            },
            "stabilization": {
              "enabled": true,
              "iterations": 100
            }
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "zoomView": true,
            "dragView": true
          },
          "nodes": {
            "font": {
              "size": 14,
              "face": "arial"
            }
          },
          "edges": {
            "font": {
              "size": 10,
              "align": "middle"
            },
            "smooth": {
              "type": "continuous"
            }
          }
        }
        """)
        
        # Generate HTML directly in memory
        html_string = net.generate_html()
        logger.info("Graph visualization HTML generated in memory")
        
        return html_string
    
    def create_simple_visualization(self):
        """
        Create a simple matplotlib visualization as a fallback
        Returns a matplotlib figure object
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches
        except ImportError:
            logger.error("matplotlib not installed")
            return None
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Use spring layout for positioning
        pos = nx.spring_layout(self.graph, k=2, iterations=50)
        
        # Color scheme
        color_map = {
            'user': '#FF6B6B',
            'person': '#4ECDC4',
            'event': '#95E1D3',
            'emotion': '#F9A825',
            'topic': '#9B59B6',
            'memory': '#74B9FF',
            'unknown': '#CCCCCC'
        }
        
        # Get node colors based on type
        node_colors = [
            color_map.get(self.graph.nodes[node].get('type', 'unknown'), '#CCCCCC')
            for node in self.graph.nodes()
        ]
        
        # Get node sizes based on type
        node_sizes = [
            1000 if self.graph.nodes[node].get('type') == 'user'
            else 600 if self.graph.nodes[node].get('type') == 'person'
            else 400
            for node in self.graph.nodes()
        ]
        
        # Draw nodes
        nx.draw_networkx_nodes(
            self.graph, pos,
            node_color=node_colors,
            node_size=node_sizes,
            alpha=0.8,
            ax=ax
        )
        
        # Draw edges
        nx.draw_networkx_edges(
            self.graph, pos,
            edge_color='gray',
            arrows=True,
            arrowsize=15,
            alpha=0.5,
            ax=ax
        )
        
        # Draw labels
        labels = {}
        for node in self.graph.nodes():
            node_type = self.graph.nodes[node].get('type', 'unknown')
            if node_type == 'memory':
                # Truncate memory labels
                content = self.graph.nodes[node].get('content', node)
                labels[node] = content[:15] + '...' if len(content) > 15 else content
            else:
                labels[node] = node
        
        nx.draw_networkx_labels(
            self.graph, pos,
            labels,
            font_size=8,
            font_weight='bold',
            ax=ax
        )
        
        # Create legend
        legend_elements = [
            mpatches.Patch(color=color_map['user'], label='User'),
            mpatches.Patch(color=color_map['person'], label='Person'),
            mpatches.Patch(color=color_map['event'], label='Event'),
            mpatches.Patch(color=color_map['emotion'], label='Emotion'),
            mpatches.Patch(color=color_map['topic'], label='Topic'),
            mpatches.Patch(color=color_map['memory'], label='Memory')
        ]
        ax.legend(handles=legend_elements, loc='upper left')
        
        ax.set_title("Knowledge Graph Visualization", fontsize=16, fontweight='bold')
        ax.axis('off')
        plt.tight_layout()
        
        logger.info("Simple matplotlib visualization created")
        return fig

from flask_login import UserMixin
from datetime import datetime, timedelta
import heapq
from collections import deque, defaultdict
import math

class User(UserMixin):
    """User model for authentication and profile information."""
    def __init__(self, id=None, username=None, email=None, password_hash=None, 
                 full_name=None, farm_name=None, location=None, farm_type=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.full_name = full_name
        self.farm_name = farm_name
        self.location = location
        self.farm_type = farm_type
        self.date_registered = datetime.now()
    
    def __repr__(self):
        return f'<User {self.username}>'

# Priority Queue for Activity Management
class ActivityPriorityQueue:
    """Priority queue implementation for activities."""
    def __init__(self):
        self.queue = []
        self.entry_finder = {}
        self.REMOVED = '<removed>'
        self.counter = 0
    
    def add_activity(self, activity, priority=0):
        """Add a new activity or update the priority of an existing activity."""
        if activity['id'] in self.entry_finder:
            self.remove_activity(activity['id'])
        count = self.counter
        self.counter += 1
        entry = [priority, count, activity]
        self.entry_finder[activity['id']] = entry
        heapq.heappush(self.queue, entry)
    
    def remove_activity(self, activity_id):
        """Mark an existing activity as removed. Raise KeyError if not found."""
        entry = self.entry_finder.pop(activity_id)
        entry[-1] = self.REMOVED
    
    def pop_activity(self):
        """Remove and return the lowest priority activity. Raise KeyError if empty."""
        while self.queue:
            priority, count, activity = heapq.heappop(self.queue)
            if activity is not self.REMOVED:
                del self.entry_finder[activity['id']]
                return activity
        raise KeyError('pop from an empty priority queue')
    
    def get_all_activities(self):
        """Return all activities in priority order without removing them."""
        activities = []
        # Create a copy of the queue to avoid modifying the original
        temp_queue = self.queue.copy()
        
        # Extract activities in priority order
        while temp_queue:
            priority, count, activity = heapq.heappop(temp_queue)
            if activity is not self.REMOVED:
                activities.append(activity)
        
        return activities

# Circular Linked List for Recurring Tasks
class Node:
    """Node in a circular linked list."""
    def __init__(self, activity):
        self.activity = activity
        self.next = None

class CircularLinkedList:
    """Circular linked list implementation for recurring tasks."""
    def __init__(self):
        self.head = None
    
    def append(self, activity):
        """Add a new activity to the circular linked list."""
        new_node = Node(activity)
        if not self.head:
            self.head = new_node
            new_node.next = new_node  # Point to itself for a single node
            return
        
        # Find the last node
        temp = self.head
        while temp.next != self.head:
            temp = temp.next
        
        # Add the new node
        temp.next = new_node
        new_node.next = self.head
    
    def remove(self, activity_id):
        """Remove an activity from the circular linked list by id."""
        if not self.head:
            return
        
        # If the head is to be removed
        if self.head.activity['id'] == activity_id:
            # If there's only one node
            if self.head.next == self.head:
                self.head = None
                return
            
            # Find the last node
            temp = self.head
            while temp.next != self.head:
                temp = temp.next
            
            # Update the last node's next pointer
            temp.next = self.head.next
            self.head = self.head.next
            return
        
        # Find the activity to remove
        prev = None
        current = self.head
        
        while True:
            if current.activity['id'] == activity_id:
                prev.next = current.next
                return
            
            prev = current
            current = current.next
            
            # If we've gone all the way around without finding the activity
            if current == self.head:
                break
    
    def get_all_activities(self):
        """Return all activities in the circular linked list."""
        activities = []
        if not self.head:
            return activities
        
        current = self.head
        while True:
            activities.append(current.activity)
            current = current.next
            if current == self.head:
                break
        
        return activities
    
    def get_next_occurrence(self, activity_id, current_date):
        """Calculate the next occurrence of a recurring activity."""
        if not self.head:
            return None
        
        current = self.head
        while True:
            if current.activity['id'] == activity_id:
                activity = current.activity
                interval_days = activity.get('interval_days', 7)  # Default 7 days if not specified
                last_date = datetime.strptime(activity['date'], '%Y-%m-%d')
                
                # Calculate next occurrence from the last date
                while last_date <= current_date:
                    last_date = last_date + timedelta(days=interval_days)
                
                return last_date.strftime('%Y-%m-%d')
            
            current = current.next
            if current == self.head:
                break
        
        return None

# Inventory Management System with Alerts
class InventoryManager:
    """Inventory management system with low stock alerts."""
    def __init__(self):
        self.items = {}
        self.alerts = []
    
    def add_item(self, item):
        """Add a new item to inventory or update existing item."""
        self.items[item['id']] = item
        self._check_stock_level(item)
    
    def remove_item(self, item_id):
        """Remove an item from inventory."""
        if item_id in self.items:
            del self.items[item_id]
    
    def update_quantity(self, item_id, quantity):
        """Update the quantity of an item in inventory."""
        if item_id in self.items:
            self.items[item_id]['quantity'] = quantity
            self._check_stock_level(self.items[item_id])
    
    def get_all_items(self):
        """Return all items in inventory."""
        return list(self.items.values())
    
    def _check_stock_level(self, item):
        """Check if an item is below its minimum stock level."""
        if item['quantity'] <= item.get('min_quantity', 0):
            alert = {
                'item_id': item['id'],
                'item_name': item['name'],
                'current_quantity': item['quantity'],
                'min_quantity': item.get('min_quantity', 0),
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            # Avoid duplicate alerts
            for existing_alert in self.alerts:
                if existing_alert['item_id'] == alert['item_id']:
                    return
            self.alerts.append(alert)
    
    def get_alerts(self):
        """Return all current inventory alerts."""
        return self.alerts
    
    def clear_alert(self, item_id):
        """Clear the alert for an item."""
        self.alerts = [alert for alert in self.alerts if alert['item_id'] != item_id]
    
    def check_availability_for_activity(self, activity, required_items):
        """Check if there's enough inventory for an activity."""
        missing_items = []
        
        for req in required_items:
            inventory_id = req['inventory_id']
            quantity_required = req['quantity_required']
            
            if inventory_id in self.items:
                item = self.items[inventory_id]
                if item['quantity'] < quantity_required:
                    missing_items.append({
                        'id': item['id'],
                        'name': item['name'],
                        'available': item['quantity'],
                        'required': quantity_required,
                        'shortage': quantity_required - item['quantity']
                    })
            else:
                # Item not found in inventory
                missing_items.append({
                    'id': inventory_id,
                    'name': 'Unknown Item',
                    'available': 0,
                    'required': quantity_required,
                    'shortage': quantity_required
                })
        
        return {
            'activity_id': activity['id'],
            'activity_type': activity['activity_type'],
            'date': activity['date'],
            'has_shortages': len(missing_items) > 0,
            'missing_items': missing_items
        }

# Weather Analytics System
class WeatherAnalytics:
    """Weather analytics for farm management."""
    def __init__(self):
        self.weather_data = {}  # Keyed by date
    
    def add_weather_data(self, weather):
        """Add or update weather data for a specific date."""
        date_str = weather['date']
        self.weather_data[date_str] = weather
    
    def get_forecast(self, start_date, days=7):
        """Get weather forecast for a range of days."""
        forecast = []
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        
        for i in range(days):
            date_str = current_date.strftime('%Y-%m-%d')
            if date_str in self.weather_data:
                forecast.append(self.weather_data[date_str])
            current_date = current_date + timedelta(days=1)
        
        return forecast
    
    def check_rain_forecast(self, start_date, days=7):
        """Check if rain is forecasted in the next few days."""
        forecast = self.get_forecast(start_date, days)
        rain_days = []
        
        for weather in forecast:
            # Check for rain conditions
            if weather.get('conditions', '').lower() in ['rain', 'rainy', 'showers', 'thunderstorm'] or \
               weather.get('precipitation', 0) > 0.5:  # More than 0.5mm of precipitation
                rain_days.append(weather)
        
        return rain_days
    
    def should_skip_irrigation(self, activity, start_date):
        """Determine if an irrigation activity should be skipped due to rain."""
        if activity['activity_type'].lower() != 'irrigation':
            return False
        
        activity_date = datetime.strptime(activity['date'], '%Y-%m-%d')
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        
        # Check if the activity is scheduled for the next 3 days
        days_difference = (activity_date - current_date).days
        if 0 <= days_difference <= 3:
            # Check if rain is forecasted within 24 hours before or after
            rain_check_start = (activity_date - timedelta(days=1)).strftime('%Y-%m-%d')
            rain_forecast = self.check_rain_forecast(rain_check_start, 3)
            
            if rain_forecast:
                return True
        
        return False


# Community system with Graph data structure for user connections
class CommunityGraph:
    """Graph implementation for community connections and friend recommendations."""
    def __init__(self):
        self.graph = defaultdict(dict)  # Adjacency list representation with weights
    
    def add_user(self, user_id):
        """Add a user node to the graph if it doesn't exist."""
        if user_id not in self.graph:
            self.graph[user_id] = {}
    
    def add_connection(self, user_id, connected_user_id, strength=1):
        """Add a connection (edge) between two users with a specified strength (weight)."""
        self.add_user(user_id)
        self.add_user(connected_user_id)
        
        # Bidirectional connection
        self.graph[user_id][connected_user_id] = strength
        self.graph[connected_user_id][user_id] = strength
    
    def remove_connection(self, user_id, connected_user_id):
        """Remove a connection between users."""
        if user_id in self.graph and connected_user_id in self.graph[user_id]:
            del self.graph[user_id][connected_user_id]
        
        if connected_user_id in self.graph and user_id in self.graph[connected_user_id]:
            del self.graph[connected_user_id][user_id]
    
    def get_connections(self, user_id):
        """Get all direct connections for a user."""
        if user_id in self.graph:
            return self.graph[user_id]
        return {}
    
    def find_friend_recommendations(self, user_id, max_depth=2):
        """Use Dijkstra's algorithm to find potential friend recommendations.
        Returns users sorted by connection strength (closest first).
        """
        if user_id not in self.graph:
            return []
        
        # Initialize distances with infinity for all nodes except the start
        distances = {node: float('inf') for node in self.graph}
        distances[user_id] = 0
        
        # Priority queue for Dijkstra's algorithm
        priority_queue = [(0, user_id)]  # (distance, node)
        
        # Track visited nodes and their paths
        visited = set()
        paths = {user_id: []}  # Track the path to each node
        
        while priority_queue:
            current_distance, current_node = heapq.heappop(priority_queue)
            
            # Skip if we've already processed this node
            if current_node in visited:
                continue
            
            # Mark as visited
            visited.add(current_node)
            
            # Skip if we've reached our max depth
            if len(paths[current_node]) >= max_depth:
                continue
            
            # Check all neighbors
            for neighbor, weight in self.graph[current_node].items():
                # Friendship strength is inverse of weight (higher weight = stronger connection)
                distance = current_distance + (1 / weight)
                
                # If we found a shorter path
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    
                    # Update the path
                    paths[neighbor] = paths[current_node] + [current_node]
                    
                    # Add to the priority queue
                    heapq.heappush(priority_queue, (distance, neighbor))
        
        # Filter out the original user and direct connections
        direct_connections = set(self.graph[user_id].keys())
        recommendations = []
        
        for node, distance in distances.items():
            if node != user_id and node not in direct_connections and distance < float('inf'):
                # Calculate a score based on distance (lower is better)
                score = 1 / (distance + 1)  # Add 1 to avoid division by zero
                recommendations.append({
                    'user_id': node,
                    'score': score,
                    'path': paths[node] + [node]  # Complete path including the recommendation
                })
        
        # Sort by score (highest first)
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations
    
    def calculate_connection_strength(self, user_id, other_user_id):
        """Calculate the connection strength between two users based on interactions."""
        if user_id not in self.graph or other_user_id not in self.graph:
            return 0
        
        # Direct connection
        if other_user_id in self.graph[user_id]:
            return self.graph[user_id][other_user_id]
        
        # No direct connection, try to find a path
        visited = set()
        queue = deque([(user_id, 1.0)])  # (node, strength so far)
        
        while queue:
            current, strength = queue.popleft()
            
            if current in visited:
                continue
            
            visited.add(current)
            
            # Check if we found the target
            if current == other_user_id:
                return strength
            
            # Try all connections
            for neighbor, weight in self.graph[current].items():
                if neighbor not in visited:
                    # Strength decreases with each hop
                    new_strength = strength * (weight / 10)
                    queue.append((neighbor, new_strength))
        
        return 0  # No connection found


# Post tagging system with tree structure for efficient tag searching
class TagNode:
    """Node in a tag tree data structure."""
    def __init__(self, tag_id, tag_name, category):
        self.tag_id = tag_id
        self.tag_name = tag_name
        self.category = category
        self.children = {}  # Child tags as subtree
        self.posts = []  # Post IDs associated with this tag
    
    def add_post(self, post_id):
        """Associate a post with this tag."""
        if post_id not in self.posts:
            self.posts.append(post_id)
    
    def remove_post(self, post_id):
        """Remove a post association."""
        if post_id in self.posts:
            self.posts.remove(post_id)
    
    def get_post_count(self):
        """Get the number of posts associated with this tag."""
        return len(self.posts)


class TagTree:
    """Tree-based implementation for tag management."""
    def __init__(self):
        # Root node is a dummy node that holds categories as its children
        self.root = TagNode(0, "ROOT", "root")
    
    def add_tag(self, tag_id, tag_name, category):
        """Add a tag to the tree under the specified category."""
        # Create category node if it doesn't exist
        if category not in self.root.children:
            self.root.children[category] = TagNode(-1, category, "category")
        
        # Add tag as a child of the category
        self.root.children[category].children[tag_name] = TagNode(tag_id, tag_name, category)
    
    def add_post_to_tag(self, tag_id, tag_name, category, post_id):
        """Associate a post with a specific tag."""
        if category in self.root.children and tag_name in self.root.children[category].children:
            self.root.children[category].children[tag_name].add_post(post_id)
            # Also add to category node for category-wide search
            self.root.children[category].add_post(post_id)
    
    def find_posts_by_tag(self, tag_name, category=None):
        """Find all posts associated with a tag."""
        posts = []
        
        # If category is provided, look only in that category
        if category:
            if category in self.root.children and tag_name in self.root.children[category].children:
                posts = self.root.children[category].children[tag_name].posts
        else:
            # Look in all categories
            for cat in self.root.children:
                if tag_name in self.root.children[cat].children:
                    posts.extend(self.root.children[cat].children[tag_name].posts)
        
        return posts
    
    def find_posts_by_category(self, category):
        """Find all posts associated with a category."""
        if category in self.root.children:
            return self.root.children[category].posts
        return []
    
    def get_all_tags(self):
        """Get all tags organized by category."""
        tags = {}
        for category, category_node in self.root.children.items():
            tags[category] = {}
            for tag_name, tag_node in category_node.children.items():
                tags[category][tag_name] = {
                    'id': tag_node.tag_id,
                    'post_count': tag_node.get_post_count()
                }
        return tags
    
    def search_tags(self, query):
        """Search for tags that match a query string."""
        results = []
        query = query.lower()
        
        for category, category_node in self.root.children.items():
            for tag_name, tag_node in category_node.children.items():
                if query in tag_name.lower():
                    results.append({
                        'id': tag_node.tag_id,
                        'name': tag_node.tag_name,
                        'category': category,
                        'post_count': tag_node.get_post_count()
                    })
        
        return results

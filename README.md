# Farm-Management-System
A smart web design for maintaining and tracking farm activities.








Running the Project Locally
Prerequisites
1.	Python 3.7+ installed
2.	Git installed
3.	Basic understanding of command-line operations
Step-by-Step Instructions
1.	Clone the Repository:
git clone <your-repository-url>
cd farm-management-system
2.	Set Up Virtual Environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
3.	Install Dependencies:
pip install flask flask-login flask-wtf flask-sqlalchemy werkzeug email-validator
4.	Initialize the Database:
python app.py  # This will create and initialize the database
5.	Run the Application:
flask run  # Or: python -m flask run
6.	Access the Application:
Open your browser and go to http://127.0.0.1:5000











Project Details

Problem Statement : To design a Farm management system



Farm Management System Implementation Breakdown
Project Overview
I've built a comprehensive farm management system that leverages various data structures to efficiently organize farm data, track activities, manage inventory, monitor weather, and connect farmers through a community platform. Let me explain the implementation details:
Data Structures Implementation
1. Priority Queue for Activity Management
•	File Location: models.py - ActivityPriorityQueue class
•	Purpose: Efficiently manages farm activities based on their priority
•	Implementation Details:
o	Uses Python's heapq library for heap operations
o	Activities are stored with priority values (lower values = higher priority)
o	Each activity is assigned a unique count to maintain FIFO order for equal priorities
o	Supports operations like add_activity(), remove_activity(), pop_activity()
o	Time complexity for queue operations is O(log n)
o	Includes a special REMOVED marker to handle removed items efficiently
2. Circular Linked List for Recurring Tasks
•	File Location: models.py - Node and CircularLinkedList classes
•	Purpose: Manages recurring farm activities (like irrigation, fertilizing) in a cyclical pattern
•	Implementation Details:
o	Custom Node class with pointers to next nodes
o	Last node points back to the first node (circular structure)
o	Maintains interval information for recurring activities
o	Efficiently calculates next occurrence dates
o	Handles operations like append(), remove(), get_all_activities()
o	When a recurring activity is completed, system automatically schedules the next occurrence
3. Graph Data Structure for Community Connections
•	File Location: models.py - CommunityGraph class
•	Purpose: Establishes connections between farmers and enables friend recommendations
•	Implementation Details:
o	Uses an adjacency list representation with Python dictionaries
o	Each user is a node in the graph
o	Connections between users are weighted edges (higher weight = stronger connection)
o	Connection strength increases as users interact (comment, like posts)
o	Implements Dijkstra's algorithm to find potential friend recommendations
o	Calculates paths through the network to find indirect connections
o	Time complexity for friend recommendations is O(E log V) where E is edges and V is vertices
4. Tree Data Structure for Tag Management
•	File Location: models.py - TagNode and TagTree classes
•	Purpose: Organizes community posts with a hierarchical tagging system
•	Implementation Details:
o	Implements a tree with a root node and children representing categories and tags
o	Categories are first-level nodes, tags are second-level nodes
o	Allows efficient searching of posts by tags and categories
o	Maintains post counts for each tag
o	Supports operations like add_tag(), add_post_to_tag(), find_posts_by_tag()
o	Enables browsing posts by category hierarchies
5. Inventory Management System
•	File Location: models.py - InventoryManager class
•	Purpose: Tracks farm inventory items and generates low stock alerts
•	Implementation Details:
o	Uses dictionary-based storage for fast lookup
o	Automatically checks stock levels when quantities change
o	Generates alerts when items fall below minimum quantities
o	Associates inventory items with farming activities
o	Validates if there's enough inventory for scheduled activities
6. Weather Analytics System
•	File Location: models.py - WeatherAnalytics class
•	Purpose: Tracks weather data and enables smart farming decisions
•	Implementation Details:
o	Stores weather data with date-based indexing for fast retrieval
o	Checks weather forecasts to intelligently manage irrigation
o	Provides methods to skip irrigation when rain is forecasted
o	Has forecasting capabilities for multi-day planning
Database System
The project uses SQLite3 for data storage (farm_management.db) with the following tables:
Database Structure
•	File Location: app.py - init_db() function
•	Tables:
i.	users: Stores user authentication and profile data
ii.	inventory: Manages farm supplies and equipment
iii.	activity_types: Predefined activity categories
iv.	crop_types: Supported crop varieties
v.	activities: Core table for farm tasks with scheduling info
vi.	activity_inventory: Junction table linking activities to required inventory
vii.	weather_data: Historical and forecast weather information
viii.	community_posts: User-generated community content
ix.	tags: Categories and labels for community posts
x.	post_tags: Junction table linking posts to tags
xi.	comments: User comments on community posts
xii.	user_connections: Records of user relationships (for graph structure)
xiii.	private_messages: Direct communications between users
Database Operations
•	Connection Management: Uses get_db_connection() function in app.py
•	Data Access: Uses cursor-based SQL operations for CRUD operations
•	Transaction Safety: Implements commit() for data integrity
•	Foreign Key Relationships: Maintains referential integrity between tables
•	Default Data: Populates initial activity types, crop types, and tags
Personalized Activity Tracker Logic
Activity Tracking Implementation
•	File Location: app.py - activity-related routes
•	Core Logic:
i.	Activity Creation (add_activity route):
o	Collects activity details (type, date, field, crop, etc.)
o	Sets recurrence pattern if applicable
o	Associates required inventory items
o	Prioritizes activities based on user input
o	Stores in the database with user_id for personalization
ii.	Activity Completion (complete_activity route):
o	Marks activity as completed
o	Updates inventory quantities based on used resources
o	If recurring, automatically generates next occurrence:
	Calculates next date using interval_days
	Creates new activity entry with same properties
	Maintains the recurring pattern using circular linked list concept
iii.	Weather Integration:
o	Checks weather forecast before irrigation activities
o	Can skip or reschedule based on rain predictions
o	Uses should_skip_irrigation method from WeatherAnalytics class
iv.	Inventory Validation:
o	Verifies if required inventory is available for activities
o	Provides warnings for insufficient stock
o	Updates quantities when activities are completed
v.	Priority Management:
o	Activities are organized by priority levels (1-5)
o	Lower numerical values indicate higher priority
o	Priority queue data structure ensures important tasks surface first

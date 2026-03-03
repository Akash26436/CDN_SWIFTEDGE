import threading

class Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None

class LRUCache:
    """
    O(1) LRU Cache implementation using a HashMap and Doubly Linked List.
    Thread-safe for concurrent edge server access.
    """
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {} # Key -> Node
        self.lock = threading.Lock()
        
        # Sentinel nodes
        self.head = Node(0, 0)
        self.tail = Node(0, 0)
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node):
        p = node.prev
        n = node.next
        p.next = n
        n.prev = p

    def _add(self, node):
        # Add to front (most recent)
        n = self.head.next
        self.head.next = node
        node.prev = self.head
        node.next = n
        n.prev = node

    def get(self, key):
        with self.lock:
            if key in self.cache:
                node = self.cache[key]
                self._remove(node)
                self._add(node)
                return node.value
            return None

    def put(self, key, value):
        with self.lock:
            if key in self.cache:
                self._remove(self.cache[key])
            
            node = Node(key, value)
            self._add(node)
            self.cache[key] = node
            
            if len(self.cache) > self.capacity:
                # Evict LRU (from tail)
                lru = self.tail.prev
                self._remove(lru)
                del self.cache[lru.key]

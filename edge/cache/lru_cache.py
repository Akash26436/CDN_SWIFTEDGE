import threading

class Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
        self.lock = threading.Lock()
        self.head = Node(0,0)
        self.tail = Node(0,0)
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add(self, node):
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node

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
                lru = self.tail.prev
                self._remove(lru)
                del self.cache[lru.key]

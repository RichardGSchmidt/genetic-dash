
class HashChain:
    def __init__(self, capacity=8):
        self.capacity = capacity
        self.size = 0
        self.buckets = [[] for i in range(self.capacity)]

    #Hash function that modulos based on capacity, this finds a bucket between 0 < (capacity - 1)
    def hash(self, key):
        return key % self.capacity

    def safe_copy(self):
        copy = HashChain()
        for k in self.keys():
            copy.insert(k, self.get(k))
        return copy


    #Insert add or update a key
    def insert(self, key, value):
        index = self.hash(key)
        # Check if key already exists
        for entry in self.buckets[index]:
            if entry[0] == key:
                entry[1] = value  # Update value if key exists
                return

        # If we get here, the key doesn't exist, so add it
        self.buckets[index].append([key, value])
        self.size += 1
        self.adjust_if_needed()

    def remove(self,key):
        index = self.hash(key)
        for entry in self.buckets[index]:
            if entry[0] == key:
                self.buckets[index].remove(entry)
                self.size -= 1
                self.adjust_if_needed()
                return 0

        #if the program gets this far, the requested key was not found and a console message is displayed
        print(f'Key: {key} not found, removal has failed')
        return -1

    # Method to get an object based on key (Task B)
    # since this is used to implement a package object it
    # returns a package object as detailed in package.py
    # which include the following attributes:
    #                   delivery address, due_time, city, zipcode, package weight, and delivery status
    def get(self, key):
        index = self.hash(key)
        for entry in self.buckets[index]:
            if entry[0] == key:
                return entry[1]
        return None

    # Method to return all keys
    def keys(self):
        all_keys = []
        for bucket in self.buckets:
            for key, x in bucket:
                all_keys.append(key)
        return all_keys


    def adjust(self, new_capacity):
        old_buckets = self.buckets
        self.capacity = new_capacity
        self.buckets = [[] for i in range(new_capacity)]
        self.size = 0 #Reset size

        #uses a direct implementation of insertion without calling insert() in order to avoid infinite loops
        for bucket in old_buckets:
            for entry in bucket:
                key, value = entry[0], entry[1]
                index = self.hash(key)
                self.buckets[index].append([key, value])
                self.size += 1

    def adjust_if_needed(self):
        load_factor = self.size / self.capacity
        if load_factor > 0.75:
            self.adjust(2 * self.capacity)
        elif load_factor < 0.25 and self.capacity > 8:
            self.adjust(self.capacity // 2)

    def __str__(self):
        return str(self.buckets)
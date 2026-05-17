NUM_ROOMS, DAYS = 4, 30

class Node:
    def __init__(self, check_in, check_out, room, bid):
        self.check_in, self.check_out = check_in, check_out
        self.room, self.bid = room, bid
        self.max_right = check_out
        self.left = self.right = None
        self.height = 1

def h(n):  return n.height    if n else 0
def mr(n): return n.max_right if n else 0
def fix(n):
    n.height    = 1 + max(h(n.left), h(n.right))
    n.max_right = max(n.check_out, mr(n.left), mr(n.right))

def rot_r(z):
    y = z.left; z.left = y.right; y.right = z; fix(z); fix(y); return y
def rot_l(z):
    y = z.right; z.right = y.left; y.left = z; fix(z); fix(y); return y

def balance(n):
    fix(n)
    bf = h(n.left) - h(n.right)
    if bf > 1:
        if h(n.left.left) < h(n.left.right): n.left = rot_l(n.left)
        return rot_r(n)
    if bf < -1:
        if h(n.right.right) < h(n.right.left): n.right = rot_r(n.right)
        return rot_l(n)
    return n

def insert(n, ci, co, room, bid):
    if n is None: return Node(ci, co, room, bid)
    if ci <= n.check_in: n.left  = insert(n.left,  ci, co, room, bid)
    else:                n.right = insert(n.right, ci, co, room, bid)
    return balance(n)

def delete(n, ci, bid):
    if n is None: return None
    if   ci < n.check_in: n.left  = delete(n.left,  ci, bid)
    elif ci > n.check_in: n.right = delete(n.right, ci, bid)
    elif n.bid == bid:
        if not n.left:  return n.right
        if not n.right: return n.left
        s = n.right
        while s.left: s = s.left
        n.check_in, n.check_out, n.room, n.bid = s.check_in, s.check_out, s.room, s.bid
        n.right = delete(n.right, s.check_in, s.bid)
    else:
        n.left  = delete(n.left,  ci, bid)
        n.right = delete(n.right, ci, bid)
    return balance(n)

def query(n, day, found, stats):
    if n is None: return
    stats[0] += 1
    if n.max_right <= day: stats[1] += 1; return   # prune subtree
    query(n.left, day, found, stats)
    if n.check_in <= day:
        if day < n.check_out:
            found.append({"room": n.room, "bid": n.bid,
                          "check_in": n.check_in, "check_out": n.check_out})
        query(n.right, day, found, stats)

def overlaps(n, ci, co):
    if n is None or n.max_right <= ci: return False
    if n.check_in < co and ci < n.check_out: return True
    return overlaps(n.left, ci, co) or overlaps(n.right, ci, co)

def inorder(n, out):
    if n is None: return
    inorder(n.left, out); out.append((n.check_in, n.check_out)); inorder(n.right, out)

class Hotel:
    def __init__(self):
        self.next_bid = 1
        self.bookings = {}
        self.rooms  = {r: None for r in range(1, NUM_ROOMS + 1)}
        self.single = None

    def add(self, ci, co, room):
        if not (1 <= room <= NUM_ROOMS):       return None, "Invalid room"
        if ci < 1 or co > DAYS or ci >= co:    return None, "Invalid dates"
        if overlaps(self.rooms[room], ci, co): return None, f"Room {room} already booked"
        bid = self.next_bid; self.next_bid += 1
        self.rooms[room] = insert(self.rooms[room], ci, co, room, bid)
        self.single      = insert(self.single,      ci, co, room, bid)
        self.bookings[bid] = {"bid": bid, "check_in": ci, "check_out": co, "room": room}
        return bid, None

    def remove(self, bid):
        if bid not in self.bookings: return False
        b = self.bookings.pop(bid)
        self.rooms[b["room"]] = delete(self.rooms[b["room"]], b["check_in"], bid)
        self.single           = delete(self.single,           b["check_in"], bid)
        return True

    def query_date(self, day):
        found, stats = [], [0, 0]
        query(self.single, day, found, stats)
        return {"hits": found, "visited": stats[0], "pruned": stats[1]}

    def suggest(self, desired, nights):
        results = []
        for room in range(1, NUM_ROOMS + 1):
            if not overlaps(self.rooms[room], desired, desired + nights):
                results.append({"room": room, "start": desired}); continue
            booked = []; inorder(self.rooms[room], booked)
            prev = 1
            for s, e in booked:
                if s - prev >= nights:
                    results.append({"room": room, "start": prev}); break
                prev = max(prev, e)
        return results

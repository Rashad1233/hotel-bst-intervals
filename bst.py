NUM_ROOMS, DAYS = 4, 30

class Node:
    def __init__(self, check_in, check_out, room, bid):
        self.check_in, self.check_out = check_in, check_out
        self.room, self.bid = room, bid
        self.max_right = check_out  # start with own check_out, fix() will update from children
        self.left = self.right = None
        self.height = 1

def h(n):  return n.height    if n else 0
def mr(n): return n.max_right if n else 0
def fix(n):
    n.height    = 1 + max(h(n.left), h(n.right))
    n.max_right = max(n.check_out, mr(n.left), mr(n.right))  # biggest check_out in subtree

def rot_r(z):
    # right rotation: z's left child becomes new root, z goes right
    # fix() bottom-up because z's subtree changed first
    y = z.left; z.left = y.right; y.right = z; fix(z); fix(y); return y

def rot_l(z):
    # mirror of rot_r
    y = z.right; z.right = y.left; y.left = z; fix(z); fix(y); return y

def balance(n):
    # AVL: keep height difference between left and right <= 1
    # balance factor > 1 means left-heavy, < -1 means right-heavy
    fix(n)
    bf = h(n.left) - h(n.right)
    if bf > 1:
        if h(n.left.left) < h(n.left.right): n.left = rot_l(n.left)  # left-right case
        return rot_r(n)
    if bf < -1:
        if h(n.right.right) < h(n.right.left): n.right = rot_r(n.right)  # right-left case
        return rot_l(n)
    return n

def insert(n, ci, co, room, bid):
    # BST insert by check_in, then rebalance on the way back up -> O(log n)
    if n is None: return Node(ci, co, room, bid)
    if ci <= n.check_in: n.left  = insert(n.left,  ci, co, room, bid)
    else:                n.right = insert(n.right, ci, co, room, bid)
    return balance(n)  # fix() inside balance updates max_right on every node we touched

def delete(n, ci, bid):
    # O(log n): find by check_in, if same bid delete it, otherwise keep searching
    if n is None: return None
    if   ci < n.check_in: n.left  = delete(n.left,  ci, bid)
    elif ci > n.check_in: n.right = delete(n.right, ci, bid)
    elif n.bid == bid:
        if not n.left:  return n.right  # one child cases are easy
        if not n.right: return n.left
        # two children: replace with inorder successor (leftmost in right subtree)
        s = n.right
        while s.left: s = s.left
        n.check_in, n.check_out, n.room, n.bid = s.check_in, s.check_out, s.room, s.bid
        n.right = delete(n.right, s.check_in, s.bid)
    else:
        # same check_in but different bid (two bookings on same day, different rooms)
        n.left  = delete(n.left,  ci, bid)
        n.right = delete(n.right, ci, bid)
    return balance(n)

def query(n, day, found, stats):
    # find all bookings where check_in <= day < check_out -> O(log n + k), k = results
    if n is None: return
    stats[0] += 1
    if n.max_right <= day:
        # every check_out in this subtree is <= day, so nothing here can cover day
        stats[1] += 1; return  # skip entire subtree, this is the O(log n) pruning
    query(n.left, day, found, stats)
    if n.check_in <= day:  # only visit right subtree if this node started before day
        if day < n.check_out:  # active booking: guest is still staying on this day
            found.append({"room": n.room, "bid": n.bid,
                          "check_in": n.check_in, "check_out": n.check_out})
        query(n.right, day, found, stats)

def overlaps(n, ci, co):
    # check if any booking in subtree overlaps [ci, co) -> O(log n) with max_right pruning
    if n is None or n.max_right <= ci: return False  # whole subtree ends before ci
    if n.check_in >= co: return overlaps(n.left, ci, co)
    if n.check_in < co and ci < n.check_out: return True  # two intervals overlap iff neither ends before the other starts
    return overlaps(n.left, ci, co) or overlaps(n.right, ci, co)

def inorder(n, out):
    # inorder traversal gives bookings sorted by check_in -> O(n)
    if n is None: return
    inorder(n.left, out); out.append((n.check_in, n.check_out)); inorder(n.right, out)

class Hotel:
    def __init__(self):
        self.next_bid = 1
        self.bookings = {}
        self.rooms  = {r: None for r in range(1, NUM_ROOMS + 1)}  # one BST per room
        self.single = None  # one BST with all rooms together

    def add(self, ci, co, room):
        if not (1 <= room <= NUM_ROOMS):       return None, "Invalid room"
        if ci < 1 or co > DAYS or ci >= co:    return None, "Invalid dates"
        if overlaps(self.rooms[room], ci, co): return None, f"Room {room} already booked"
        bid = self.next_bid; self.next_bid += 1
        # insert into both: per-room tree for conflict checks, single tree for date queries
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
        # for each room try desired date first, otherwise find first gap >= nights wide
        results = []
        for room in range(1, NUM_ROOMS + 1):
            if not overlaps(self.rooms[room], desired, desired + nights):
                results.append({"room": room, "start": desired}); continue
            booked = []; inorder(self.rooms[room], booked)  # sorted by check_in
            prev = 1
            for s, e in booked:
                if s - prev >= nights:  # gap between prev end and next booking start
                    results.append({"room": room, "start": prev}); break
                prev = max(prev, e)
        return results

from collections import deque
import secrets
from flask import Flask, send_file, request, jsonify, session
Piece_values = {
    'P': 1,
    'N': 3,
    'B': 3,
    'R': 5,
    'Q': 9,
    'K': 0
}

def get_piece(move):
    if move[0] in Piece_values:
        return move[0]
    return 'P'

def capture_piece(move):
    if 'x' not in move:
        return None
    
    parts = move.split('x')
    if len(parts) < 2:
        return None
    captured_part = parts[1]

    if captured_part[0] in Piece_values:
        return captured_part[0]
    return 'P'


def calculate_evaluation(move , player):
    piece = get_piece(move)
    value = Piece_values.get(piece , 0)
    captured = capture_piece(move)

    if captured:
        value += Piece_values.get(captured , 0)
        
    return value if player == 'white' else -value

class movenode:
    def __init__(self , move , player , move_number , evaluation , parent):
        self.move = move
        self.player = player
        self.move_number = move_number
        self.parent = parent
        self.evaluation = evaluation
        self.children = []

class chess_move_tree:
    def __init__(self):
        self.root = movenode('start' , 'white' , 0 ,evaluation= 0, parent= None)
        self.current = self.root

    def add_move(self , move):
        new_move_number = self.current.move_number + 1
        next_player = 'black' if self.current.player == 'white' else 'white'
        evaluation = calculate_evaluation(move , self.current.player)
        new_node = movenode(move , next_player , new_move_number , evaluation , self.current)

        self.current.children.append(new_node)
        self.current = new_node

    def move_back(self):
        if self.current.parent:
            self.current = self.current.parent
        
    def reset(self):
        self.current = self.root

    def print_moves(self):
        stored_moves = []
        node = self.current
        while node.parent:
            stored_moves.append(node.move)
            node = node.parent

        stored_moves.reverse()
        print(stored_moves)

    def list_variations(self):
        variations = []
        for child in self.current.children:
            variations.append(child.move)
            
        print(variations)
    
    def dfs_search(self , move , node = None):
        if node == None:
            node = self.root
        
        if node.move == move:
            return node
        
        for child in node.children:
            result = self.dfs_search(move , child)
            if result:
                return result
            
        return None
    
    def bfs_search(self , move):
        Q = deque()
        Q.append(self.root)
        
        while Q:
            node = Q.popleft()
            if node.move == move:
                return node
            for child in node.children:
                Q.append(child)
        return None
    
    def max_depth(self , node = None):
        if node == None:
            node = self.root
        
        if not node.children:
            return 0
        
        return 1 + max(self.max_depth(child) for child in node.children)
    
    def root_branches(self):
        branches = []
        for child in self.root.children:
            branches.append(child.move)
        return len(branches)
    
    def branching_factor(self):
        total_branches = []
        for child in self.current.children:
            total_branches.append(child.move)
        return len(total_branches)

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

trees = {}

def get_tree():
    if 'tree_id' not in session:
        session['tree_id'] = secrets.token_hex(8)
    
    if session['tree_id'] not in trees:
        trees[session['tree_id']] = chess_move_tree()
    
    return trees[session['tree_id']]

def get_current_path(tree):
    path = []
    node = tree.current
    while node.parent:
        path.append({
            'move': node.move,
            'player': node.player,
            'evaluation': node.evaluation,
            'move_number': node.move_number
        })
        node = node.parent
    path.reverse()
    return path

def get_variations(tree):
    variations = []
    for child in tree.current.children:
        variations.append({
            'move': child.move,
            'player': child.player,
            'evaluation': child.evaluation
        })
    return variations

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/api/status')
def status():
    tree = get_tree()
    return jsonify({
        'path': get_current_path(tree),
        'variations': get_variations(tree),
        'stats': {
            'max_depth': tree.max_depth(),
            'root_branches': tree.root_branches(),
            'branching_factor': tree.branching_factor()
        }
    })

@app.route('/api/add_move', methods=['POST'])
def add_move():
    tree = get_tree()
    move = request.json.get('move')
    tree.add_move(move)
    return jsonify({'success': True})

@app.route('/api/move_back', methods=['POST'])
def move_back():
    tree = get_tree()
    tree.move_back()
    return jsonify({'success': True})

@app.route('/api/reset', methods=['POST'])
def reset():
    tree = get_tree()
    tree.reset()
    return jsonify({'success': True})

@app.route('/api/search', methods=['POST'])
def search():
    tree = get_tree()
    move = request.json.get('move')
    result = tree.dfs_search(move)
    
    if result:
        tree.current = result
        return jsonify({
            'found': True,
            'move_number': result.move_number
        })
    else:
        return jsonify({'found': False})

@app.route('/api/select_variation', methods=['POST'])
def select_variation():
    tree = get_tree()
    move = request.json.get('move')
    
    for child in tree.current.children:
        if child.move == move:
            tree.current = child
            break
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
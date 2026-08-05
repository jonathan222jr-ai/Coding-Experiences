#include <iostream>
#include <string>
using namespace std;

// ===================================================
// Definition of a single BST node
// Each node stores an integer key and pointers
// to its left child, right child, and parent.
// ===================================================
struct Node {
    int key;
    Node* left;
    Node* right;
    Node* parent;

    // Constructor: initializes node with given key
    Node(int k) : key(k), left(nullptr), right(nullptr), parent(nullptr) {}
};

// ===================================================
// Binary Search Tree class
// Implements: insert, delete, and traversals
// ===================================================
class BST {
private:
    Node* root; // pointer to root node of the tree

    // --------------------------
    // Helper: Inorder traversal (Left, Root, Right)
    // --------------------------
    void inorder(Node* x) {
        if (x != nullptr) {
            inorder(x->left);
            cout << x->key << endl;
            inorder(x->right);
        }
    }

    // --------------------------
    // Helper: Preorder traversal (Root, Left, Right)
    // --------------------------
    void preorder(Node* x) {
        if (x != nullptr) {
            cout << x->key << endl;
            preorder(x->left);
            preorder(x->right);
        }
    }

    // --------------------------
    // Helper: Postorder traversal (Left, Right, Root)
    // --------------------------
    void postorder(Node* x) {
        if (x != nullptr) {
            postorder(x->left);
            postorder(x->right);
            cout << x->key << endl;
        }
    }

    // --------------------------
    // Helper: Search for a key in the BST
    // Returns pointer to the node containing the key,
    // or nullptr if not found.
    // --------------------------
    Node* search(Node* x, int key) {
        if (x == nullptr || x->key == key)
            return x;
        if (key < x->key)
            return search(x->left, key);
        else
            return search(x->right, key);
    }

    // --------------------------
    // Helper: Find the smallest node (minimum) in a subtree
    // Used in the delete operation
    // --------------------------
    Node* treeMinimum(Node* x) {
        while (x->left != nullptr)
            x = x->left;
        return x;
    }

    // --------------------------
    // Helper: Transplant (replace one subtree with another)
    // Used by deleteKey() to rearrange nodes
    // --------------------------
    void transplant(Node* u, Node* v) {
        if (u->parent == nullptr)
            root = v;                     // u was root
        else if (u == u->parent->left)
            u->parent->left = v;          // replace u with v in left child
        else
            u->parent->right = v;         // replace u with v in right child

        if (v != nullptr)
            v->parent = u->parent;        // link new subtree back to parent
    }

public:
    // Constructor: start with an empty tree
    BST() : root(nullptr) {}

    // ===================================================
    // INSERT operation (same as textbook CLRS algorithm)
    // ===================================================
    void insert(int key) {
        Node* z = new Node(key);   // new node to insert
        Node* y = nullptr;         // will track parent of z
        Node* x = root;            // start from root

        // Traverse tree to find correct spot
        while (x != nullptr) {
            y = x; // keep track of parent
            if (z->key < x->key)
                x = x->left;
            else
                x = x->right;
        }

        // y is parent of z
        z->parent = y;

        // If tree was empty
        if (y == nullptr)
            root = z;
        else if (z->key < y->key)
            y->left = z;
        else
            y->right = z;
    }

    // ===================================================
    // DELETE operation (same as textbook CLRS algorithm)
    // ===================================================
    void deleteKey(int key) {
        Node* z = search(root, key); // find node to delete
        if (z == nullptr)
            return; // key not found → do nothing

        // Case 1: Node has no left child
        if (z->left == nullptr)
            transplant(z, z->right);

        // Case 2: Node has no right child
        else if (z->right == nullptr)
            transplant(z, z->left);

        // Case 3: Node has two children
        else {
            Node* y = treeMinimum(z->right); // find successor

            // If successor not directly the right child
            if (y->parent != z) {
                transplant(y, y->right);
                y->right = z->right;
                y->right->parent = y;
            }

            // Replace z with its successor
            transplant(z, y);
            y->left = z->left;
            y->left->parent = y;
        }

        delete z; // free memory of deleted node
    }

    // ===================================================
    // Traversal methods (call the helpers)
    // ===================================================
    void printInorder()  { inorder(root); }
    void printPreorder() { preorder(root); }
    void printPostorder(){ postorder(root); }
};

// ===================================================
// MAIN FUNCTION
// Reads commands from standard input (cin).
// Each line is a command:
//   iN → insert N
//   dN → delete N
//   oin → print inorder
//   opre → print preorder
//   opost → print postorder
//   e → exit program
// ===================================================
int main() {
    BST tree;
    string cmd;

    while (cin >> cmd) {
        // Exit the program
        if (cmd[0] == 'e') {
            break;
        }
        // Insert a key
        else if (cmd[0] == 'i') {
            int key = stoi(cmd.substr(1)); // get number after 'i'
            tree.insert(key);
        }
        // Delete a key
        else if (cmd[0] == 'd') {
            int key = stoi(cmd.substr(1)); // get number after 'd'
            tree.deleteKey(key);
        }
        // Print inorder traversal
        else if (cmd == "oin") {
            tree.printInorder();
        }
        // Print preorder traversal
        else if (cmd == "opre") {
            tree.printPreorder();
        }
        // Print postorder traversal
        else if (cmd == "opost") {
            tree.printPostorder();
        }
    }

    return 0;
}


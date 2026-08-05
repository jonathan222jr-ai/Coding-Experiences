#include <iostream>
#include <string>
using namespace std;
struct Node {
    int key;
    Node* left;
    Node* right;
    Node* parent;

    
    Node(int k) : key(k), left(nullptr), right(nullptr), parent(nullptr) {}
};


class BST {
private:
    Node* root;

    void inorder(Node* x) {
        if (x != nullptr) {
            inorder(x->left);
            cout << x->key << endl;
            inorder(x->right);
        }
    }

    
    void preorder(Node* x) {
        if (x != nullptr) {
            cout << x->key << endl;
            preorder(x->left);
            preorder(x->right);
        }
    }

    void postorder(Node* x) {
        if (x != nullptr) {
            postorder(x->left);
            postorder(x->right);
            cout << x->key << endl;
        }
    }

    
    Node* search(Node* x, int key) {
        if (x == nullptr || x->key == key)
            return x;
        if (key < x->key)
            return search(x->left, key);
        else
            return search(x->right, key);
    }

    
    Node* treeMinimum(Node* x) {
        while (x->left != nullptr)
            x = x->left;
        return x;
    }

   
    void transplant(Node* u, Node* v) {
        if (u->parent == nullptr)
            root = v;
        else if (u == u->parent->left)
            u->parent->left = v;
        else
            u->parent->right = v;

        if (v != nullptr)
            v->parent = u->parent;
    }

public:
    
    BST() : root(nullptr) {}

    
    void insert(int key) {
        Node* z = new Node(key);
        Node* y = nullptr;
        Node* x = root;

       
        while (x != nullptr) {
            y = x;
            if (z->key < x->key)
                x = x->left;
            else
                x = x->right;
        }

        
        z->parent = y;

        
        if (y == nullptr)
            root = z;
        else if (z->key < y->key)
            y->left = z;
        else
            y->right = z;
    }

    
    void deleteKey(int key) {
        Node* z = search(root, key);
        if (z == nullptr)
            return;

        
        if (z->left == nullptr)
            transplant(z, z->right);

        
        else if (z->right == nullptr)
            transplant(z, z->left);

        
        else {
            Node* y = treeMinimum(z->right);

           
            if (y->parent != z) {
                transplant(y, y->right);
                y->right = z->right;
                y->right->parent = y;
            }

            
            transplant(z, y);
            y->left = z->left;
            y->left->parent = y;
        }

        delete z;
    }

   
    void printInorder()  { inorder(root); }
    void printPreorder() { preorder(root); }
    void printPostorder(){ postorder(root); }
};


int main() {
    BST tree;
    string cmd;

    while (cin >> cmd) {
        
        if (cmd[0] == 'e') {
            break;
        }
        // Insert a key
        else if (cmd[0] == 'i') {
            int key = stoi(cmd.substr(1));
            tree.insert(key);
        }
        // Delete a key
        else if (cmd[0] == 'd') {
            int key = stoi(cmd.substr(1));
            tree.deleteKey(key);
        }
        
        else if (cmd == "oin") {
            tree.printInorder();
        }
        
        else if (cmd == "opre") {
            tree.printPreorder();
        }
       
        else if (cmd == "opost") {
            tree.printPostorder();
        }
    }

    return 0;
}


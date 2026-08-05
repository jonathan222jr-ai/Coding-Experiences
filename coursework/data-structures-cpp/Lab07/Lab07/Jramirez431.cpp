#include <iostream>
#include <vector>
#include <list>
using namespace std;


int main() {
    int m;
    cin >> m;
    vector<list<int>> hashTable(m);

    char command;
    while (cin >> command) {
        if (command == 'e') {
            break;
        }
        else if (command == 'i') {
            int key;
            cin >> key;
            int index = key % m;
            
            hashTable[index].push_front(key);
        }
        else if (command == 's') {
            int key;
            cin >> key;
            int index = key % m;
            int pos = 0;
            bool found = false;
            for (int val : hashTable[index]) {
                if (val == key) {
                    cout << key << ":FOUND_AT" << index << "," << pos << ";" << endl;
                    found = true;
                    break;
                }
                pos++;
            }
            if (!found) {
                cout << key << ":NOT_FOUND;" << endl;
            }
        }
        else if (command == 'd') {
            int key;
            cin >> key;
            int index = key % m;
            bool deleted = false;
            for (auto it = hashTable[index].begin(); it != hashTable[index].end(); ++it) {
                if (*it == key) {
                    hashTable[index].erase(it);
                    cout << key << ":DELETED;" << endl;
                    deleted = true;
                    break;
                }
            }
            if (!deleted) {
                cout << key << ":DELETE_FAILED;" << endl;
            }
        }
        else if (command == 'o') {
            for (int i = 0; i < m; i++) {
                cout << i << ":";
                for (int val : hashTable[i]) {
                    cout << val << "->";
                }
                cout << ";" << endl;
            }
        }
    }

    return 0;
}


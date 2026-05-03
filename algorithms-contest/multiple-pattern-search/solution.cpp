#include <algorithm>
#include <vector>
#include <iostream>
#include <string>
#include <queue>
#include <limits>

const int SIZE = 128;

struct Node
{
    std::vector<int> next;
    std::vector<int> go;
    int suf;
    bool term;
    bool good;

    Node() : next(SIZE, -1), go(SIZE, -1), suf(0), term(false), good(false) {}
};

std::vector<Node> T(1);

void add(const std::string &s)
{
    int v = 0;
    for (char ch : s)
    {
        int c = static_cast<unsigned char>(ch);
        if (T[v].next[c] == -1)
        {
            T[v].next[c] = static_cast<int>(T.size());
            T.push_back(Node());
        }
        v = T[v].next[c];
    }
    T[v].term = true;
}

void karas()
{
    std::queue<int> q;
    T[0].suf = 0;
    for (int c = 0; c < SIZE; ++c)
    {
        if (T[0].next[c] != -1)
        {
            int u = T[0].next[c];
            T[u].suf = 0;
            T[0].go[c] = u;
            q.push(u);
        }
        else
        {
            T[0].go[c] = 0;
        }
    }
    T[0].good = T[0].term;

    while (!q.empty())
    {
        int v = q.front();
        q.pop();

        T[v].good = T[v].term || T[T[v].suf].good;

        for (int c = 0; c < SIZE; ++c)
        {
            if (T[v].next[c] != -1)
            {
                int u = T[v].next[c];
                T[u].suf = T[T[v].suf].go[c];
                T[v].go[c] = u;
                q.push(u);
            }
            else
            {
                T[v].go[c] = T[T[v].suf].go[c];
            }
        }
    }
}

bool find(std::string &s)
{
    int v = 0;
    for (char ch : s)
    {
        int c = static_cast<int>(ch);
        v = T[v].go[c];
        if (T[v].good)
        {
            return true;
        }
    }
    return false;
}

int main()
{
    std::cin.tie(nullptr);
    std::ios::sync_with_stdio(false);
    int n;
    std::cin >> n;
    std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
    for (int i = 0; i < n; ++i)
    {
        std::string tmp;
        std::getline(std::cin, tmp);
        add(tmp);
    }
    karas();

    std::string s;
    while (std::getline(std::cin, s))
    {
        if (find(s))
        {
            std::cout << s << "\n";
        }
    }
}
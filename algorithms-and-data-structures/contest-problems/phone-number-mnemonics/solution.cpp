#include <iostream>
#include <vector>
#include <algorithm>
#include <string>
#include <cctype>

struct Node
{
    std::vector<int> next;
    std::vector<int> ids;

    Node() : next(10, -1) {}
};

std::vector<Node> bor(1);

char getn(char c)
{
    if (c == 'a' || c == 'b' || c == 'c')
    {
        return '2';
    }
    if (c == 'd' || c == 'e' || c == 'f')
    {
        return '3';
    }
    if (c == 'g' || c == 'h')
    {
        return '4';
    }
    if (c == 'i' || c == 'j')
    {
        return '1';
    }
    if (c == 'k' || c == 'l')
    {
        return '5';
    }
    if (c == 'm' || c == 'n')
    {
        return '6';
    }
    if (c == 'o' || c == 'q' || c == 'z')
    {
        return '0';
    }
    if (c == 'p' || c == 'r' || c == 's')
    {
        return '7';
    }
    if (c == 't' || c == 'u' || c == 'v')
    {
        return '8';
    }
    if (c == 'w' || c == 'x' || c == 'y')
    {
        return '9';
    }
}

std::string encode(std::string &input)
{
    std::string res = "";
    for (char c : input)
    {
        res += getn(c);
    }
    return res;
}

void add(std::string &s, int id)
{
    std::string code = encode(s);
    int v = 0;
    for (char c : code)
    {
        int d = c - '0';
        if (bor[v].next[d] == -1)
        {
            bor[v].next[d] = bor.size();
            Node tmp;
            bor.push_back(tmp);
        }
        v = bor[v].next[d];
    }
    bor[v].ids.push_back(id);
}

int main()
{
    std::string num;
    int m;
    while (true)
    {
        bor.clear();
        bor.push_back(Node());
        std::cin >> num;
        if (num == "-1")
        {
            break;
        }
        std::cin >> m;
        std::vector<std::string> a(m);
        for (int i = 0; i < m; ++i)
        {
            std::cin >> a[i];
            add(a[i], i);
        }

        int n = num.size();
        std::vector<int> dp(n + 1, 1e9);
        dp[n] = 0;
        std::vector<int> picked(n, -1), nxt(n, -1);

        for (int i = n - 1; i >= 0; --i)
        {
            int v = 0;
            for (int j = i; j < n; ++j)
            {
                int d = num[j] - '0';
                if (bor[v].next[d] == -1)
                {
                    break;
                }
                v = bor[v].next[d];
                if (!bor[v].ids.empty())
                {
                    for (int id : bor[v].ids)
                    {
                        if (dp[j + 1] + 1 < dp[i])
                        {
                            dp[i] = dp[j + 1] + 1;
                            picked[i] = id;
                            nxt[i] = j + 1;
                        }
                    }
                }
            }
        }
        if (dp[0] == 1e9)
        {
            std::cout << "No solution.\n";
            continue;
        }
        int pos = 0;
        bool flag = true;
        while (pos < n)
        {
            if (!flag)
            {
                std::cout << " ";
            }
            flag = false;
            std::cout << a[picked[pos]];
            pos = nxt[pos];
        }
        std::cout << "\n";
    }
}
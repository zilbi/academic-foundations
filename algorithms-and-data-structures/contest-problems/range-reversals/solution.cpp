#include <iostream>
#include <vector>
#include <algorithm>
#include <cmath>

struct block
{
    std::vector<int> a;
    long long sum;
    bool rev = false;
};

int n, m, k;

std::vector<block> blocks;

void push(block &b)
{
    if (!b.rev)
    {
        return;
    }
    std::reverse(b.a.begin(), b.a.end());
    b.rev = false;
}

void rebuild_s(block &b)
{
    long long s = 0;
    for (int x : b.a)
    {
        s += x;
    }
    b.sum = s;
}

int size(block &b)
{
    return b.a.size();
}

void build(std::vector<int> &ar)
{
    blocks.clear();
    for (int i = 0; i < ar.size(); i += k)
    {
        block b;
        int r = std::min(i + k, static_cast<int>(ar.size()));
        b.a.assign(ar.begin() + i, ar.begin() + r);
        rebuild_s(b);
        blocks.push_back(std::move(b));
    }
}

void rebuild_a()
{
    std::vector<int> ar;
    ar.reserve(n);
    for (auto &b : blocks)
    {
        push(b);
        for (int x : b.a)
        {
            ar.push_back(x);
        }
    }
    build(ar);
}

void split(int p)
{
    if (p <= 0 || p >= n)
    {
        return;
    }

    int cur = 0;
    for (int i = 0; i < blocks.size(); ++i)
    {
        int len = size(blocks[i]);
        if (cur + len < p)
        {
            cur += len;
            continue;
        }
        if (p == cur || p == cur + len)
        {
            return;
        }

        push(blocks[i]);

        int cut = p - cur;
        block l, r;

        l.a.assign(blocks[i].a.begin(), blocks[i].a.begin() + cut);
        r.a.assign(blocks[i].a.begin() + cut, blocks[i].a.end());

        rebuild_s(l);
        rebuild_s(r);
        blocks.insert(blocks.begin() + i + 1, std::move(r));
        blocks[i] = std::move(l);
        return;
    }
}

int find(int p)
{
    int cur = 0;
    for (int i = 0; i < blocks.size(); ++i)
    {
        int len = size(blocks[i]);
        if (cur <= p and p < cur + len)
        {
            return i;
        }
        cur += len;
    }
    return -1;
}

void reverse(int l, int r)
{
    split(l);
    split(r + 1);
    int bl = find(l);
    int br = find(r);

    std::reverse(blocks.begin() + bl, blocks.begin() + br + 1);
    for (int i = bl; i <= br; ++i)
    {
        blocks[i].rev ^= 1;
    }

    if (blocks.size() > k * 4)
    {
        rebuild_a();
    }
}

long long get_sum(int l, int r)
{
    split(l);
    split(r + 1);
    int bl = find(l);
    int br = find(r);

    long long ans = 0;
    for (int i = bl; i <= br; ++i)
    {
        ans += blocks[i].sum;
    }
    return ans;
}

int main()
{
    std::cin.tie(nullptr);
    std::ios::sync_with_stdio(false);

    std::cin >> n >> m;

    std::vector<int> a(n);
    for (int i = 0; i < n; ++i)
    {
        std::cin >> a[i];
    }

    k = std::max(static_cast<int>(std::sqrt(n)), 1);
    build(a);

    for (int i = 0; i < m; ++i)
    {
        int q, l, r;
        std::cin >> q >> l >> r;
        --l;
        --r;

        if (q == 0)
        {
            std::cout << get_sum(l, r) << "\n";
        }
        else
        {
            reverse(l, r);
        }
    }
}

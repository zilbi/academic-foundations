#include <iostream>
#include <vector>
#include <functional>
#include <random>
#include <chrono>

static std::mt19937 rng(
    (uint32_t)std::chrono::steady_clock::now().time_since_epoch().count());
static int rnd() { return (int)rng(); }

struct Node
{
    int val, prio;
    Node *l;
    Node *r;
    int size = 1;
    int mn;

    Node(int v, int prio_) : val(v), prio(prio_), l(nullptr), r(nullptr), mn(v) {};

    void update()
    {

        size = 1 + (l ? l->size : 0) + (r ? r->size : 0);
        mn = val;
        if (l and l->mn < mn)
        {
            mn = l->mn;
        }
        if (r and r->mn < mn)
        {
            mn = r->mn;
        }
    }

    static std::pair<Node *, Node *> split(Node *v, int k)
    {
        if (v == nullptr)
        {
            return {nullptr, nullptr};
        }
        int lsz = (v->l ? v->l->size : 0);
        if (lsz >= k)
        {
            auto [A, B] = split(v->l, k);
            v->l = B;
            v->update();
            return {A, v};
        }
        else
        {
            auto [A, B] = split(v->r, k - lsz - 1);
            v->r = A;
            v->update();
            return {v, B};
        }
    }

    static Node *merge(Node *A, Node *B)
    {
        if (A == nullptr)
        {
            return B;
        }
        if (B == nullptr)
        {
            return A;
        }
        if (A->prio > B->prio)
        {
            A->r = merge(A->r, B);
            A->update();
            return A;
        }
        else
        {
            B->l = merge(A, B->l);
            B->update();
            return B;
        }
    }
};

void add(Node *&root, int i, int v)
{
    auto [A, B] = Node::split(root, i);
    Node *node = new Node(v, rnd());
    root = Node::merge(A, Node::merge(node, B));
}

void modprint(Node *v, std::vector<int> &res)
{
    if (v == nullptr)
    {
        return;
    }
    modprint(v->l, res);
    res.push_back(v->val);
    modprint(v->r, res);
}

int first(Node *t)
{
    int left_mn = (t->l ? t->l->mn : 1e9);
    if (t->l != nullptr and left_mn == 0)
    {
        return first(t->l);
    }
    if (t->val == 0)
    {
        return (t->l ? t->l->size : 0) + 1;
    }
    return (t->l ? t->l->size : 0) + 1 + first(t->r);
}

void ins(Node *&root, int lpos, int k)
{
    auto [A, B] = Node::split(root, lpos - 1);
    int t = first(B);
    auto [M, C] = Node::split(B, t);
    auto [M1, last] = Node::split(M, t - 1);
    Node *nk = new Node(k, rnd());
    Node *NM = Node::merge(nk, M1);
    root = Node::merge(A, Node::merge(NM, C));
}

int main()
{
    int n, m;
    std::cin >> n >> m;
    std::vector<int> a(n);
    for (int i = 0; i < n; ++i)
    {
        std::cin >> a[i];
    }

    Node *root = nullptr;
    int w = m + n;
    for (int i = 0; i < w; ++i)
    {
        add(root, i, 0);
    }

    for (int i = 0; i < n; ++i)
    {
        ins(root, a[i], i + 1);
    }

    std::vector<int> res;
    res.reserve(w);
    modprint(root, res);
    w = 0;

    for (int i = res.size() - 1; i >= 0; --i)
    {
        if (res[i] != 0)
        {
            w = i + 1;
            break;
        }
    }
    std::cout << w << "\n";
    for (int i = 0; i < w; ++i)
    {
        std::cout << res[i] << " ";
    }
}
#include <iostream>
#include <vector>
#include <queue>
#include <utility>
#include <climits>

long long inf = LLONG_MAX / 4;
std::pair<std::vector<long long>,std::vector<bool>> Ford(std::vector<std::vector<std::pair<int,long long>>>& gr, int s){
    std::vector<long long> dist(gr.size(), inf);
    std::vector<bool> inq(gr.size(), false);
    dist[s] = 0;
    std::queue<int> q;
    q.push(s);
    inq[s] = true;
    std::vector<int> cnt(gr.size(), 0);
    std::vector<bool> bad(gr.size(), false);
    std::queue<int> badq;
    while(!q.empty()){
        int v = q.front();
        q.pop();
        inq[v] = false;
        if(bad[v]){
            continue;
        }
        if(dist[v]==inf){
            continue;
        }
        for(std::pair<int,long long> p: gr[v]){
            int u=p.first;
            long long w=p.second;
            long long nd;
            if(w>0 and dist[v]>LLONG_MAX-w){
                nd = LLONG_MAX;
            }
            else if (w<0 and dist[v]<LLONG_MIN-w){
                nd = LLONG_MIN;
            }
            else nd = dist[v] + w;
            if(nd<dist[u]){
                dist[u]=nd;
                if(bad[u]){
                    continue;
                }
                cnt[u]++; 
                if(cnt[u]>=gr.size() and !bad[u]) {
                    bad[u] = true;
                    badq.push(u);
                }
                if(!inq[u]){
                    q.push(u);
                    inq[u]=true;
                }
            }
        }
    }
    while (!badq.empty()) {
        int v = badq.front(); 
        badq.pop();
        for(std::pair<int,long long> p: gr[v]){
            int u=p.first;
            long long w=p.second;
            if(!bad[u]){
                bad[u] = true;
                badq.push(u);
            }
        }
    }
    return {dist,bad};
}

int main(){
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n,m, s;
    std::cin>>n>>m>>s;
    s--;
    std::vector<std::vector<std::pair<int,long long>>> gr(n);
    for(int i=0; i<m; ++i){
        int b,e;
        long long w;
        std::cin>>b>>e>>w;
        b--,e--;
        gr[b].push_back({e, w});
    }
    auto[res, bad] = Ford(gr, s);
    for(int i=0; i<n; ++i){
        if(res[i]==inf){
            std::cout<<"*"<<"\n";
        }
        else if(bad[i]){
            std::cout<<"-"<<"\n";
        }
        else{
            std::cout<<res[i]<<"\n";
        }
    }
}
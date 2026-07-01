# Mathematical Foundations of the Base Graph Swarm Harness

This document describes the core equations used in `base_graph` to measure global properties, compute emergence, run diffusion, and verify homeostatic balance.

---

## 1. Spectral Graph Theory Primitives

### Normalized Laplacian Matrix
Given an adjacency matrix $A \in \mathbb{R}^{N \times N}$ and a degree diagonal matrix $D \in \mathbb{R}^{N \times N}$ where $D_{ii} = \sum_j A_{ij}$, the normalized Laplacian $L$ is defined as:

$$L = I - D^{-1/2} A D^{-1/2}$$

Or, entry-wise:

$$L_{ij} = \begin{cases}
1 & \text{if } i = j \text{ and } D_{ii} \neq 0 \\
-\frac{A_{ij}}{\sqrt{D_{ii} D_{jj}}} & \text{if } i \neq j \text{ and } A_{ij} \neq 0 \\
0 & \text{otherwise}
\end{cases}$$

### Spectral Gap (Algebraic Connectivity)
The eigenvalues of the normalized Laplacian are ordered as:

$$0 = \lambda_1 \le \lambda_2 \le \dots \le \lambda_N \le 2$$

The **Spectral Gap** is the second smallest eigenvalue:

$$\text{Spectral Gap} = \lambda_2$$

- A larger $\lambda_2$ indicates a more cohesive, faster-synchronizing, and well-connected graph.
- $\lambda_2 > 0$ if and only if the graph is connected.

---

## 2. Information Theoretic Entropy

We evaluate the structural and state-level uncertainty using Shannon Entropy.

### Graph Diffusion Entropy
Given a state vector $x \in \mathbb{R}^N$ representing resource distribution or opinion dynamics across nodes:

1. Normalize state values to form a probability distribution:
   $$p_i = \frac{|x_i|}{\sum_{j=1}^N |x_j|}$$
2. Compute the Shannon Entropy:
   $$H(X) = - \sum_{i=1}^N p_i \log_2(p_i)$$
3. The normalized entropy $\overline{H}(X)$ is:
   $$\overline{H}(X) = \frac{H(X)}{\log_2(N)}$$

Low entropy indicates resource/opinion concentration (high order), while high entropy ($H \approx 1$) represents uniform distribution (high disorder).

---

## 3. Emergence Level ($E$)

Emergence measures the transition of a swarm from disorganized local units to ordered global coordination. We compute composite emergence level $E \in [0, 1]$ as:

$$E = \alpha \cdot \text{spectral\_gap} + \beta \cdot (1 - \overline{H}) + \gamma \cdot \chi_{\text{persistence}}$$

Where:
- $\alpha, \beta, \gamma \ge 0$ are tuning coefficients such that $\alpha + \beta + \gamma = 1$.
- $\text{spectral\_gap} = \min(1.0, \lambda_2)$ measures connectivity.
- $1 - \overline{H}$ measures coherence or organization (reduction of disorder).
- $\chi_{\text{persistence}}$ measures the temporal stability of clusters (inverse of variance of top cluster configurations).

---

## 4. Trophallaxis Resource Sharing

Trophallaxis is the exchange of resource/energy packets between neighboring nodes to maintain homeostasis.

### Node Resource Balance
For a node $i$ with resource pool $r_i$, the resource change $\Delta r_i$ at step $t$ is:

$$\Delta r_i^{(t)} = \sum_{j \in \mathcal{N}_i} T_{ji} - \sum_{k \in \mathcal{N}_i} T_{ik} - C_i$$

Where:
- $T_{ji} \ge 0$ is the resource transferred from node $j$ to node $i$.
- $C_i \ge 0$ is the internal metabolic consumption cost of node $i$.

### Transfer Function
A node $j$ transfers resources to a needy neighbor $i$ if its own level exceeds a safety threshold $\theta$:

$$T_{ji} = \min\left(R_{\text{max\_flow}}, \kappa \cdot \max(0, r_j - r_i) \cdot \mathbb{I}(r_j > \theta)\right)$$

Where:
- $\kappa \in [0, 1]$ is the sharing rate.
- $R_{\text{max\_flow}}$ is the physical limit of the trophallaxis channel.
- $\mathbb{I}$ is the indicator function.

---

## 5. Opinion Dynamics (DeGroot Model with Bounded Confidence)

For decentralized consensus formation:

$$x_i^{(t+1)} = \sum_{j \in \mathcal{N}_i \cup \{i\}} W_{ij} x_j^{(t)}$$

Under bounded confidence (Hegselmann-Krause model), the weights $W_{ij}$ adapt based on opinion distance:

$$W_{ij} = \begin{cases}
A_{ij} & \text{if } |x_i^{(t)} - x_j^{(t)}| < \epsilon \\
0 & \text{otherwise}
\end{cases}$$

Normalized such that $\sum_j W_{ij} = 1$.

---

## 6. Stigmergic Pheromone Decay

Edges acting as stigmergic media update their virtual pheromone intensity $S_{e}$ dynamically:

$$S_e^{(t+1)} = (1 - \delta) S_e^{(t)} + \sum_{n \in \text{depositors}} \Delta S_n$$

Where:
- $\delta \in [0, 1]$ is the evaporation/decay rate.
- $\Delta S_n$ is the intensity deposit left by agent/node $n$.

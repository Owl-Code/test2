import math
from typing import Any, List, Union

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore

try:
    import torch
except ImportError:
    torch = None  # type: ignore

def get_eigenvalues(matrix: Union[Any, List[List[float]]]) -> List[float]:
    """Computes eigenvalues of a symmetric matrix.
    
    Uses PyTorch (with optional GPU acceleration) or NumPy if available, 
    else falls back to a pure Python Jacobi eigenvalue algorithm.
    """
    if torch is not None:
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            if isinstance(matrix, list):
                t_mat = torch.tensor(matrix, dtype=torch.float64)
            elif np is not None and isinstance(matrix, np.ndarray):
                t_mat = torch.from_numpy(matrix)
            else:
                t_mat = torch.tensor(matrix, dtype=torch.float64)
                
            if t_mat.numel() == 0:
                return []
                
            t_mat = t_mat.to(device)
            eigenvals = torch.linalg.eigvalsh(t_mat)
            return [float(ev) for ev in eigenvals.cpu().numpy()]
        except Exception:
            # Fallback to NumPy or pure Python if PyTorch error occurs
            pass

    if np is not None:
        if isinstance(matrix, list):
            matrix = np.array(matrix, dtype=np.float64)
        if matrix.size == 0:
            return []
        try:
            # eigvalsh is optimized for real symmetric matrices (which normalized Laplacian is)
            eigenvals = np.linalg.eigvalsh(matrix)
            return [float(ev) for ev in eigenvals]
        except Exception:
            # Fallback to general solver if eigvalsh fails
            eigenvals = np.linalg.eigvals(matrix)
            return sorted([float(ev.real) for ev in eigenvals])
            
    # Pure Python Jacobi Eigenvalue Solver for symmetric matrices
    if not matrix or not isinstance(matrix, list) or len(matrix) == 0:
        return []
        
    n = len(matrix)
    if n == 1:
        return [float(matrix[0][0])]

    # Deep copy the matrix to avoid modifying graph structures
    A = [[float(val) for val in row] for row in matrix]
    
    max_iterations = 100
    for _ in range(max_iterations):
        # Find the largest off-diagonal element A[p][q]
        p = 0
        q = 1
        max_val = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                if abs(A[i][j]) > max_val:
                    max_val = abs(A[i][j])
                    p = i
                    q = j
                    
        # If the largest off-diagonal is negligible, matrix is diagonalized
        if max_val < 1e-9:
            break
            
        # Compute rotation angle theta
        diff = A[q][q] - A[p][p]
        if abs(A[p][q]) < 1e-12:
            continue
            
        if abs(diff) < 1e-12:
            theta = math.pi / 4.0
        else:
            # theta = 1/2 * arctan(2*A_pq / (A_qq - A_pp))
            theta = 0.5 * math.atan2(2.0 * A[p][q], diff)
            
        c = math.cos(theta)
        s = math.sin(theta)
        
        # Symmetrized rotation updates
        ap = A[p][p]
        aq = A[q][q]
        apq = A[p][q]
        
        A[p][p] = c * c * ap - 2.0 * c * s * apq + s * s * aq
        A[q][q] = s * s * ap + 2.0 * c * s * apq + c * c * aq
        A[p][q] = 0.0
        A[q][p] = 0.0
        
        for i in range(n):
            if i != p and i != q:
                aip = A[i][p]
                aiq = A[i][q]
                A[i][p] = c * aip - s * aiq
                A[p][i] = A[i][p]
                A[i][q] = s * aip + c * aiq
                A[q][i] = A[i][q]
                
    # Return sorted diagonal values
    eigenvals_list = [A[i][i] for i in range(n)]
    eigenvals_list.sort()
    return eigenvals_list

def compute_entropy(values: List[float]) -> float:
    """Computes Shannon Entropy of a list of numeric values."""
    n = len(values)
    if n <= 1:
        return 0.0
        
    total = sum(values)
    if total == 0:
        return 0.0
        
    entropy = 0.0
    for val in values:
        p = val / total
        if p > 0:
            entropy -= p * math.log2(p)
            
    return entropy

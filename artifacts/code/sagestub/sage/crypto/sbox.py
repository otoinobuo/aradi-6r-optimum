class _Table:
    def __init__(self, rows): self._rows = rows
    def rows(self): return self._rows
    def nrows(self): return len(self._rows)
    def ncols(self): return len(self._rows[0])
    def __getitem__(self, ij): i, j = ij; return self._rows[i][j]
class SBox:
    def __init__(self, values, **kw):
        self.values = list(values); self.n = (len(self.values) - 1).bit_length(); self.m = max(self.values).bit_length()
    def __len__(self): return len(self.values)
    def __getitem__(self, x): return self.values[x]
    def input_size(self): return self.n
    def output_size(self): return self.m
    def difference_distribution_table(self):
        N = len(self.values); rows = [[0] * (1 << self.m) for _ in range(N)]
        for a in range(N):
            for x in range(N): rows[a][self.values[x] ^ self.values[x ^ a]] += 1
        return _Table(rows)
    def linear_approximation_table(self, scale="absolute_bias"):
        N = len(self.values); rows = [[0] * (1 << self.m) for _ in range(N)]
        for a in range(N):
            for b in range(1 << self.m):
                s = 0
                for x in range(N):
                    s += 1 if (bin(a & x).count("1") + bin(b & self.values[x]).count("1")) % 2 == 0 else -1
                rows[a][b] = s // 2  # sage default: absolute_bias = (#eq - N/2) = s/2
        return _Table(rows)

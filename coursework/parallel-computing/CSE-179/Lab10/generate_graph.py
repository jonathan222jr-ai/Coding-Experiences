import random
import time

def generate_weighted_graph(num_vertices, edge_probability):
    seed = int(time.time())
    random.seed(seed)
    print(f"Using seed: {seed}")

    matrix = [[0] * num_vertices for _ in range(num_vertices)]

    for i in range(num_vertices):
        for j in range(i + 1, num_vertices):
            if random.randint(1, 100) <= edge_probability:
                weight = random.randint(1, 100)  # weights 1-100 (0 = no edge)
                matrix[i][j] = weight
                matrix[j][i] = weight  # undirected graph

    return matrix

def save_matrix(matrix, filename="adjacency_matrix.txt"):
    n = len(matrix)
    with open(filename, "w") as f:
        f.write(f"{n}\n")
        for row in matrix:
            f.write(" ".join(map(str, row)) + "\n")
    print(f"Graph saved to {filename}")

if __name__ == "__main__":
    n = 100
    prob = 50
    graph = generate_weighted_graph(n, prob)
    save_matrix(graph)

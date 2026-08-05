from bs4 import BeautifulSoup
import requests

def print_grid_from_doc(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    rows = soup.find_all("tr")

    points = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) == 3:
            try:
                x = int(cols[0].text.strip())
                char = cols[1].text.strip()
                y = int(cols[2].text.strip())
                points.append((x, char, y))
            except:
                continue

    max_x = max(p[0] for p in points)
    max_y = max(p[2] for p in points)

    grid = [[' ' for _ in range(max_x + 1)] for _ in range(max_y + 1)]

    for x, char, y in points:
        grid[y][x] = char

    for row in grid:
        print(''.join(row))
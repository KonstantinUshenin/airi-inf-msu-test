# Примеры решений

## База

### B1

```python
# ячейка 1
answer = 42

# ячейка 2
print(answer)
```

Если выполнить сначала вторую ячейку, будет `NameError: name 'answer' is not
defined`: переменная живёт не в тексте ноутбука, а в памяти **ядра**, и
появляется там только в момент выполнения ячейки. После `Kernel → Restart Kernel
and Run All Cells` память ядра очищается и ячейки выполняются сверху вниз —
печатается `42`.

Отсюда правило: перед тем как показывать ноутбук кому-то (или сдавать его),
всегда делайте Restart & Run All. Иначе легко сдать ноутбук, который у вас
«работает», а у проверяющего падает.

### B2

```python
x = 5
%pwd            # текущий рабочий каталог
%who            # список определённых переменных (покажет x)
!python --version
%timeit sum(range(10**6))
```

### B3

```python
import numpy as np

arr = np.array([1, 4, 9, 16, 25])
print("arr:", arr, "| shape:", arr.shape, "| dtype:", arr.dtype)

grid = np.linspace(0, 1, 5)      # [0.   0.25 0.5  0.75 1.  ]
print("grid:", grid, "| shape:", grid.shape, "| dtype:", grid.dtype)
```

### B4

```python
import numpy as np

a = np.arange(5)
print("a ** 2 :", a ** 2)          # [ 0  1  4  9 16]
print("sqrt   :", np.sqrt(a))
print("a + 10 :", a + 10)          # [10 11 12 13 14]

b = np.array([10, 20, 30, 40, 50])
print("a + b  :", a + b)           # поэлементно
```

### B5

```python
import numpy as np

x = np.arange(10)
print(x[2:5])          # [2 3 4]
print(x[-3:])          # [7 8 9]
print(x[x % 2 == 0])   # [0 2 4 6 8]
```

### B6

```python
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0, 2 * np.pi, 200)
plt.plot(x, np.sin(x))
plt.xlabel("x")
plt.ylabel("sin(x)")
plt.title("y = sin(x)")
plt.grid(True)
plt.savefig("sin.png", dpi=150)   # сохранить ДО show
plt.show()
```

## Среднее

### M1

```python
import numpy as np

N = 10**6
loop = sum(i * i for i in range(N))
vec = int((np.arange(N) ** 2).sum())
assert loop == vec == 333332833333500000

%timeit sum(i * i for i in range(N))     # чистый Python
%timeit (np.arange(N) ** 2).sum()        # NumPy — быстрее
```

### M2

```python
import numpy as np

rows = np.arange(3).reshape(-1, 1)   # столбец (3, 1)
cols = np.arange(4)                  # строка  (4,)
A = rows + cols                      # broadcasting → (3, 4)
print(A)                             # [[0 1 2 3] [1 2 3 4] [2 3 4 5]]
```

### M3

```python
import numpy as np

M = np.arange(6).reshape(2, 3)
print(M.sum(axis=0))   # [3 5 7]  — по столбцам
print(M.sum(axis=1))   # [ 3 12]  — по строкам
print(M.argmax())      # 5        — индекс максимума (в развёрнутом виде)
```

### M4

```python
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(-5, 5, 400)
fig, axes = plt.subplots(2, 2, figsize=(10, 8))

axes[0, 0].plot(x, x ** 2)
axes[0, 0].set_title("$y = x^2$")

axes[0, 1].plot(x, x ** 3 - 3 * x)
axes[0, 1].set_title("$y = x^3 - 3x$")

axes[1, 0].plot(x, np.sinc(x / np.pi))    # sinc(x/π) = sin(x)/x без деления на 0
axes[1, 0].set_title("$y = \\sin(x)/x$")

axes[1, 1].plot(x, np.log(1 + x ** 2))
axes[1, 1].set_title("$y = \\ln(1 + x^2)$")

for ax in axes.flat:
    ax.grid(True)

fig.tight_layout()
fig.savefig("subplots.png", dpi=150)
plt.show()
```

### M5

```python
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(0)
data = np.random.randn(10000)

plt.hist(data, bins=50, density=True, edgecolor="black", label="выборка")
x = np.linspace(-4, 4, 300)
plt.plot(x, (1 / np.sqrt(2 * np.pi)) * np.exp(-x ** 2 / 2), "r-", lw=2, label="N(0,1)")
plt.legend()
plt.title("density=True уравнивает масштабы")
plt.show()
```

### M6

```python
!python --version
!pip show numpy matplotlib | grep -E "Name|Version"
!pip install -q plotly            # доустановка недостающего пакета

from google.colab import drive
drive.mount("/content/drive")     # запросит доступ к диску

plt.savefig("/content/drive/MyDrive/sin_cos.png", dpi=150)
```

Файл, записанный в `/content` (рабочий каталог), лежит на диске **временной
виртуальной машины**: она выдаётся на сессию и уничтожается при отключении
вместе со всем содержимым, включая доустановленные пакеты. `/content/drive` —
это примонтированный Google Drive, то есть внешнее хранилище, поэтому там файл
переживает конец сессии.

## Сложное

### H1

```python
import numpy as np
import matplotlib.pyplot as plt

g = np.arange(-3, 3, 0.05)
X, Y = np.meshgrid(g, g)
Z = np.sin(X ** 2 + Y ** 2)
print("Z.shape:", Z.shape)

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

im = axes[0].imshow(Z, extent=[-3, 3, -3, 3], origin="lower", cmap="viridis")
axes[0].set_title("imshow")
fig.colorbar(im, ax=axes[0])

cf = axes[1].contourf(X, Y, Z, levels=20, cmap="viridis")
axes[1].set_title("contourf")
fig.colorbar(cf, ax=axes[1])

fig.tight_layout()
plt.show()
```

### H2

```python
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(0)
N = 10**6
pts = np.random.rand(N, 2)
inside = (pts[:, 0] ** 2 + pts[:, 1] ** 2) <= 1.0
pi_est = 4 * inside.mean()
print("pi ~", pi_est, "| error:", abs(pi_est - np.pi))   # error < 0.01

# сходимость: оценка по первым k точкам
k = np.arange(1, N + 1)
running = 4 * np.cumsum(inside) / k
plt.plot(k[::1000], running[::1000])
plt.axhline(np.pi, color="red", ls="--", label="π")
plt.xscale("log")
plt.xlabel("число точек")
plt.ylabel("оценка π")
plt.legend()
plt.title("Монте-Карло: сходимость к π")
plt.show()
```

### H3

```python
import numpy as np
import matplotlib.pyplot as plt

re = np.linspace(-2, 1, 800)
im = np.linspace(-1.5, 1.5, 800)
C = re[np.newaxis, :] + 1j * im[:, np.newaxis]

Z = np.zeros_like(C)
iters = np.zeros(C.shape, dtype=int)
alive = np.ones(C.shape, dtype=bool)

max_iter = 100
for i in range(max_iter):                 # цикл только по итерациям
    Z[alive] = Z[alive] ** 2 + C[alive]   # z = z^2 + c
    diverged = np.abs(Z) > 2
    iters[alive & diverged] = i
    alive &= ~diverged

plt.figure(figsize=(9, 7))
plt.imshow(iters, extent=[-2, 1, -1.5, 1.5], origin="lower", cmap="inferno")
plt.colorbar(label="итерация расходимости")
plt.title("Множество Мандельброта")
plt.show()
```

### H4

```python
import numpy as np
import matplotlib.pyplot as plt

fig = plt.figure(figsize=(15, 4))

# Лиссажу — декартовы координаты
ax1 = fig.add_subplot(1, 3, 1)
t = np.linspace(0, 2 * np.pi, 1000)
ax1.scatter(np.sin(3 * t), np.sin(4 * t), c=t, cmap="hsv", s=2)
ax1.set_title("Фигура Лиссажу")
ax1.set_aspect("equal")

# Спираль Архимеда — полярные координаты
ax2 = fig.add_subplot(1, 3, 2, projection="polar")
theta = np.linspace(0, 6 * np.pi, 500)
ax2.plot(theta, 0 + 0.5 * theta)          # r = a + b*theta
ax2.set_title("Спираль Архимеда")

# Кардиоида — полярные координаты
ax3 = fig.add_subplot(1, 3, 3, projection="polar")
theta = np.linspace(0, 2 * np.pi, 500)     # полный оборот
ax3.plot(theta, 1 + np.cos(theta))         # r = 1 + cos(theta)
ax3.set_title("Кардиоида")

fig.tight_layout()
plt.show()
```

### H5

```python
import numpy as np

np.random.seed(0)
X = np.random.randn(1000, 4) * 5 + 2       # произвольные среднее и разброс
Xz = (X - X.mean(axis=0)) / X.std(axis=0)  # broadcasting по столбцам, без циклов

print("mean:", np.round(Xz.mean(axis=0), 6))   # ~ [0 0 0 0]
print("std :", np.round(Xz.std(axis=0), 6))    # ~ [1 1 1 1]
```

### H6

```python
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

x = np.linspace(0, 4 * np.pi, 300)
fig, ax = plt.subplots(figsize=(8, 4))
line, = ax.plot(x, np.sin(x))
ax.set_ylim(-1.5, 1.5)
ax.set_title("Бегущая волна: y = sin(x - t)")
ax.grid(True, alpha=0.3)

def update(frame):
    t = frame * 0.2
    line.set_ydata(np.sin(x - t))     # обновляем данные линии на каждом кадре
    return (line,)

anim = FuncAnimation(fig, update, frames=60, interval=50, blit=True)
anim.save("wave.gif", writer=PillowWriter(fps=20))
plt.close(fig)
```

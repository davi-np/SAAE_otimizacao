# Método 1: SLSQP (Programação Quadrática Sequencial)

Trecho em questão: [src/main.py:161-188](../src/main.py#L161-L188)

SLSQP (*Sequential Least Squares Programming*, Kraft, 1988) é a implementação de **Programação Quadrática Sequencial (SQP)** disponível no SciPy. No código ele é usado como "caixa-preta": o trabalho está em entregar o problema no formato certo, com gradiente e Jacobianas exatos.

---

## 1. O problema que ele recebe

Depois da eliminação dos volumes ([adaptacao.md](adaptacao.md), seção 4), o problema fica só nas variáveis $u = (x, z) \in \mathbb{R}^{384}$:

$$
\min_{u} \; f(u)
\quad \text{s.a.} \quad
h_{\min} \le b + M u \le h_{\max},
\qquad 0 \le u \le 1 .
$$

São 384 restrições lineares de volume (192 de mínimo e 192 de máximo) e 768 limites de caixa.

---

## 2. Como o método funciona

A cada iteração $k$, no ponto $u_k$, o SQP monta e resolve um **subproblema quadrático (QP)** para obter a direção $d$:

$$
\min_{d} \; \nabla f(u_k)^\top d + \tfrac12\, d^\top B_k\, d
\quad \text{s.a.} \quad
c(u_k) + \nabla c(u_k)^\top d \ge 0,
\qquad 0 \le u_k + d \le 1 .
$$

- **$B_k$** é uma aproximação da Hessiana do Lagrangeano, atualizada por **BFGS** a cada passo. No SLSQP ela é guardada fatorada ($B = L D L^\top$), e o QP é resolvido como um **problema de mínimos quadrados** com restrições. Daí o nome.
- **As restrições são linearizadas.** Aqui elas já são lineares, então a linearização é **exata**: o QP enxerga as restrições verdadeiras.
- **Busca linear.** O passo $u_{k+1} = u_k + \alpha d$ usa uma função de mérito $\ell_1$ (objetivo + penalidade das violações). Ela evita que o método dê passos que melhorem $f$ mas piorem muito a viabilidade.
- **Multiplicadores.** O QP devolve os multiplicadores $\lambda$, que convergem para os do ponto KKT ([kkt.md](kkt.md)).

**Particularidade deste problema:** $f$ é **quadrática** (termos lineares, $\beta x^2$ e $\rho\,\Delta x^2$), e as restrições são lineares. O problema inteiro já é um QP convexo. Se $B_k$ fosse a Hessiana exata, uma única iteração bastaria. As 21 iterações observadas vêm basicamente do BFGS aprendendo a Hessiana a partir de $B_0 = I$ e da identificação do conjunto ativo.

---

## 3. O código, linha a linha

### 3.1 Ingredientes comuns aos dois métodos

| O quê | Onde | Observação |
|---|---|---|
| $f(u)$ e $\nabla f(u)$ exatos | [main.py:118-144](../src/main.py#L118-L144) | Uma função devolve os dois |
| Volumes $I = b + Mu$ | [main.py:146-148](../src/main.py#L146-L148) | Um produto matriz-vetor |
| Caixa $[0,1]^{384}$ | [main.py:150](../src/main.py#L150) | `bounds` |
| Ponto inicial $u_0 = 0{,}35$ | [main.py:151](../src/main.py#L151) | Mesmo chute para os dois métodos |
| Teste do gradiente | [main.py:154-159](../src/main.py#L154-L159) | `check_grad` compara com diferenças finitas (erro ≈ $1{,}5\cdot10^{-3}$ numa norma de ordem $10^4$, ou seja, o gradiente está certo) |

### 3.2 Restrições ([main.py:165-176](../src/main.py#L165-L176))

```python
{"type": "ineq",
 "fun": lambda u: (volume_reservatorios(u) - h_min_vec) / h_max_vec,   # I >= h_min
 "jac": lambda u: M_bal_scaled},
{"type": "ineq",
 "fun": lambda u: (h_max_vec - volume_reservatorios(u)) / h_max_vec,   # I <= h_max
 "jac": lambda u: -M_bal_scaled},
```

- No SciPy, `"ineq"` significa **`fun(u) >= 0`**. Por isso o limite superior é escrito como $h_{\max} - I \ge 0$.
- Cada bloco devolve um **vetor** de 192 restrições, e não 192 dicionários separados.
- Como as restrições são lineares, a **Jacobiana é constante**: a lambda devolve sempre a mesma matriz `M_bal_scaled` (±). Isso evita que o SLSQP estime a Jacobiana por diferenças finitas, o que custaria 384 avaliações extras por iteração.
- A divisão por `h_max_vec` é o escalonamento explicado em [escalonamento.md](escalonamento.md).

### 3.3 Chamada ([main.py:178-186](../src/main.py#L178-L186))

```python
res_slsqp = minimize(
    lambda u: objetivo_e_gradiente(u)[0] / f_scale,
    u0,
    jac=lambda u: objetivo_e_gradiente(u)[1] / f_scale,
    method="SLSQP",
    bounds=bounds,
    constraints=constraints_slsqp,
    options={"ftol": 1e-8, "maxiter": 600, "disp": False},
)
```

- O objetivo e o gradiente são divididos por `f_scale = 1000` ([escalonamento.md](escalonamento.md)).
- **`ftol = 1e-8`**: o método para quando a variação de $f$ (escalado) entre iterações fica abaixo de $10^{-8}$ e as restrições estão satisfeitas. Como $f/1000 \approx 27{,}5$, isso equivale a uma precisão de cerca de $10^{-5}$ no custo real.
- **Os limites de caixa vão em `bounds`, e não como restrições.** O SLSQP os trata separadamente, o que é mais barato.
- A linha [188](../src/main.py#L188) desfaz a escala: `f_slsqp = res_slsqp.fun * f_scale`.

---

## 4. O que acontece na execução

Execução de verificação (SciPy 1.18):

| Medida | Valor |
|---|---|
| Status | `Optimization terminated successfully` |
| Iterações | 21 (21 avaliações de $f$ e de $\nabla f$) |
| Custo final | 27.529,21 |
| Violação máxima de volume | ~$10^{-9}$ m³ (o relatório, em outra máquina, reporta $2{,}7\cdot10^{-11}$) |
| Tempo | ~1,8–2,3 s (varia entre execuções) |

**Estrutura da solução:**

- **134** restrições de volume mínimo e **2** de volume máximo estão ativas ($I = h$). Os reservatórios passam a maior parte do tempo no mínimo: estocar água cedo é caro por causa da perda de 10% por hora.
- **196** das 384 variáveis estão em 0, e só **2** estão em 1.

O número de restrições ativas bate com o número de multiplicadores positivos do Lagrangeano Aumentado (134 e 2). Isso é uma verificação cruzada da complementaridade ([kkt.md](kkt.md)).

---

## 5. Convergência: o que a teoria garante

Para SQP com BFGS e busca linear numa função de mérito, os resultados clássicos (Nocedal & Wright, cap. 18) são:

- **Convergência global:** a partir de qualquer ponto inicial, o método converge para um ponto KKT, se os QPs forem viáveis e a matriz $B_k$ continuar positiva definida e limitada.
- **Convergência local superlinear:** vale perto de um ponto KKT que satisfaça três hipóteses:
  1. LICQ: os gradientes das restrições ativas são linearmente independentes;
  2. complementaridade estrita;
  3. condições suficientes de 2ª ordem.

Neste problema, as condições de 2ª ordem valem automaticamente, porque $f$ é estritamente convexa. Como as restrições são lineares, os QPs são viáveis sempre que o problema original é viável. **LICQ e complementaridade estrita não foram verificadas.** Como o ótimo é único, porém, qualquer ponto KKT encontrado é **o** ótimo global.

---

## 6. Vantagens e limitações aqui

| Vantagens | Limitações |
|---|---|
| Lida diretamente com as restrições: não precisa de penalidade nem de ajuste de parâmetros | O QP é resolvido com **álgebra densa**: com 384 variáveis e 384 restrições, cada iteração custa $O(n^3)$. Por isso o método é mais lento que o Lagrangeano Aumentado nesta instância |
| Muito preciso na viabilidade (~$10^{-9}$ m³) | Não escala bem para horizontes ou redes muito maiores |
| Poucas iterações | É uma caixa-preta (código Fortran): pouco controle sobre o que acontece dentro |

**Detalhe de eficiência:** `objetivo_e_gradiente` é chamada duas vezes por ponto, uma pela lambda do objetivo e outra pela lambda do `jac`. Passar `jac=True` com uma função que devolve `(f, grad)` eliminaria a repetição. Neste tamanho de problema, o efeito é pequeno.

Comparação com o outro método: [lagrangeano-aumentado.md](lagrangeano-aumentado.md).

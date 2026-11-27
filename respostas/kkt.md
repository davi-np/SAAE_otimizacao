# O que é um ponto KKT?

KKT são as **condições de Karush-Kuhn-Tucker**: as condições que um ponto precisa satisfazer para ser candidato a ótimo num problema **com restrições**.

Elas generalizam duas ideias conhecidas:

- **Sem restrições:** o ótimo exige $\nabla f = 0$.
- **Com restrições de igualdade:** aparecem os multiplicadores de Lagrange.

O KKT estende isso para restrições de **desigualdade**.

---

## 1. As quatro condições

Para o problema

$$\min_u f(u) \quad \text{s.a.} \quad g_i(u) \le 0, \quad i = 1, \dots, m,$$

um ponto $u^*$ é **KKT** se existem números $\lambda_1, \dots, \lambda_m$ (os **multiplicadores**) tais que:

| Condição | Fórmula | Em palavras |
|---|---|---|
| Viabilidade | $g_i(u^*) \le 0$ | o ponto respeita as restrições |
| Estacionariedade | $\nabla f(u^*) + \sum_i \lambda_i \nabla g_i(u^*) = 0$ | as forças se equilibram |
| Sinal | $\lambda_i \ge 0$ | as paredes só empurram para dentro |
| Complementaridade | $\lambda_i \, g_i(u^*) = 0$ | só a parede encostada empurra |

---

## 2. Intuição física

Imagine uma bola rolando morro abaixo sobre o gráfico de $f$, dentro de uma região cercada por **paredes** (as restrições).

- **Parou no meio da região:** nenhuma parede atua ($\lambda = 0$) e o chão é plano ali ($\nabla f = 0$).
- **Parou encostada numa parede:** a força que puxa morro abaixo ($-\nabla f$) é equilibrada pela parede. O número $\lambda_i$ mede **com que intensidade** a parede $i$ empurra.

A **complementaridade** diz que uma parede só empurra se a bola estiver encostada nela:

- encostada ($g_i = 0$): $\lambda_i$ pode ser positivo;
- longe ($g_i < 0$): obrigatoriamente $\lambda_i = 0$.

O **sinal** $\lambda_i \ge 0$ diz que a parede só empurra para dentro da região, nunca puxa a bola para fora.

---

## 3. Exemplo em 1D

$$\min\; (x-2)^2 \quad \text{s.a.} \quad x \le 1 \qquad \big(g(x) = x - 1 \le 0\big)$$

O mínimo sem restrição seria $x = 2$, que é inviável. O ótimo é então $x^* = 1$, encostado na parede.

| Condição | Verificação em $x^* = 1$ |
|---|---|
| Viabilidade | $g(1) = 0 \le 0$ ✓ |
| Estacionariedade | $f'(1) + \lambda\, g'(1) = -2 + \lambda \cdot 1 = 0 \;\Rightarrow\; \lambda = 2$ |
| Sinal | $\lambda = 2 \ge 0$ ✓ |
| Complementaridade | $\lambda \cdot g(1) = 2 \cdot 0 = 0$ ✓ |

**Contraste:** com a restrição $x \le 3$, o ótimo seria $x^* = 2$. A parede não é tocada ($g(2) = -1 < 0$), então $\lambda = 0$ e a estacionariedade vira simplesmente $f'(2) = 0$.

---

## 4. Necessário × suficiente

| | Significado | Quando vale |
|---|---|---|
| **Necessário** | todo ótimo é ponto KKT | quando as restrições satisfazem uma *condição de qualificação* (ex.: LICQ). **Restrições lineares sempre satisfazem.** |
| **Suficiente** | todo ponto KKT é ótimo | quando o problema é **convexo** ($f$ convexa e região viável convexa) |

Em problemas gerais, um ponto KKT pode ser máximo local, ponto de sela ou mínimo só local. É preciso convexidade para garantir que ele é o ótimo global.

---

## 5. No nosso problema

**As paredes** são:

- limites dos reservatórios: $h^{\min}_j - I_{jt} \le 0$ e $I_{jt} - h^{\max}_j \le 0$ (384 restrições);
- limites das bombas: $0 \le x, z \le 1$ (768 restrições).

**Ponto KKT = ótimo global.** As duas propriedades da seção 4 valem:

- as restrições são **lineares**, então KKT é necessário;
- $f$ é **estritamente convexa** (ver [adaptacao.md](adaptacao.md), seção 5.1), então KKT é suficiente, e o ponto é único.

SLSQP e Lagrangeano Aumentado são, no fundo, procedimentos para **encontrar um ponto KKT**. Como só existe um, os dois métodos chegarem ao mesmo valor é boa evidência de que ambos acertaram.

**$\lambda$ como preço sombra.** O multiplicador de uma restrição indica **quanto o custo cairia se ela fosse afrouxada em uma unidade**. Exemplo: se o reservatório 2 está cheio ($I = h^{\max}$) logo antes da ponta, o $\lambda$ dessa restrição diz quanto se economizaria com 1 m³ a mais de capacidade ali. É uma informação útil para decidir onde vale a pena ampliar reservatórios.

**No código:** os vetores `lam1` (limite mínimo) e `lam2` (limite máximo) do Lagrangeano Aumentado ([src/main.py:195-196](../src/main.py#L195-L196)) são as estimativas desses $\lambda$. A regra de atualização $\lambda \leftarrow \max(0,\, \lambda + \rho\, g)$ ([linhas 244-245](../src/main.py#L244-L245)) mantém o sinal $\lambda \ge 0$ e zera o multiplicador de restrições folgadas, ou seja, impõe as condições de sinal e complementaridade. Atenção: esses valores estão na escala normalizada do código (objetivo dividido por 1000, restrições por $h^{\max}_j$). Para obter o preço sombra em unidades monetárias por m³, é preciso desfazer essa escala.

# Método 2: Lagrangeano Aumentado (com subproblemas via L-BFGS-B)

Trecho em questão: [src/main.py:190-251](../src/main.py#L190-L251)

Diferente do SLSQP ([slsqp.md](slsqp.md)), este método foi **implementado passo a passo** no código. Só os subproblemas são entregues ao SciPy (L-BFGS-B).

---

## 1. A ideia

As restrições de volume são as "difíceis". Os limites $0 \le u \le 1$ são fáceis: um método de caixa lida com eles diretamente. O Lagrangeano Aumentado faz o seguinte:

1. **Tira as restrições de volume do problema** e as coloca no objetivo, como um termo com multiplicadores $\lambda$ e uma penalidade quadrática $\rho$.
2. Resolve uma **sequência de subproblemas só com caixa**.
3. Entre um subproblema e outro, **atualiza $\lambda$** (e, aqui, aumenta $\rho$).

Com as restrições escritas como $g(u) \le 0$:

$$
g_1(u) = \frac{h_{\min} - I(u)}{h_{\max}} \le 0,
\qquad
g_2(u) = \frac{I(u) - h_{\max}}{h_{\max}} \le 0,
$$

cada subproblema $k$ é

$$
\min_{0 \le u \le 1} \; L_\rho(u, \lambda) =
f(u) + \frac{1}{2\rho} \sum_i \Big[ \max\big(0,\, \lambda_i + \rho\, g_i(u)\big)^2 - \lambda_i^2 \Big].
$$

Essa é a forma de **Rockafellar** para desigualdades. Ela é diferenciável (classe $C^1$), e:

- onde a restrição está folgada e $\lambda_i + \rho g_i \le 0$, o termo vale $-\lambda_i^2/2\rho$, uma constante, e não influencia $u$;
- onde ela está violada ou ativa, age como $\lambda_i g_i + \frac{\rho}{2} g_i^2$: o multiplicador "empurra" para dentro, e a penalidade reforça.

**Por que não só penalidade?** Uma penalidade pura ($\frac{\rho}{2}\sum \max(0,g)^2$) só fica viável com $\rho \to \infty$, e isso deixa o subproblema mal condicionado. Com o termo $\lambda$, o método pode convergir com $\rho$ **finito**. Os multiplicadores fazem o trabalho que a penalidade faria sozinha com $\rho$ enorme.

---

## 2. O código, linha a linha

### 2.1 Inicialização ([main.py:193-198](../src/main.py#L193-L198))

```python
u_aug = u0.copy()           # mesmo ponto inicial do SLSQP (0,35)
lam1 = np.zeros(R * T)      # λ para g1 (volume mínimo), 192 posições
lam2 = np.zeros(R * T)      # λ para g2 (volume máximo), 192 posições
pen_rho = 20.0              # ρ inicial
```

Começar com $\lambda = 0$ significa que o primeiro subproblema é uma **penalidade quadrática pura**.

### 2.2 O subproblema: valor e gradiente ([main.py:201-221](../src/main.py#L201-L221))

```python
g1 = (h_min_vec - I_vec) / h_max_vec
g2 = (I_vec - h_max_vec) / h_max_vec
s1 = np.maximum(0.0, lam1 + pen_rho * g1)
s2 = np.maximum(0.0, lam2 + pen_rho * g2)
L_val  = f_val_s + (0.5 / pen_rho) * (np.sum(s1**2 - lam1**2) + np.sum(s2**2 - lam2**2))
grad_L = g_f_s + M_bal_scaled.T @ (s2 - s1)
```

- **Linhas [207-209](../src/main.py#L207-L209):** as restrições na forma $g \le 0$, escalonadas por $h_{\max}$ ([escalonamento.md](escalonamento.md)).
- **Linhas [212-213](../src/main.py#L212-L213):** $s = \max(0, \lambda + \rho g)$ são os **multiplicadores "tentativos"**. Eles valem zero nas restrições folgadas.
- **Linhas [216-218](../src/main.py#L216-L218):** o valor de $L_\rho$, exatamente a fórmula da seção 1.
- **Linha [220](../src/main.py#L220): o gradiente.** Derivando $\frac{1}{2\rho}\max(0, \lambda + \rho g)^2$ obtém-se $s \cdot \nabla g$. Como $\nabla g_1 = -M/h_{\max}$ e $\nabla g_2 = +M/h_{\max}$:
  $$\nabla L_\rho = \nabla f + M_{\text{scaled}}^\top (s_2 - s_1).$$
  A estrutura é a de $\nabla_u$ do Lagrangeano clássico, $\nabla f + \sum \lambda_i \nabla g_i$, com $s$ no lugar de $\lambda$.

**Por que a função é redefinida dentro do laço:** a cada iteração `lam1`, `lam2` e `pen_rho` mudam. Na prática, a função lê esses nomes do escopo global no momento em que é chamada, então defini-la fora do laço daria o mesmo resultado. Defini-la dentro só deixa explícito que cada $k$ tem seu próprio subproblema.

### 2.3 Resolver o subproblema com L-BFGS-B ([main.py:224-232](../src/main.py#L224-L232))

```python
res_sub = minimize(
    lambda u: aug_lag_and_grad(u)[0], u_aug,
    jac=lambda u: aug_lag_and_grad(u)[1],
    method="L-BFGS-B", bounds=bounds,
    options={"ftol": 1e-11, "gtol": 1e-8, "maxiter": 400},
)
u_aug = res_sub.x
```

**L-BFGS-B** (Byrd, Lu, Nocedal & Zhu, 1995) é um método **quase-Newton de memória limitada** para problemas **só com caixa**:

- Ele aproxima a Hessiana com os últimos $m$ pares (passo, variação do gradiente); o padrão é $m = 10$. Não guarda nenhuma matriz $384 \times 384$.
- A cada iteração, ele segue o gradiente projetado na caixa até o primeiro mínimo ao longo desse caminho (o **ponto de Cauchy generalizado**). Isso identifica quais variáveis ficam presas em 0 ou 1.
- Depois minimiza o modelo quadrático nas variáveis livres e faz uma busca linear.

Parâmetros do código:

- **Warm start (`u_aug`):** cada subproblema parte da solução do anterior. Como $\lambda$ e $\rho$ mudam pouco de uma iteração para a outra, a solução também muda pouco, e isso economiza muitas iterações.
- **`ftol=1e-11`, `gtol=1e-8`:** tolerâncias apertadas. A atualização de $\lambda$ supõe que o subproblema foi bem resolvido.
- **`res_sub.success` não é verificado.** Se um subproblema parasse por `maxiter`, o laço seguiria sem aviso ([revisao.md](../docs/revisao.md), item 4).

### 2.4 Medir, atualizar $\lambda$, aumentar $\rho$ ([main.py:234-249](../src/main.py#L234-L249))

```python
viol_m3 = max(0.0, np.max(h_min_vec - I_cur), np.max(I_cur - h_max_vec))   # em m³, sem escala
lam1 = np.maximum(0.0, lam1 + pen_rho * g1_cur)
lam2 = np.maximum(0.0, lam2 + pen_rho * g2_cur)
if viol_m3 < 1e-4:
    break
pen_rho = min(pen_rho * 3.0, 1e6)
```

- **Linha [239](../src/main.py#L239):** a violação é medida em **m³ físicos**, sem escala. Por isso o critério de parada tem sentido prático.
- **Linhas [244-245](../src/main.py#L244-L245): atualização dos multiplicadores**, $\lambda \leftarrow \max(0, \lambda + \rho g)$. Ela é exatamente o $s$ do subproblema, avaliado na solução. Duas propriedades:
  - o $\max(0,\cdot)$ garante $\lambda \ge 0$ (condição de sinal do KKT);
  - restrições folgadas ($g < 0$) têm o $\lambda$ levado a zero (complementaridade) ([kkt.md](kkt.md)).

  Interpretação: se a restrição $i$ continua violada ($g_i > 0$), $\lambda_i$ cresce e a "empurra" com mais força no próximo subproblema.
- **Linhas [247-248](../src/main.py#L247-L248):** a parada exige violação menor que $10^{-4}$ m³. O critério olha **só a viabilidade**, não a otimalidade (o gradiente do Lagrangeano).
- **Linha [249](../src/main.py#L249):** $\rho$ é multiplicado por 3 **em toda iteração**, até no máximo $10^6$. A regra clássica aumenta $\rho$ só quando a violação não cai o suficiente ([revisao.md](../docs/revisao.md), item 4).

---

## 3. O que acontece na execução

Histórico das iterações externas (o `hist_aug` da [linha 241](../src/main.py#L241)), com $\rho$ usado em cada subproblema:

| $k$ | $\rho$ | Custo $f$ | Violação máx. (m³) |
|---:|---:|---:|---:|
| 1 | 20 | 25.980,75 | 375 |
| 2 | 60 | 27.379,43 | 44,5 |
| 3 | 180 | 27.520,09 | 2,81 |
| 4 | 540 | 27.528,95 | 0,088 |
| 5 | 1.620 | 27.529,20 | 0,0037 |
| 6 | 4.860 | 27.529,21 | 0,00093 |
| 7 | 14.580 | 27.529,21 | 0,00029 |
| 8 | 43.740 | 27.529,21 | 0,00020 |
| 9 | 131.220 | 27.529,21 | 0,00015 |
| 10 | 393.660 | 27.529,21 | 0,000069 ✓ |

Como ler a tabela:

- **O custo começa abaixo do ótimo (25.980) e sobe.** Na iteração 1 ($\lambda = 0$, $\rho$ pequeno), compensa violar o volume mínimo em até 375 m³, porque a penalidade é fraca. Esse ponto é inviável, e por isso mais barato. À medida que $\lambda$ cresce, o método "paga" pela viabilidade, e o custo converge para 27.529,21, o mesmo do SLSQP.
- **Até $k = 5$, a violação cai cerca de 10 a 30 vezes por iteração.** Esse é o efeito combinado dos multiplicadores e do $\rho$ crescente.
- **De $k = 6$ em diante, a queda fica lenta**, mesmo com $\rho$ triplicando. A explicação provável é que o limite passa a ser a **precisão dos subproblemas**: com $\rho$ grande, o L-BFGS-B fica mal condicionado e para (por `ftol`/`gtol`) antes de zerar a violação. Ou seja, aumentar $\rho$ já não estava ajudando.
- **Resultado final:** 134 multiplicadores de mínimo e 2 de máximo positivos, os mesmos 134 + 2 ativos encontrados pelo SLSQP. A maior diferença entre as duas soluções, componente a componente, é de $6\cdot10^{-4}$ (na escala $[0,1]$).
- **Tempo:** ~0,5–0,7 s, contra ~1,8–2,3 s do SLSQP. A comparação é frágil, porque as precisões são diferentes ($10^{-5}$ contra $10^{-9}$ m³) e houve uma execução só ([revisao.md](../docs/revisao.md), item 8).

---

## 4. Convergência: o que a teoria garante

- **Problemas convexos** ($f$ convexa e $g$ afins, como aqui): o método de multiplicadores equivale ao **método do ponto proximal aplicado ao problema dual** (Rockafellar, 1976). Por isso $\lambda_k \to \lambda^*$ para **qualquer $\rho > 0$ fixo**, desde que os subproblemas sejam resolvidos com precisão suficiente (com erros somáveis). Em particular, **não é preciso $\rho \to \infty$**.
- **Caso geral, não convexo** (Nocedal & Wright, cap. 17; Bertsekas, 1982): se $u^*$ satisfaz LICQ e as condições suficientes de 2ª ordem, existe $\bar\rho$ tal que, para $\rho \ge \bar\rho$ e $\lambda$ perto de $\lambda^*$, o subproblema tem minimizador local perto de $u^*$, e a iteração converge linearmente. A taxa melhora quando $\rho$ aumenta.
- **L-BFGS-B, em cada subproblema:** converge para um ponto estacionário do problema com caixa. Como $L_\rho$ é convexa (soma de $f$ convexa com termos convexos em $g$ afim), esse ponto é o minimizador global do subproblema.

O código aumenta $\rho$ mesmo sem necessidade teórica. Isso acelera as primeiras iterações, mas causa a estagnação vista em $k \ge 6$.

---

## 5. Vantagens e limitações aqui

| Vantagens | Limitações |
|---|---|
| Cada subproblema é **só com caixa**, e o L-BFGS-B resolve isso de forma barata, com memória $O(mn)$ e sem QP denso | Mais parâmetros para ajustar: $\rho_0$, fator de aumento, teto, tolerâncias internas e externas |
| Escala melhor para problemas grandes | Precisão de viabilidade menor (~$10^{-5}$ m³), limitada pelo condicionamento |
| Transparente: dá para acompanhar $\lambda$, $\rho$ e a violação a cada passo | O critério de parada ignora a otimalidade, e o sucesso dos subproblemas não é verificado |
| Os $\lambda$ finais são estimativas dos preços sombra ([kkt.md](kkt.md)) | Com $\rho$ muito grande, o subproblema fica mal condicionado |

**Possíveis melhorias** (detalhadas em [revisao.md](../docs/revisao.md), item 4):

1. aumentar $\rho$ só quando a violação não cair pelo menos à metade;
2. parar também pela norma do gradiente projetado de $L_\rho$;
3. verificar `res_sub.success`;
4. passar `jac=True` com uma função que devolve `(L, grad)`, para não calcular `aug_lag_and_grad` duas vezes por ponto.

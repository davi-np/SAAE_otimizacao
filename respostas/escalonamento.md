# Por que escalonar o objetivo e as restrições?

Trecho em questão: [src/main.py:111-113](../src/main.py#L111-L113)

```python
f_scale = 1000.0
M_bal_scaled = M_bal / h_max_vec[:, None]
```

Isso é **escalonamento numérico** e **não muda a solução** do problema. O objetivo é que os dois otimizadores trabalhem com números de tamanho parecido. Sem a escala, a função objetivo e as restrições ficam em unidades e ordens de grandeza muito diferentes.

---

## 1. O problema sem escala

Valores medidos no próprio código:

| Grandeza | Ordem de grandeza |
|---|---|
| Custo $f(u)$ com todas as bombas a 50% | ~37.000 |
| Maior componente do gradiente | ~2.160 |
| Faixa de volume permitida no reservatório 3 ($h_{\max} - h_{\min}$) | 74 m³ |
| Faixa de volume permitida no reservatório 4 | 1.820 m³ |
| Entradas de `M_bal` (por reservatório) | 70 a 750 |

Isso causa três problemas.

### 1.1 As tolerâncias são absolutas

O SLSQP para quando a variação de $f$ fica abaixo de `ftol` e aceita violações de restrição abaixo de um limite fixo.

- Com $f$ na casa de 37.000, uma tolerância como $10^{-6}$ é muito mais rígida do que o necessário.
- Nas restrições, 1 m³ de violação é desprezível no reservatório 4 (2.600 m³), mas passa de 1% da faixa do reservatório 3 (74 m³).

### 1.2 O Lagrangeano Aumentado usa um só μ para todas as restrições

A penalidade é do tipo

$$\frac{\mu}{2}\sum_i \max(0,\, g_i)^2 .$$

Sem escala, um déficit de algumas centenas de m³ no reservatório 4 dominaria a soma, e as restrições do reservatório 3 quase não pesariam. Nenhum valor de μ serviria bem para os quatro reservatórios ao mesmo tempo.

### 1.3 Condicionamento

O subproblema resolvido pelo L-BFGS-B soma dois termos:

- o objetivo, com Hessiana da ordem de $2\beta c$ (até ~1.100);
- a penalidade, $\mu\, M^\top M$, com entradas de $M$ até 750.

Termos muito desbalanceados deixam a Hessiana mal condicionada, e a convergência fica mais lenta.

---

## 2. O que cada linha faz

### `f_scale = 1000`

O custo passa a ser medido em **milhares de R$**, e $f$ fica na ordem de dezenas. O gradiente é dividido pelo mesmo fator ([main.py:181](../src/main.py#L181) e [main.py:205](../src/main.py#L205)).

### `M_bal_scaled = M_bal / h_max_vec[:, None]`

As restrições passam a ser escritas como **fração da capacidade** de cada reservatório:

$$\frac{I_{jt} - h_{\min,j}}{h_{\max,j}} \ge 0, \qquad \frac{h_{\max,j} - I_{jt}}{h_{\max,j}} \ge 0 .$$

Como $I = b + M u$, a Jacobiana dessa restrição é `M_bal / h_max`, aplicada linha por linha. É essa matriz que entra:

- no campo `jac` das restrições do SLSQP ([main.py:169](../src/main.py#L169) e [main.py:174](../src/main.py#L174));
- no gradiente do Lagrangeano aumentado, `grad_L` ([main.py:220](../src/main.py#L220)).

**Sobre o `[:, None]`:** ele transforma o vetor de 192 posições em uma coluna (192 × 1). Assim, o broadcasting do NumPy divide cada **linha** de `M_bal` pelo $h_{\max}$ do reservatório dela.

Depois da escala, as entradas da matriz ficam entre ~0,16 e ~1,0 nos quatro reservatórios:

| Reservatório | max \|`M_bal`\| | max \|`M_bal_scaled`\| |
|---|---:|---:|
| 1 | 70 | 0,35 |
| 2 | 120 | 0,16 |
| 3 | 107 | 1,01 |
| 4 | 750 | 0,29 |

---

## 3. Por que a solução não muda

Dividir o objetivo por uma constante positiva e cada restrição por outra constante positiva preserva o conjunto viável e o ponto de mínimo. O que muda são os **valores**:

- **Objetivo:** $f$ precisa ser multiplicado de volta, o que é feito em [main.py:188](../src/main.py#L188).
- **Multiplicadores:** mudam de escala,
  $$\lambda_{\text{real}} = \lambda_{\text{escalado}} \cdot \frac{f_{\text{scale}}}{h_{\max,j}} .$$
  Lembre disso se for interpretar os λ (ver [kkt.md](kkt.md)) como custo marginal em R$/m³.
- **Violação reportada:** a violação máxima em m³ é recalculada **sem escala** ([main.py:239](../src/main.py#L239) e [main.py:306-308](../src/main.py#L306-L308)). Por isso esse número continua tendo sentido físico.

---

## 4. Observação

A escala usa $h_{\max}$, e não a faixa $h_{\max} - h_{\min}$. As duas opções funcionam. Usar a faixa equilibraria ainda mais os reservatórios, mas a diferença aqui é pequena.

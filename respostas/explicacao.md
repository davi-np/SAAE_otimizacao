# Entendendo o projeto

Guia curto para entender o problema, o modelo e o que o código [src/main.py](../src/main.py) faz.

---

## 1. O problema real

O SAAE de São Carlos usa **bombas** para levar água de poços/ETA até **reservatórios** espalhados pelos bairros. Dos reservatórios, a água chega às casas por gravidade.

A energia elétrica tem **tarifa horo-sazonal**: entre 18h e 21h (horário de ponta) ela custa o **dobro**. A pergunta é:

> Quanto cada bomba deve operar em cada hora para que nenhum reservatório fique abaixo do mínimo de segurança nem transborde, pagando o menor custo de energia possível?

A ideia intuitiva é "encher antes da ponta". Mas há um contrapeso: os reservatórios **perdem 10% do volume por hora** (vazamentos). Água estocada cedo demais se perde. O ótimo equilibra esses dois efeitos.

**Instância usada:** 4ª classe do artigo (Soler et al., 2016) — 4 reservatórios reais de São Carlos, 48 horas (2 dias), ponta nos períodos 19–21 e 43–45.

```
   (1) ──► (2) ◄── (3) ◄──► (4)        setas = bombas de transferência
    ▲       ▲       ▲        ▲
  poço    poço    poço      ETA        cada reservatório tem sua bomba de captação
```

---

## 2. O modelo original do artigo (linear inteiro-misto)

| Símbolo | Significado |
|---|---|
| $x_{jt} \in [0,1]$ | fração da hora $t$ em que a bomba de captação $j$ fica ligada |
| $z_{jlt} \in [0,1]$ | fração da hora em que a bomba de transferência $j \to l$ fica ligada |
| $I_{jt}$ | volume do reservatório $j$ no fim da hora $t$ |
| $y_{jt}, \alpha_{jt} \in \{0,1\}$ | bomba ligada? / bomba foi acionada nesta hora? |

- **Objetivo:** custo de manter bombas ligadas ($c_{jt} x_{jt}$, $\gamma z$) + custo de acionamento ($sc_{jt}\alpha_{jt}$).
- **Balanço de massa:** $I_{jt} = (1-\theta) I_{j,t-1} + v_j x_{jt} - (\text{sai por transf.}) + (\text{entra por transf.}) - d_{jt}$
- **Limites:** $h^{\min}_j \le I_{jt} \le h^{\max}_j$.

Por causa das variáveis binárias, isso **não** é um problema de otimização não-linear contínua. O artigo resolve com CPLEX e com uma heurística.

---

## 3. A adaptação feita pelo grupo

Para caber no escopo da disciplina, o modelo foi transformado num problema **contínuo, suave e convexo** (versão detalhada em [adaptacao.md](adaptacao.md)):

| Original | Adaptação | Motivo |
|---|---|---|
| $x$ = fração do **tempo** ligada | $x$ = fração da **vazão** (bomba com inversor de frequência) | reinterpretação física; $x$ já era contínuo, isso só justifica o custo não-linear abaixo |
| custo de acionamento $sc \cdot \alpha$ (com as binárias $y$, $\alpha$) | $\rho\,(x_{jt} - x_{j,t-1})^2$, com $\rho = 15$ | **é aqui que as binárias somem**; desestimula variações bruscas |
| custo linear $c \cdot x$ | $c\,(x + \beta x^2)$, com $\beta = 0{,}35$ | operar em vazão alta custa proporcionalmente mais (perda de carga) |
| $I_{jt}$ como variável | $I_{jt}$ **eliminado** (escrito em função de $x, z$) | sobram só restrições de desigualdade e caixa |

**Eliminação dos volumes.** Aplicando o balanço recursivamente, o volume na hora $t$ é:

$$I_{jt} = \underbrace{(1-\theta)^{t} I_{j0}}_{\text{volume inicial, já com perdas}} + \sum_{s \le t} (1-\theta)^{t-s}\big(\text{entradas} - \text{saídas} - d_{js}\big)_s$$

Isso é **afim** nas decisões: $I = b + M u$, onde $u = (x, z)$ tem 384 componentes (8 bombas × 48 h).

**Problema final:**

$$\min_{u \in [0,1]^{384}} f(u) \quad \text{s.a.} \quad h^{\min} \le b + M u \le h^{\max}$$

$f$ é **estritamente convexa** (Hessiana diagonal positiva + termo de suavização semidefinido) e as restrições são **lineares**. Consequência: existe um único mínimo global, e qualquer ponto KKT ([o que é isso?](kkt.md)) é ele. Por isso os dois métodos devem chegar ao mesmo valor — o que serve de verificação cruzada.

---

## 4. Mapa do código

| Seção | Linhas | O que faz |
|---|---|---|
| Dados | [22–57](../src/main.py#L22-L57) | Tabelas 2 e 3 do artigo, tarifa por hora, $\theta$, $\beta$, $\rho$ |
| Demanda | [62–73](../src/main.py#L62-L73) | Demanda sintética por faixa do dia + ruído (semente 42) |
| Balanço | [88–113](../src/main.py#L88-L113) | Monta $b$ e $M$ (volume = $b + Mu$) e o escalonamento |
| Objetivo | [118–144](../src/main.py#L118-L144) | $f(u)$ e gradiente analítico; [check_grad](../src/main.py#L154-L159) confere o gradiente |
| SLSQP | [164–188](../src/main.py#L164-L188) | Resolve com `scipy.optimize.minimize(method="SLSQP")` |
| Lagr. Aumentado | [193–251](../src/main.py#L193-L251) | Implementação própria; subproblemas com L-BFGS-B |
| Método Usual | [256–297](../src/main.py#L256-L297) | Simula a regra prática do SAAE (sem otimização) |
| Comparação | [302–331](../src/main.py#L302-L331) | Imprime custos, violações e uso médio das bombas |

---

## 5. Os dois métodos, em uma frase cada

- **SLSQP (Programação Quadrática Sequencial):** a cada iteração aproxima o problema por um QP (modelo quadrático do Lagrangeano + restrições linearizadas), resolve e dá um passo. Aqui as restrições já são lineares, então a linearização é exata.
- **Lagrangeano Aumentado:** troca as restrições de volume por uma penalidade com multiplicadores $\lambda$. Resolve uma sequência de problemas só com caixa $[0,1]$ (via L-BFGS-B); entre eles, atualiza $\lambda \leftarrow \max(0, \lambda + \rho g)$ e aumenta $\rho$. Para quando a violação fica abaixo de $10^{-4}$ m³.

---

## 6. O "Método Usual" (linha de base)

Reproduz a regra que o artigo (Seção 4.5) diz ser usada na prática:

- Fora da ponta: quando o reservatório atinge o mínimo, liga a bomba a 100% até encher.
- Na ponta: desliga, a não ser que o reservatório vá secar.
- Transferências não são usadas.

A operação resultante é avaliada **na mesma função $f$** e comparada com o ótimo.

---

## 7. Saída esperada

```
Método Usual  | Custo = 41.111,80
SLSQP         | Custo = 27.529,21 | 21 iterações
Lagr. Aument. | Custo = 27.529,21 | 10–11 iterações externas
Economia: 33,04%
```

Os dois otimizadores concordam, como a convexidade prevê. **Mas** o número de 33% precisa de cuidado na interpretação — ver [revisao.md](../docs/revisao.md).

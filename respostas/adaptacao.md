# A adaptação do modelo, passo a passo

Detalha a Seção 3 de [explicacao.md](explicacao.md): o que mudou em relação ao artigo, por quê, e o que se ganha e se perde em cada mudança.

---

## 0. Por que adaptar?

No modelo de Soler et al. (2016), as variáveis de **controle** das bombas já são **contínuas**:

- $x_{jt} \in [0,1]$: fração da hora em que a bomba de captação fica ligada (restrições 2 e 6 do artigo);
- $z_{jlt} \in [0,1]$: idem para a transferência (restrição 5).

As binárias são **auxiliares**, e existem só para cobrar o custo de acionamento:

- $y_{jt} \in \{0,1\}$: houve captação na hora $t$? A restrição $x_{jt} \le y_{jt}$ força $y = 1$ sempre que $x > 0$.
- $\alpha_{jt} \in \{0,1\}$: a bomba foi **acionada** na hora $t$? A restrição $\alpha_{jt} \ge y_{jt} - y_{j,t-1}$ força $\alpha = 1$ quando a bomba não operou na hora anterior e opera nesta.

Ou seja, eliminar as binárias equivale a **eliminar o custo de acionamento**.

Com binárias, o problema é de **programação linear inteira mista**, fora do escopo de otimização não-linear contínua. A adaptação precisa:

1. eliminar as binárias;
2. ter um objetivo genuinamente **não-linear** (sem isso, sobraria um problema linear);
3. preservar o sentido físico do problema.

> **Observação importante.** Só apagar $y$ e $\alpha$ e manter o resto gera a **relaxação linear** do modelo. Ela é um problema linear, não não-linear. O próprio artigo usa essa relaxação como limitante inferior ($f^L$) no cálculo do *gap*. Por isso as mudanças 2 e 3 abaixo são necessárias, e não apenas cosméticas.

---

## 1. Variáveis contínuas: de "tempo ligado" para "vazão"

| | Artigo | Adaptação |
|---|---|---|
| $x_{jt}$ | fração da hora em que a bomba fica ligada a 100% | fração da vazão máxima durante a hora toda |
| Exemplo $x = 0{,}5$ | ligada 30 min, desligada 30 min | ligada 60 min, a 50% da vazão |
| Água captada | $v_j \, x_{jt}$ | $v_j \, x_{jt}$ (igual) |

**Justificativa física:** bombas com **inversor de frequência** regulam a rotação e, com ela, a vazão de forma contínua.

**O que muda na matemática:** nada, por enquanto. $x$ já era contínuo no artigo, então esta mudança **não** é o que elimina as binárias; isso é feito no passo 3. A água bombeada continua $v_j x_{jt}$ e o balanço de massa é o mesmo. A mudança de interpretação é o que justifica, nos passos seguintes, um custo que depende de *quanto* a bomba opera, e não só de *se* ela opera.

O mesmo vale para as transferências $z_{et}$.

---

## 2. Custo não-linear: $c\,x \;\to\; c\,(x + \beta x^2)$

**Ideia:** operar a bomba em vazão alta custa mais que proporcionalmente, porque a perda de carga na tubulação cresce com a vazão.

**Exemplo** (mesma água, $\beta = 0{,}35$):

| Estratégia | Custo |
|---|---|
| 1 hora a 100% | $c\,(1 + 0{,}35) = 1{,}35\,c$ |
| 2 horas a 50% | $2 \cdot c\,(0{,}5 + 0{,}35 \cdot 0{,}25) = 1{,}175\,c$ |

O termo quadrático **premia espalhar o bombeamento**. No modelo linear do artigo, as duas estratégias custariam o mesmo ($c$). Com $\beta > 0$, a solução ótima espalha a captação por várias horas: 186 dos 192 valores de $x$ ficam estritamente entre 0 e 1.

**Ressalvas:**

- Pelas leis de afinidade, a potência de uma bomba cresce aproximadamente com o **cubo** da rotação. O quadrático é uma simplificação convexa e diferenciável, não uma lei física exata.
- $\beta = 0{,}35$ é um valor escolhido pelo grupo, sem calibração com dados reais.
- O termo é aplicado também a $z$, com coeficiente $\gamma$.

---

## 3. Suavização: custo de acionamento $\to$ $\rho\,(x_{jt} - x_{j,t-1})^2$

**No artigo:** cada vez que a bomba é ligada, paga-se $sc_{jt}$ (igual a 1 nas instâncias). A restrição $\alpha_{jt} \ge y_{jt} - y_{j,t-1}$ força $\alpha = 1$ quando a bomba passa de desligada para ligada. O objetivo é evitar operação intermitente.

**Na adaptação:** a "variação de rotação" entre horas vizinhas é penalizada quadraticamente, com $\rho = 15$ e $x_{j,0} = 0$ (bombas desligadas antes do início).

| Transição | Penalidade |
|---|---|
| $0 \to 1$ direto | $15 \cdot 1^2 = 15$ |
| $0 \to 0{,}5 \to 1$ (em duas horas) | $15 \cdot (0{,}25 + 0{,}25) = 7{,}5$ |
| $0{,}4 \to 0{,}45$ | $15 \cdot 0{,}0025 \approx 0{,}04$ |

**Diferenças em relação ao original:**

- O artigo cobra só ao **ligar**; aqui também se paga ao **desligar** e a cada pequena variação.
- Rampas suaves saem mais baratas que saltos, então o termo empurra a solução para perfis contínuos no tempo.
- O peso é pequeno perto das tarifas (100 a 1600). Para o reservatório 4 ($c = 800$), o termo é quase irrelevante.
- Não é aplicado a $z$. Isso é coerente com o artigo, que não cobra acionamento de transferências por considerá-las "esporádicas".

> **Faz sentido penalizar ao desligar?** Sim, desde que o termo seja entendido como penalidade de **variação de rotação** (desgaste e golpe de aríete em paradas bruscas), e não como substituto fiel do custo de acionamento. Nos testes, penalizar só a subida muda o custo em cerca de 0,3%. Detalhes e recomendação em [revisao.md](revisao.md), item 17.

---

## 4. Eliminação dos volumes $I_{jt}$

Este é o passo mais técnico. Ele não muda o problema, só a forma de escrevê-lo.

### 4.1 Desenrolando o balanço

Seja $q_{jt}$ o saldo líquido da hora $t$ (captação + transferências recebidas − enviadas − demanda). O balanço é:

$$I_{jt} = (1-\theta)\,I_{j,t-1} + q_{jt}$$

Aplicando a fórmula repetidamente:

$$
\begin{aligned}
I_{j1} &= (1-\theta)\,I_{j0} + q_{j1} \\
I_{j2} &= (1-\theta)^2 I_{j0} + (1-\theta)\,q_{j1} + q_{j2} \\
I_{j3} &= (1-\theta)^3 I_{j0} + (1-\theta)^2 q_{j1} + (1-\theta)\,q_{j2} + q_{j3} \\
&\;\;\vdots \\
I_{jt} &= (1-\theta)^t I_{j0} + \sum_{s=1}^{t} (1-\theta)^{t-s}\, q_{js}
\end{aligned}
$$

**Leitura:** a água que entrou $k$ horas atrás vale hoje $(1-\theta)^k$ do volume original. Com $\theta = 10\%$:

| Bombeada há | Sobra |
|---|---:|
| 1 h | 90% |
| 3 h | 73% |
| 6 h | 53% |
| 7 h | 48% |

Como a ponta custa o **dobro**, adiantar o bombeamento só compensa enquanto sobra mais de 50% da água, ou seja, até cerca de **6 horas antes** da ponta. É exatamente o critério de "períodos pré-críticos" da Eq. (9) do artigo, e a otimização o descobre sozinha. O termo $\beta$ desloca um pouco esse limite.

### 4.2 Forma matricial

Como $q_{js}$ é linear em $x$ e $z$, cada $I_{jt}$ é uma função **afim** de $u = (x, z)$:

$$I = b + M\,u$$

- **$b$**: volume inicial com perdas, menos todas as demandas acumuladas com perdas. Não depende das decisões.
- **$M$**: cada coluna corresponde a uma bomba numa hora $s$. Na linha $(j, t)$, a coluna da captação $x_{js}$ vale $v_j (1-\theta)^{t-s}$ se $s \le t$ e $0$ caso contrário, porque a água de hoje não afeta o passado. Para uma transferência $e$, o valor é $\pm w_e (1-\theta)^{t-s}$: $+$ se $e$ entra em $j$, $-$ se sai.

No código: [src/main.py:88-106](../src/main.py#L88-L106). O código usa índices a partir de 0, por isso aparece $(1-\theta)^{t+1}$.

### 4.3 As duas formas de escrever o mesmo problema

**Com $I$ como variável** (como no artigo): o otimizador escolhe $x$, $z$ **e** $I$, como se "chutasse" os volumes. As equações de balanço entram como restrições de igualdade que amarram tudo. Um ponto em que $I$ não bate com o bombeamento é **inviável**.

**Com $I$ eliminado** (como no código): o otimizador escolhe só $x$ e $z$. Os volumes são **calculados** por $I = b + Mu$, como uma coluna de planilha preenchida por fórmula. O balanço vale automaticamente em qualquer ponto.

Exemplo com 1 reservatório e 2 horas:

| | Com $I$ como variável | Com $I$ eliminado |
|---|---|---|
| Incógnitas | $x_1, x_2, I_1, I_2$ | $x_1, x_2$ |
| Balanço | $I_1 = 0{,}9\,I_0 + v x_1 - d_1$ e $I_2 = 0{,}9\,I_1 + v x_2 - d_2$ (restrições) | já embutido na fórmula de $I_1(x)$ e $I_2(x)$ |
| Limites de volume | $h^{\min} \le I_t \le h^{\max}$ (limites simples das variáveis $I$) | $h^{\min} \le I_t(x) \le h^{\max}$ (desigualdades lineares em $x$) |

Na instância completa:

| | Com $I$ como variável | Com $I$ eliminado |
|---|---:|---:|
| Variáveis | 576 ($x$, $z$, $I$) | 384 ($x$, $z$) |
| Igualdades de balanço | 192 | 0 |
| Limites de volume (mín. e máx.) | 384, como **limites de caixa** das variáveis $I$ | 384, como **desigualdades lineares gerais** em $u$ |
| Limites $0 \le x, z \le 1$ | 768 | 768 |

**Ganhos da eliminação:** o problema fica menor, sem igualdades, e todo ponto visitado pelo otimizador é fisicamente coerente (o volume sempre corresponde ao bombeamento).

**Custo:** $M$ é densa no tempo, porque cada $I_{jt}$ depende de todas as horas anteriores. Já as equações de balanço só ligam horas vizinhas. Nesta instância pequena isso não importa.

As duas formas têm a mesma solução. A eliminação é uma escolha de implementação, não uma exigência. O Lagrangeano Aumentado funcionaria nas duas: aqui ele penaliza as desigualdades de volume; na outra forma, penalizaria as igualdades de balanço. Nos dois casos, os subproblemas ficam só com caixa.

---

## 5. O problema resultante e por que ele é "bem comportado"

$$
\min_{u \in [0,1]^{384}} \;
\sum_{j,t} \Big[ c_{jt}(x_{jt} + \beta x_{jt}^2) + \rho (x_{jt} - x_{j,t-1})^2 \Big]
+ \sum_{e,t} \gamma_{et}(z_{et} + \beta z_{et}^2)
\quad \text{s.a.} \quad h^{\min} \le b + M u \le h^{\max}
$$

### 5.1 Convexidade estrita, passo a passo

**O que queremos mostrar.** Que $f$ tem formato de "tigela": um único fundo, sem regiões planas. A ferramenta é a Hessiana $H$ (matriz das derivadas segundas). Se $v^\top H v > 0$ para todo $v \ne 0$ ($H$ **positiva definida**), então $f$ é estritamente convexa.

Como $f$ é uma soma de termos, $H$ é a soma das Hessianas de cada termo. Basta olhar um termo por vez.

**Termo 1: custo $c\,(x + \beta x^2)$ e $\gamma\,(z + \beta z^2)$.**

Cada parcela depende de **uma única** variável:

- A parte linear $c\,x$ tem derivada segunda zero e não contribui.
- A parte $c\beta x^2$ tem derivada segunda $2\beta c$.
- Derivadas cruzadas (entre variáveis diferentes) são zero, porque nenhuma parcela mistura duas variáveis.

Resultado: uma matriz **diagonal**

$$H_1 = \mathrm{diag}\big(2\beta c_{11}, \dots, 2\beta c_{4,48},\; 2\beta\gamma_{11}, \dots, 2\beta\gamma_{4,48}\big)$$

Todas as entradas são positivas ($\beta = 0{,}35$, $c \ge 100$, $\gamma \ge 3$). Logo

$$v^\top H_1 v = \sum_i 2\beta c_i\, v_i^2 > 0 \quad \text{para todo } v \ne 0,$$

pois é uma soma de quadrados com pesos positivos, e pelo menos um $v_i$ é diferente de zero. **$H_1$ é positiva definida.**

**Termo 2: suavização $\rho \sum (x_{jt} - x_{j,t-1})^2$.**

Este termo **mistura** horas vizinhas, então gera entradas fora da diagonal. Exemplo para uma bomba e 3 horas, com $x_0 = 0$:

$$\rho\big[x_1^2 + (x_2 - x_1)^2 + (x_3 - x_2)^2\big]$$

Chamando de $D$ a matriz que calcula as diferenças,

$$D = \begin{pmatrix} 1 & 0 & 0 \\ -1 & 1 & 0 \\ 0 & -1 & 1 \end{pmatrix}, \qquad Dx = \begin{pmatrix} x_1 \\ x_2 - x_1 \\ x_3 - x_2 \end{pmatrix},$$

o termo é $\rho\,\|Dx\|^2$, e sua Hessiana é $H_2 = 2\rho\, D^\top D$.

> **Como ler $D$.** Cada linha de $D$ produz uma das diferenças. Multiplicando linha por vetor:
>
> - linha 1, $(1, 0, 0)$: $1 \cdot x_1 = x_1$. É $x_1 - x_0$ com $x_0 = 0$.
> - linha 2, $(-1, 1, 0)$: $-x_1 + x_2 = x_2 - x_1$.
> - linha 3, $(0, -1, 1)$: $-x_2 + x_3 = x_3 - x_2$.
>
> $\|Dx\|^2$ é a soma dos quadrados das entradas de $Dx$, ou seja, exatamente $x_1^2 + (x_2 - x_1)^2 + (x_3 - x_2)^2$. A matriz é só uma forma compacta de escrever o termo de suavização.
>
> **Conferindo a Hessiana na mão.** Com $g = x_1^2 + (x_2 - x_1)^2 + (x_3 - x_2)^2$:
>
> $$\frac{\partial g}{\partial x_1} = 4x_1 - 2x_2, \qquad \frac{\partial g}{\partial x_2} = -2x_1 + 4x_2 - 2x_3, \qquad \frac{\partial g}{\partial x_3} = -2x_2 + 2x_3$$
>
> $$\nabla^2 g = \begin{pmatrix} 4 & -2 & 0 \\ -2 & 4 & -2 \\ 0 & -2 & 2 \end{pmatrix} = 2 \begin{pmatrix} 2 & -1 & 0 \\ -1 & 2 & -1 \\ 0 & -1 & 1 \end{pmatrix} = 2\, D^\top D$$
>
> Multiplicando por $\rho$: $H_2 = 2\rho\, D^\top D$. Escrever assim é útil porque $v^\top (D^\top D) v = (Dv)^\top (Dv) = \|Dv\|^2$, e o sinal fica evidente sem calcular nada.

Para qualquer $v$:

$$v^\top H_2 v = 2\rho\, \|Dv\|^2 \ge 0.$$

É uma norma ao quadrado, então nunca é negativa. **$H_2$ é positiva semidefinida.** Basta isso; não precisamos que ela seja definida. Ela vale zero, por exemplo, em direções que só mexem em $z$, porque a suavização não envolve $z$.

**Juntando os dois:**

$$v^\top H v = \underbrace{v^\top H_1 v}_{> 0} + \underbrace{v^\top H_2 v}_{\ge 0} > 0 \quad \text{para todo } v \ne 0.$$

Logo $H$ é positiva definida, e **$f$ é estritamente convexa**.

**Duas observações:**

- $f$ é **quadrática**: polinômio de grau 2 em $u$. Por isso $H$ é constante e o argumento vale em qualquer ponto, não só perto do ótimo.
- Quem garante a convexidade **estrita** é o termo $\beta$. Sem ele ($\beta = 0$), $H = H_2$ seria só semidefinida, e poderiam existir vários ótimos empatados. É o que acontece no modelo linear original, em que o ótimo pode ser uma aresta ou face inteira do poliedro.

**Consequências:**

| Fato | Por quê |
|---|---|
| Existe solução | conjunto viável fechado e limitado (caixa) e $f$ contínua, desde que haja ponto viável |
| Ela é única | $f$ estritamente convexa sobre conjunto convexo |
| KKT é **necessário** | restrições lineares dispensam condições de qualificação (LICQ etc.) |
| KKT é **suficiente** | problema convexo |

Portanto, qualquer método que encontre um ponto KKT ([o que é isso?](kkt.md)) encontrou **o** ótimo global. É por isso que SLSQP e Lagrangeano Aumentado devem dar o mesmo resultado, e de fato dão.

**Escalonamento (detalhe numérico):** no código, $f$ é dividida por 1000 e cada restrição de volume por $h^{\max}_j$. Isso não muda a solução, só deixa os números perto de 1 e ajuda os otimizadores.

---

## 6. Balanço: o que a adaptação custa

| Ganho | Perda |
|---|---|
| Problema contínuo, suave e convexo | $f$ deixa de ser "reais gastos": $\beta x^2$ e $\rho\,\Delta x^2$ são termos de modelagem |
| Ótimo global garantido e verificável | $\beta$ e $\rho$ são escolhidos sem calibração |
| Métodos de NLP aplicáveis | Comparar com o Método Usual em $f$ favorece o otimizado (ver [revisao.md](revisao.md), item 1) |
| Resolve em segundos | Perde-se a contagem discreta de partidas (custo de acionamento) do original |

**Recomendação:** reportar a economia usando só a parte linear ($\sum c\,x + \sum \gamma\,z$), que é o custo de energia comparável ao do artigo, e apresentar $\beta$ e $\rho$ como parâmetros de regularização, idealmente com uma análise de sensibilidade.

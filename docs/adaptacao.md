# A adaptação do modelo, passo a passo

Detalha a Seção 3 de [explicacao.md](explicacao.md): o que mudou em relação ao artigo, por quê, e o que se ganha e se perde em cada mudança.

---

## 0. Por que adaptar?

O modelo de Soler et al. (2016) tem duas variáveis **binárias** por bomba e por hora:

- $y_{jt} \in \{0,1\}$: a bomba está ligada na hora $t$?
- $\alpha_{jt} \in \{0,1\}$: a bomba foi **acionada** na hora $t$, ou seja, estava desligada e foi ligada?

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

**O que muda na matemática:** nada, por enquanto. A água bombeada continua $v_j x_{jt}$ e o balanço de massa é o mesmo. A mudança de interpretação é o que justifica, nos passos seguintes, um custo que depende de *quanto* a bomba opera, e não só de *se* ela opera.

O mesmo vale para as transferências $z_{et}$.

---

## 2. Custo não-linear: $c\,x \;\to\; c\,(x + \beta x^2)$

**Ideia:** operar a bomba em vazão alta custa mais que proporcionalmente, porque a perda de carga na tubulação cresce com a vazão.

**Exemplo** (mesma água, $\beta = 0{,}35$):

| Estratégia | Custo |
|---|---|
| 1 hora a 100% | $c\,(1 + 0{,}35) = 1{,}35\,c$ |
| 2 horas a 50% | $2 \cdot c\,(0{,}5 + 0{,}35 \cdot 0{,}25) = 1{,}175\,c$ |

O termo quadrático **premia espalhar o bombeamento**. Por isso a solução ótima tem valores intermediários ($x \approx 0{,}4$), e não o "liga a 100% / desliga" do modelo original.

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

### 4.3 O que se ganha

| | Com $I$ como variável | Com $I$ eliminado |
|---|---:|---:|
| Variáveis | 384 + 192 = 576 | 384 |
| Restrições de igualdade | 192 | 0 |
| Desigualdades $h^{\min} \le I \le h^{\max}$ | 384 | 384 |
| Limites de caixa | 768 | 768 |

O ganho principal está no Lagrangeano Aumentado. Sem igualdades, as únicas restrições difíceis são as 384 desigualdades de volume. Penalizando-as, cada subproblema fica **só com caixa** $[0,1]$, que o L-BFGS-B resolve muito bem.

---

## 5. O problema resultante e por que ele é "bem comportado"

$$
\min_{u \in [0,1]^{384}} \;
\sum_{j,t} \Big[ c_{jt}(x_{jt} + \beta x_{jt}^2) + \rho (x_{jt} - x_{j,t-1})^2 \Big]
+ \sum_{e,t} \gamma_{et}(z_{et} + \beta z_{et}^2)
\quad \text{s.a.} \quad h^{\min} \le b + M u \le h^{\max}
$$

**Convexidade estrita.** A Hessiana é a soma de:

- uma matriz **diagonal** com entradas $2\beta c_{jt} > 0$ e $2\beta\gamma_{et} > 0$, positiva definida;
- $2\rho\, D^\top D$, onde $D$ calcula as diferenças $x_{jt} - x_{j,t-1}$, positiva semidefinida.

Positiva definida + semidefinida = **positiva definida**. Logo $f$ é estritamente convexa.

**Consequências:**

| Fato | Por quê |
|---|---|
| Existe solução | conjunto viável fechado e limitado (caixa) e $f$ contínua, desde que haja ponto viável |
| Ela é única | $f$ estritamente convexa sobre conjunto convexo |
| KKT é **necessário** | restrições lineares dispensam condições de qualificação (LICQ etc.) |
| KKT é **suficiente** | problema convexo |

Portanto, qualquer método que encontre um ponto KKT encontrou **o** ótimo global. É por isso que SLSQP e Lagrangeano Aumentado devem dar o mesmo resultado, e de fato dão.

**Escalonamento (detalhe numérico):** no código, $f$ é dividida por 1000 e cada restrição de volume por $h^{\max}_j$. Isso não muda a solução, só deixa os números perto de 1 e ajuda os otimizadores.

---

## 6. Balanço: o que a adaptação custa

| Ganho | Perda |
|---|---|
| Problema contínuo, suave e convexo | $f$ deixa de ser "reais gastos": $\beta x^2$ e $\rho\,\Delta x^2$ são termos de modelagem |
| Ótimo global garantido e verificável | $\beta$ e $\rho$ são escolhidos sem calibração |
| Métodos de NLP aplicáveis | Comparar com o Método Usual em $f$ favorece o otimizado (ver [revisao.md](revisao.md), item 1) |
| Resolve em segundos | Perde-se a lógica discreta de "liga/desliga" do original |

**Recomendação:** reportar a economia usando só a parte linear ($\sum c\,x + \sum \gamma\,z$), que é o custo de energia comparável ao do artigo, e apresentar $\beta$ e $\rho$ como parâmetros de regularização, idealmente com uma análise de sensibilidade.

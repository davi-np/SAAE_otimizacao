# Revisão: código e relatório

**Como foi verificado:** rodei `src/main.py` (numpy/scipy recentes) e scripts auxiliares de análise. Os custos do relatório **se reproduzem** (27.529,21 / 41.111,80 / 33,04%). Os problemas abaixo são de **interpretação, metodologia e redação** — o núcleo matemático está correto (ver final).

---

## Prioridade alta — afetam as conclusões

### 1. A economia de 33% está inflada

Dois efeitos somados:

**a) Termos artificiais contam como "custo".** $f$ inclui $\beta x^2$ e $\rho\,\Delta x^2$, que são escolhas de modelagem, não energia paga. E eles punem justamente o Método Usual, que opera aos saltos (81% das horas com a bomba em exatamente 0% ou 100%):

| | Custo linear ($\sum c x + \gamma z$) | $\beta x^2$ | $\rho\,\Delta x^2$ | Total |
|---|---:|---:|---:|---:|
| Usual | 30.308 | 9.998 | 805 | 41.112 |
| Otimizado | 23.319 | 4.121 | 90 | 27.529 |

**b) Efeito de fim de horizonte.** Sem restrição sobre o volume final, o otimizador termina **todos** os reservatórios exatamente em $h^{\min}$ (60 / 225 / 32 / 780). O Usual termina com bem mais água (189 / 321 / 60 / 1943). O otimizado capta 20.662 m³ contra 27.745 m³ — parte da "economia" é só não reabastecer no fim.

**Comparação justa** (mesmo critério de volume final):

| Cenário | Economia em $f$ | Economia em energia linear |
|---|---:|---:|
| Como está | 33,0% | 23,1% |
| Com $I_{j,T} \ge I_{j,0}$ | 30,2% | 20,4% |
| Com $I_{j,T} \ge$ volume final do Usual | 26,8% | **17,3%** |

O último número é coerente com o artigo (Tabela 8: **19,05%** para a 4ª classe).

**Sugestão:** adicionar a restrição $I_{j,T} \ge I_{j,0}$ ao modelo (é comum em planejamento com horizonte finito) e reportar o custo **linear** de energia como métrica principal de economia.

### 2. As transferências nunca são usadas

Em todas as soluções, $z = 0$. Motivo: com os dados da 4ª classe, captar no próprio reservatório é sempre mais barato que captar em outro e transferir:

| Reservatório | Custo por m³ captado (fora da ponta) |
|---|---:|
| 1 | 100/70 = 1,43 |
| 2 | 100/120 = 0,83 |
| 3 | 130/107 = 1,21 |
| 4 | 800/750 = 1,07 |

Ex.: mandar água de 1 → 2 custa ≥ 1,43 + 3/70; o reservatório 2 capta por 0,83. Na prática, o problema se **separa em 4 problemas independentes** e a parte de rede do modelo fica inativa. O relatório não menciona isso. Vale comentar (é um resultado interessante) ou testar uma instância onde transferências compensem (ex.: 5ª ou 6ª classe, Tabelas 4–6 do artigo).

### 3. Só uma instância foi resolvida

O enunciado pede "algumas instâncias". Hoje há uma única (semente 42, $\theta = 10\%$). Sugestões baratas, já que o código roda em ~3 s:

- $\theta \in \{0\%, 10\%, 20\%\}$ (espelha os Experimentos 1–3 do artigo);
- algumas sementes diferentes para a demanda;
- sensibilidade a $\beta$ e $\rho$ (valores hoje sem justificativa);
- opcional: 5ª e 6ª classes.

### 4. Lagrangeano Aumentado: texto contradiz a implementação

O relatório diz que o método "permite obter convergência exata **sem exigir que $\rho_k \to \infty$**". Mas o código ([linha 249](../src/main.py#L249)) multiplica $\rho$ por 3 **toda** iteração, sem condição. Na execução, $\rho$ vai de 20 a **393.660**.

**Correção:** aumentar $\rho$ só quando a violação não cai o suficiente, que é a regra clássica:

```python
if viol_m3 > 0.5 * viol_anterior:
    pen_rho = min(pen_rho * 3.0, 1e6)
```

Também: o critério de parada só olha viabilidade (não otimalidade), e `res_sub.success` nunca é verificado.

---

## Prioridade média — relatório

| # | Problema | Onde | Correção |
|---|---|---|---|
| 5 | Nome do script errado: `saae_sao_carlos_nl.py` | Relatório §4 e README | `src/main.py`. O README também cita a pasta `relatorio/` (não existe) e tem placeholders nos integrantes |
| 6 | "Comportamento idêntico ao Experimento 8" | §4 | Não há comparação direta. Comparar com a Tabela 8 do artigo (19,05%) ou retirar |
| 7 | Demanda "seguindo a Seção 4.1 do artigo" | §2 | Os fatores 25/55/60/50% e o 0,65·$v_j$ foram **inventados pelo grupo**. Dizer isso explicitamente |
| 8 | "LA é 3,2× mais rápido" | §4 | Comparação frágil: precisões diferentes (SLSQP ~$10^{-10}$ m³, LA ~$10^{-5}$ m³), execução única, BLAS multithread. Suavizar a afirmação |
| 9 | Números não batem exatamente ao rodar | Tabela 3 | Obtive 10 iterações externas (não 11) e violações 9,7e-10 / 6,9e-5. Custos idênticos. Informar versões/máquina ou arredondar |
| 10 | Índices inconsistentes | Eq. (1) vs (2)–(3) | Eq. (1) usa $t$ a partir de 0 ($(1-\theta)^{t+1}$, $s = 0..t$); o resto usa $t = 1..T$. Padronizar |
| 11 | $\delta^+(j)$ e $\delta^-(j)$ não definidos | Eq. (1) | Definir (arestas que saem / entram em $j$) |
| 12 | "Penalidades elevadas de acionamento" do Usual | §4 | Essas penalidades são os termos artificiais $\beta$/$\rho$ do **nosso** modelo (ver item 1) |
| 13 | $\beta x^2$ como "perda de carga" | §2 | Simplificação aceitável, mas pelas leis de afinidade a potência cresce ~cubicamente com a rotação. Apresentar como escolha de modelagem convexa |
| 14 | Métodos não vistos em aula pouco explicados | §3 | O enunciado exige explicar aplicabilidade, funcionamento e teorema de convergência. L-BFGS-B (usado nos subproblemas) nem é explicado |
| 15 | Referências incompletas | Referências | Nocedal & Wright é citado no texto mas não listado. Faltam Kraft (1988, SLSQP) e Byrd et al. (1995, L-BFGS-B). Só o Gemini aparece como IA — se o Claude foi usado no relatório, o enunciado exige citar |
| 16 | Falta um gráfico | §4 | Volume × tempo (Usual vs. Otimizado), como as Fig. 11–13 do artigo. Deixaria visíveis o enchimento antes da ponta e o efeito de fim de horizonte |

### 17. Justificativa do termo de suavização $\rho\,(x_{jt} - x_{j,t-1})^2$

O relatório (§2) apresenta o termo como substituto do custo de acionamento do artigo. Não é fiel. O artigo cobra só ao **ligar**, e só a partir de "desligada". O termo atual cobra subidas **e** descidas, e qualquer variação, como 0,40 → 0,45.

Na prática, a simetria quase não importa. Resolvi com SLSQP três variantes:

| Variante | Custo linear | Uso médio na ponta | Maior queda em 1 h |
|---|---:|---:|---:|
| Simétrica (atual) | 23.319 | 20,3% | 0,99 |
| Só subida, $\rho\max(0,\Delta x)^2$ | 23.248 | 17,7% | 1,00 |
| Sem suavização | 23.233 | 17,5% | 1,00 |

A diferença é de cerca de 0,3%. A tarifa dobrada da ponta domina a penalidade (ρ = 15), e o uso residual na ponta vem do $\beta x^2$ e das perdas, não da suavização.

**Recomendação:** **manter o termo simétrico** e mudar a redação. Em vez de "substitui o custo de acionamento", apresentá-lo como **penalidade de variação de rotação** (desgaste do conjunto motor-bomba e golpe de aríete, que ocorre justamente em paradas bruscas), um regularizador que suaviza as rampas. Dizer explicitamente que nenhuma versão contínua reproduz o custo de acionamento discreto do artigo.

Por que não usar a versão só na subida: ela tem derivada primeira contínua, mas a segunda não. Isso contradiz a afirmação de que o objetivo é de classe $C^\infty$ e enfraquece as hipóteses do teorema de convergência do SLSQP, sem ganho prático.

### 18. "Variáveis contínuas" não é o que elimina as binárias

A adaptação 1 do relatório (§2, "Variáveis contínuas de vazão") dá a entender que o controle das bombas passou a ser contínuo por causa da adaptação. No artigo, porém, $x_{jt}$ e $z_{jlt}$ **já são contínuos** em $[0,1]$ (fração da hora ligada). As binárias $y$ e $\alpha$ são auxiliares e só servem para cobrar o custo de acionamento.

**Correção de redação:** deixar claro que:

- as binárias somem porque o **custo de acionamento** foi substituído pelo termo $\rho\,\Delta x^2$ (adaptação 2);
- a reinterpretação de $x$ como fração de vazão (inversor de frequência) serve para justificar fisicamente o termo $\beta x^2$, e não para tornar $x$ contínuo.

---

## Prioridade baixa — código

- **`check_grad` assusta à toa:** imprime erro absoluto 1,5e-3. O erro **relativo** é 3e-7 (gradiente correto). Imprimir o relativo.
- **Avaliação dupla:** `fun` e `jac` são lambdas separadas que chamam `objetivo_e_gradiente` duas vezes ([179–181](../src/main.py#L179-L181), [225–227](../src/main.py#L225-L227)). Usar `jac=True` e passar a função que devolve `(f, grad)`. Afeta a comparação de tempo.
- **Script monolítico:** tudo em variáveis globais. Encapsular a instância numa função `(seed, theta, beta, rho)` facilita o item 3.

---

## O que está correto (verificado)

- Dados das Tabelas 2 e 3 conferem com o artigo; arestas 1→2, 3→2, 3→4, 4→3 conferem com a Figura 9.
- Índices da ponta (períodos 19–21 e 43–45) corretos.
- Matriz de balanço reproduz a Eq. (1) do artigo, com perda aplicada a $I_{j,t-1}$.
- Gradiente do objetivo, jacobianas das restrições e gradiente do Lagrangeano Aumentado estão corretos.
- A afirmação de convexidade estrita é verdadeira, e SLSQP e LA concordam até 6 casas — boa evidência de que ambos acharam o ótimo global.

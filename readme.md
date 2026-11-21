# Otimização Não-Linear Contínua no Abastecimento de Água (SAAE São Carlos)

Trabalho da disciplina **SME0212 / SME5720 — Otimização Não-Linear** (ICMC-USP, 2º semestre de 2026).

## Sobre o projeto

Este repositório implementa uma adaptação contínua e não-linear do modelo de planejamento da operação de bombas de captação e transferência de água proposto por [Soler et al. (2016)](https://www.scielo.br/j/prod/a/BXCWkj9kC8mMgJF3QP9T9Sm/?lang=pt) para o sistema de abastecimento do **SAAE de São Carlos (SP)** (4ª classe de exemplares: 4 reservatórios, horizonte de 48 horas).

Para adequar o problema original (PLIM) à otimização não-linear contínua:
- As variáveis binárias de acionamento foram removidas, passando as bombas a operar continuamente em $[0, 1]$.
- A função objetivo incorpora perda de carga quadrática ($\beta x^2$) e suavização temporal ($\rho \Delta x^2$).
- Os volumes dos reservatórios são expressos diretamente em função das vazões bombeadas via matriz de balanço de massa com perdas horárias ($\theta = 10\%$).

## Formulação Matemática

### Função objetivo minimizada

$$
\min_{x, z} \; f(x, z) = \sum_{t=1}^{T} \sum_{j=1}^{R} \Big[ c_{jt}\big(x_{jt} + \beta x_{jt}^2\big) + \rho \big(x_{jt} - x_{j,t-1}\big)^2 \Big] + \sum_{t=1}^{T} \sum_{e=1}^{E} \gamma_{et}\big(z_{et} + \beta z_{et}^2\big)
$$

onde $x_{jt} \in [0, 1]$ é a fração de vazão da bomba de captação do reservatório $j$ na hora $t$, $z_{et} \in [0, 1]$ é a fração de vazão da bomba de transferência $e$ na hora $t$, $\beta = 0{,}35$ modela a perda de carga hidráulica e $\rho = 15{,}0$ suaviza variações bruscas entre horas consecutivas ($x_{j,0} = 0$).

### Restrições

Eliminando os estoques $I_{jt}$ recursivamente a partir do volume inicial $I_{j,0}$ com taxa de perda $\theta = 0{,}10$:

$$
I_{jt}(x, z) = (1 - \theta)^{t+1} I_{j,0} + \sum_{s=0}^{t} (1 - \theta)^{t-s} \left( v_j x_{js} - \sum_{e \in \delta^+(j)} w_e z_{es} + \sum_{e \in \delta^-(j)} w_e z_{es} - d_{js} \right)
$$

O problema fica sujeito apenas aos limites de capacidade dos reservatórios e aos limites operacionais das bombas:

$$
h_j^{\min} \le I_{jt}(x, z) \le h_j^{\max}, \quad \forall j \in \{1, \dots, R\},\; t \in \{1, \dots, T\}
$$

$$
0 \le x_{jt} \le 1, \quad 0 \le z_{et} \le 1, \quad \forall j, e, t
$$

## Dados Utilizados (4ª Classe — SAAE São Carlos)

Os parâmetros abaixo foram extraídos das **Tabelas 2 e 3** de [Soler et al. (2016)](https://www.scielo.br/j/prod/a/BXCWkj9kC8mMgJF3QP9T9Sm/?lang=pt), considerando horário de ponta entre 18h e 21h (períodos $19, 20, 21$ e $43, 44, 45$).

### Tabela 2 — Reservatórios e bombas de captação

| Reservatório ($j$) | $h_j^{\min}$ ($\text{m}^3$) | $h_j^{\max}$ ($\text{m}^3$) | $I_{j,0}$ ($\text{m}^3$) | Vazão $v_j$ ($\text{m}^3/\text{h}$) | Custo Fora Ponta | Custo Ponta |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| Reservatório 1 | 60 | 200 | 100 | 70 | 100 | 200 |
| Reservatório 2 | 225 | 750 | 375 | 120 | 100 | 200 |
| Reservatório 3 | 32 | 106 | 53 | 107 | 130 | 260 |
| Reservatório 4 | 780 | 2600 | 1300 | 750 | 800 | 1600 |

### Tabela 3 — Bombas de transferência entre reservatórios

| Ligação ($j \to l$) | Vazão máxima $w_{jlt}$ ($\text{m}^3/\text{h}$) | Custo por período $\gamma_{jlt}$ |
| :--- | ---: | ---: |
| Reservatório $1 \to 2$ | 70 | 3 |
| Reservatório $3 \to 2$ | 40 | 15 |
| Reservatório $3 \to 4$ | 80 | 3 |
| Reservatório $4 \to 3$ | 80 | 30 |

## Estrutura do repositório

- `saae_sao_carlos_nl.py`: script principal com os dados das Tabelas 2 e 3, formulação matricial, validação do gradiente (`check_grad`), resolução pelos dois métodos e comparação com o Método Usual.
- `requirements.txt`: dependências Python do projeto.
- `relatorio/`: pasta sugerida para o relatório em PDF e gráficos gerados.

## Como executar

1. Crie e ative um ambiente virtual (opcional):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # .venv\Scripts\activate   # Windows
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Execute o script:
   ```bash
   python3 saae_sao_carlos_nl.py
   ```

## Resultados principais (4ª classe — 48h, $\theta = 10\%$)

| Abordagem | Custo Total | Violação Máx. | Tempo |
| :--- | ---: | ---: | ---: |
| Método Usual (sem otimização) | 41.111,80 | 9,09e-13 m³ | — |
| `SLSQP` (SciPy) | 27.529,21 | 2,73e-11 m³ | 2,280 s |
| Lagrangeano Aumentado (`L-BFGS-B`) | 27.529,21 | 4,13e-05 m³ | 0,716 s |

Economia obtida com a otimização: **33,04%** de redução no custo total em relação ao Método Usual.

## Integrantes do grupo

- [Nome Completo 1 — Nº USP]
- [Nome Completo 2 — Nº USP]
- [Nome Completo 3 — Nº USP]
- [Nome Completo 4 — Nº USP]

## Referência

SOLER, E. M.; TOLEDO, F. M. B.; SANTOS, M. O.; ARENALES, M. N. **Otimização dos custos de energia elétrica na programação da captação, armazenamento e distribuição de água**. *Production*, v. 26, n. 2, p. 385-401, 2016. Disponível em: [SciELO](https://www.scielo.br/j/prod/a/BXCWkj9kC8mMgJF3QP9T9Sm/?lang=pt).

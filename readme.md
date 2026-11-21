# Otimização Não-Linear Contínua no Abastecimento de Água (SAAE São Carlos)

Trabalho da disciplina **SME0212 / SME5720 — Otimização Não-Linear** (ICMC-USP, 2º semestre de 2026).

## Sobre o projeto

Este repositório implementa uma adaptação contínua e não-linear do modelo de planejamento da operação de bombas de captação e transferência de água proposto por [Soler et al. (2016)](https://www.scielo.br/j/prod/a/BXCWkj9kC8mMgJF3QP9T9Sm/?lang=pt) para o sistema de abastecimento do **SAAE de São Carlos (SP)** (4ª classe de exemplares: 4 reservatórios, horizonte de 48 horas).

Para adequar o problema original (PLIM) à otimização não-linear contínua:

- As variáveis binárias de acionamento foram removidas, passando as bombas a operar continuamente em $[0, 1]$.
- A função objetivo incorpora perda de carga quadrática ($\beta x^2$) e suavização temporal ($\rho \Delta x^2$).
- Os volumes dos reservatórios são expressos diretamente em função das vazões bombeadas via matriz de balanço de massa com perdas horárias ($\theta = 10\%$).

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

| Abordagem                            | Custo Total | Violação Máx. |  Tempo |
| :----------------------------------- | ----------: | ---------------: | -----: |
| Método Usual (sem otimização)     |   41.111,80 |     9,09e-13 m³ |     — |
| `SLSQP` (SciPy)                    |   27.529,21 |     1,10e-11 m³ | ~4,7 s |
| Lagrangeano Aumentado (`L-BFGS-B`) |   27.529,21 |     9,74e-05 m³ | ~0,4 s |

Economia obtida com a otimização: **33,04%** de redução no custo total em relação ao Método Usual.

## Integrantes do grupo

- Davi Nascimento Pereira - 16906368

## Referência

SOLER, E. M.; TOLEDO, F. M. B.; SANTOS, M. O.; ARENALES, M. N. **Otimização dos custos de energia elétrica na programação da captação, armazenamento e distribuição de água**. *Production*, v. 26, n. 2, p. 385-401, 2016. Disponível em: [SciELO](https://www.scielo.br/j/prod/a/BXCWkj9kC8mMgJF3QP9T9Sm/?lang=pt).

"""
Modelo Não-Linear Contínuo Adaptado — SAAE São Carlos (4ª Classe, 4 Reservatórios)
Baseado em Soler et al. (2016), Production, v. 26, n. 2, pp. 385-401.
DOI: https://doi.org/10.1590/0103-6513.146113

Este código resolve o problema de planejamento da operação de bombas hidráulicas
ao longo de 48 horas usando dois métodos de otimização não-linear contínua:
  1. SLSQP (Sequential Least Squares Programming) da biblioteca SciPy.
  2. Lagrangeano Aumentado implementado passo a passo (subproblemas via L-BFGS-B).
Também simula o "Método Usual" (Seção 4.5 do artigo, sem otimização) para
comparar os gastos com energia elétrica com e sem otimização.
"""

import time                            # Biblioteca padrão para medir o tempo de execução
import numpy as np                     # Biblioteca para manipulação eficiente de vetores e matrizes
from scipy.optimize import minimize    # Função principal de otimização do SciPy
from scipy.optimize import check_grad  # Ferramenta para validar o gradiente analítico

# ==============================================================================
# 1. DADOS DA 4ª CLASSE DE SÃO CARLOS (Tabelas 2 e 3 de Soler et al., 2016)
# ==============================================================================
R = 4   # Número total de reservatórios do sistema (4ª classe)
T = 48  # Horizonte de planejamento em horas (2 dias completos = 48 períodos)

# Tabela 2: Parâmetros físicos dos 4 reservatórios (índices 0, 1, 2, 3)
h_min = np.array([60.0, 225.0, 32.0, 780.0])       # Volume mínimo de segurança (m3)
h_max = np.array([200.0, 750.0, 106.0, 2600.0])    # Capacidade máxima física (m3)
I_0   = np.array([100.0, 375.0, 53.0, 1300.0])     # Volume inicial em t = 0 (m3)
v_cap = np.array([70.0, 120.0, 107.0, 750.0])      # Vazão máxima da bomba de captação (m3/h)

# Tabela 2: Custo de manter a bomba de captação ligada por 1 hora (tarifa azul)
c_fora_ponta = np.array([100.0, 100.0, 130.0, 800.0])   # Custo fora do horário de ponta
c_ponta      = np.array([200.0, 200.0, 260.0, 1600.0])  # Custo no horário de ponta (dobro)

# Conjunto dos índices (0-based) que correspondem às 18h-21h nos dois dias:
# Dia 1: horas 19, 20, 21 (índices 18, 19, 20) | Dia 2: horas 43, 44, 45 (índices 42, 43, 44)
ponta_idx = {18, 19, 20, 42, 43, 44}
c_cap = np.zeros((R, T))               # Cria matriz (4 x 48) preenchida com zeros
for t in range(T):                     # Percorre cada uma das 48 horas
    if t in ponta_idx:                 # Verifica se a hora t pertence ao horário de ponta
        c_cap[:, t] = c_ponta          # Atribui a tarifa cara (ponta) na coluna t
    else:                              # Caso contrário, é horário normal
        c_cap[:, t] = c_fora_ponta     # Atribui a tarifa normal (fora de ponta) na coluna t

# Tabela 3: Ligações de transferência entre reservatórios (pares origem -> destino, 0-based)
# 1->2 vira (0,1), 3->2 vira (2,1), 3->4 vira (2,3), 4->3 vira (3,2)
transf_edges = [(0, 1), (2, 1), (2, 3), (3, 2)]
E = len(transf_edges)                  # Quantidade de tubulações de transferência (E = 4)
w_transf = np.array([70.0, 40.0, 80.0, 80.0])    # Vazão máxima de transferência (m3/h)
gamma_base = np.array([3.0, 15.0, 3.0, 30.0])    # Custo de energia por hora de transferência
gamma = np.repeat(gamma_base[:, None], T, axis=1)  # Repete o custo para as 48 horas (matriz 4 x 48)

# Parâmetros de perda de água e da adaptação não-linear contínua
theta = 0.10                           # Taxa de perda/vazamento por hora (10%, Experimento 8)
beta = 0.35                            # Peso do termo quadrático (perda de carga hidráulica)
rho  = 15.0                            # Peso da penalidade de variação brusca entre horas
x_init_prev = np.zeros(R)              # Estado inicial das bombas antes de t=1 (todas desligadas)

# ==============================================================================
# 2. PERFIL DE DEMANDA HORÁRIA (48h)
# ==============================================================================
rng = np.random.default_rng(42)        # Gerador aleatório com semente fixa (reprodutibilidade)
hora_dia = np.arange(T) % 24           # Converte t=0..47 na hora do dia (0..23)
fator_horario = np.where(              # Define multiplicador de consumo por faixa do dia:
    (hora_dia >= 0) & (hora_dia < 6), 0.25,     # Madrugada: 25% (consumo baixo)
    np.where((hora_dia >= 6) & (hora_dia < 12), 0.55,  # Manhã: 55%
    np.where((hora_dia >= 12) & (hora_dia < 18), 0.60, # Tarde: 60% (pico diurno)
             0.50))                                    # Noite: 50%
)
d = np.zeros((R, T))                   # Inicializa matriz de demandas d_{j,t} (4 x 48)
for j in range(R):                     # Para cada reservatório j:
    ruido = rng.uniform(0.92, 1.08, size=T)       # Sorteia variação aleatória de +/- 8%
    d[j, :] = 0.65 * v_cap[j] * fator_horario * ruido  # Calibra demanda pela vazão da bomba

# ==============================================================================
# 3. VETOR ÚNICO DE DECISÃO E MATRIZ DE BALANÇO DE MASSA
# ==============================================================================
N_x = R * T                            # Total de variáveis de captação x (4 * 48 = 192)
N_z = E * T                            # Total de variáveis de transferência z (4 * 48 = 192)
N = N_x + N_z                          # Dimensão total do vetor de decisão u (N = 384)

def unpack(u):
    """Separa o vetor 1D u (384) nas matrizes 2D x (4x48) e z (4x48)."""
    x = u[:N_x].reshape((R, T))        # Primeiras 192 posições formam a matriz x
    z = u[N_x:].reshape((E, T))        # Últimas 192 posições formam a matriz z
    return x, z                        # Retorna as duas matrizes

# Eliminamos as variáveis de estoque I_{j,t} escrevendo I = b_const + M_bal @ u
M_bal = np.zeros((R * T, N))           # Matriz de coeficientes (192 linhas x 384 colunas)
b_const = np.zeros(R * T)              # Termo constante (192 posições: estoque inicial - demandas)

for j in range(R):                     # Percorre cada reservatório j (0..3)
    for t in range(T):                 # Percorre cada período t (0..47)
        row = j * T + t                # Índice da linha correspondente a (j, t)
        # Volume inicial I_0[j] após sofrer (t + 1) horas seguidas de perda (1 - theta)
        b_const[row] = ((1.0 - theta) ** (t + 1)) * I_0[j]
        for s in range(t + 1):         # Soma as entradas e saídas desde s = 0 até s = t
            decay = (1.0 - theta) ** (t - s)  # Fator de decaimento por vazamento até a hora t
            b_const[row] -= decay * d[j, s]   # Subtrai a demanda consumida na hora s
            M_bal[row, j * T + s] += decay * v_cap[j]  # Soma captação da própria bomba j em s
            for e_idx, (orig, dest) in enumerate(transf_edges):  # Percorre transferências
                col_z = N_x + e_idx * T + s   # Índice da variável z_{e,s} no vetor u
                if orig == j:                 # Se a água SAI do reservatório j:
                    M_bal[row, col_z] -= decay * w_transf[e_idx]  # Subtrai do estoque de j
                if dest == j:                 # Se a água ENTRA no reservatório j:
                    M_bal[row, col_z] += decay * w_transf[e_idx]  # Soma ao estoque de j

h_min_vec = np.repeat(h_min, T)        # Repete h_min 48 vezes para comparar com I (192)
h_max_vec = np.repeat(h_max, T)        # Repete h_max 48 vezes para comparar com I (192)

# Escalonamento numérico: coloca função objetivo e restrições na ordem de ~1.0
f_scale = 1000.0                       # Divisor da função objetivo
M_bal_scaled = M_bal / h_max_vec[:, None]  # Divide cada linha de M_bal pelo respectivo h_max

# ==============================================================================
# 4. FUNÇÃO OBJETIVO, GRADIENTE ANALÍTICO E AVALIAÇÃO DE ESTOQUE
# ==============================================================================
def objetivo_e_gradiente(u):
    """Calcula o custo total f(u) e o vetor gradiente exato grad_f(u)."""
    x, z = unpack(u)                   # Desempacota o vetor u nas matrizes x e z

    # 1) Custo das bombas de captação: sum c_{j,t} * (x_{j,t} + beta * x_{j,t}^2)
    f_cap = np.sum(c_cap * (x + beta * x**2))
    # Derivada parcial em relação a x_{j,t}: c_{j,t} * (1 + 2 * beta * x_{j,t})
    grad_x = c_cap * (1.0 + 2.0 * beta * x)

    # 2) Penalidade de suavização temporal: sum rho * (x_{j,t} - x_{j,t-1})^2
    diff_0 = x[:, 0] - x_init_prev     # Diferença na primeira hora (t = 0)
    diff_t = x[:, 1:] - x[:, :-1]      # Diferenças entre horas consecutivas (t >= 1)
    f_smooth = rho * (np.sum(diff_0**2) + np.sum(diff_t**2))

    # Regra da cadeia para a suavização no gradiente de x:
    grad_x[:, 0] += 2.0 * rho * diff_0     # Contribuição de (x_{j,0} - x_init)^2
    grad_x[:, 1:] += 2.0 * rho * diff_t    # Contribuição com sinal (+) para t
    grad_x[:, :-1] -= 2.0 * rho * diff_t   # Contribuição com sinal (-) para t-1

    # 3) Custo das bombas de transferência: sum gamma_{e,t} * (z_{e,t} + beta * z_{e,t}^2)
    f_transf = np.sum(gamma * (z + beta * z**2))
    # Derivada parcial em relação a z_{e,t}: gamma_{e,t} * (1 + 2 * beta * z_{e,t})
    grad_z = gamma * (1.0 + 2.0 * beta * z)

    f_total = f_cap + f_smooth + f_transf  # Soma os três componentes do custo total
    grad_total = np.concatenate([grad_x.ravel(), grad_z.ravel()])  # Junta tudo em 1D (384)
    return f_total, grad_total         # Retorna valor escalar e vetor gradiente

def volume_reservatorios(u):
    """Calcula o vetor de estoques I (192 posições) para qualquer vetor de operação u."""
    return b_const + M_bal @ u         # Produto matriz-vetor linear

bounds = [(0.0, 1.0)] * N              # Limites de caixa: cada bomba opera entre 0% e 100%
u0 = np.full(N, 0.35)                  # Chute inicial: todas as bombas começam em 35%

# Validação automática do gradiente analítico contra diferenças finitas
erro_grad = check_grad(
    lambda u: objetivo_e_gradiente(u)[0],
    lambda u: objetivo_e_gradiente(u)[1],
    u0
)
print(f"Verificação do gradiente (check_grad): erro = {erro_grad:.2e}")

# ==============================================================================
# 5. MÉTODO 1: SLSQP (Sequential Least Squares Programming)
# ==============================================================================
t0 = time.perf_counter()               # Marca o instante inicial
constraints_slsqp = [
    {
        "type": "ineq",                # No SciPy, "ineq" exige que fun(u) >= 0
        "fun": lambda u: (volume_reservatorios(u) - h_min_vec) / h_max_vec,  # I >= h_min
        "jac": lambda u: M_bal_scaled, # Jacobiana exata da restrição inferior
    },
    {
        "type": "ineq",                # Segunda restrição: h_max - I >= 0 (ou seja, I <= h_max)
        "fun": lambda u: (h_max_vec - volume_reservatorios(u)) / h_max_vec,
        "jac": lambda u: -M_bal_scaled,# Jacobiana exata com sinal negativo
    },
]

res_slsqp = minimize(
    lambda u: objetivo_e_gradiente(u)[0] / f_scale,  # Função objetivo escalada
    u0,                                              # Ponto inicial
    jac=lambda u: objetivo_e_gradiente(u)[1] / f_scale,  # Gradiente escalado
    method="SLSQP",                                  # Algoritmo de Programação Quadrática Sequencial
    bounds=bounds,                                   # Limites 0 <= u_i <= 1
    constraints=constraints_slsqp,                   # Lista de restrições de desigualdade
    options={"ftol": 1e-8, "maxiter": 600, "disp": False},  # Critério de parada
)
tempo_slsqp = time.perf_counter() - t0 # Calcula tempo gasto pelo SLSQP
f_slsqp = res_slsqp.fun * f_scale      # Desfaz a escala para obter o custo real

# ==============================================================================
# 6. MÉTODO 2: LAGRANGEANO AUMENTADO (Implementação Própria)
# ==============================================================================
t0 = time.perf_counter()               # Marca o instante inicial
u_aug = u0.copy()                      # Copia o chute inicial para não alterar u0
lam1 = np.zeros(R * T)                 # Multiplicadores de Lagrange para g1 = (h_min - I)/h_max <= 0
lam2 = np.zeros(R * T)                 # Multiplicadores de Lagrange para g2 = (I - h_max)/h_max <= 0
pen_rho = 20.0                         # Parâmetro inicial de penalidade quadrática
hist_aug = []                          # Lista para guardar histórico (iteração, custo, violação)

for k in range(25):                    # Laço externo: no máximo 25 atualizações de multiplicadores
    def aug_lag_and_grad(u):
        """Monta o Lagrangeano Aumentado e seu gradiente para o subproblema k."""
        f_val, g_f = objetivo_e_gradiente(u)  # Avalia custo original e gradiente
        f_val_s = f_val / f_scale             # Escala o valor da função objetivo
        g_f_s = g_f / f_scale                 # Escala o vetor gradiente

        I_vec = volume_reservatorios(u)       # Calcula volumes atuais dos reservatórios
        g1 = (h_min_vec - I_vec) / h_max_vec  # Restrição inferior na forma g1 <= 0
        g2 = (I_vec - h_max_vec) / h_max_vec  # Restrição superior na forma g2 <= 0

        # Termos ativos de Rockafellar-Wets: só penalizam onde lam + pen_rho * g > 0
        s1 = np.maximum(0.0, lam1 + pen_rho * g1)
        s2 = np.maximum(0.0, lam2 + pen_rho * g2)

        # Valor do Lagrangeano Aumentado L(u, lam1, lam2; pen_rho)
        L_val = f_val_s + (0.5 / pen_rho) * (
            np.sum(s1**2 - lam1**2) + np.sum(s2**2 - lam2**2)
        )
        # Gradiente exato de L usando a regra da cadeia (nabla g1 = -M, nabla g2 = +M)
        grad_L = g_f_s + M_bal_scaled.T @ (s2 - s1)
        return L_val, grad_L

    # Resolve o subproblema apenas com limites de caixa [0, 1] usando L-BFGS-B
    res_sub = minimize(
        lambda u: aug_lag_and_grad(u)[0],     # Função do subproblema
        u_aug,                                # Warm start: parte da solução anterior
        jac=lambda u: aug_lag_and_grad(u)[1], # Gradiente do subproblema
        method="L-BFGS-B",                    # Método quase-Newton limitado à caixa
        bounds=bounds,                        # Limites 0 <= u_i <= 1
        options={"ftol": 1e-11, "gtol": 1e-8, "maxiter": 400},
    )
    u_aug = res_sub.x                  # Atualiza o ponto corrente com a solução do subproblema

    I_cur = volume_reservatorios(u_aug)       # Recalcula volumes na solução atual
    g1_cur = (h_min_vec - I_cur) / h_max_vec  # Avalia g1 escalado
    g2_cur = (I_cur - h_max_vec) / h_max_vec  # Avalia g2 escalado

    # Mede a maior violação física de volume (em m3)
    viol_m3 = max(0.0, np.max(h_min_vec - I_cur), np.max(I_cur - h_max_vec))
    f_cur, _ = objetivo_e_gradiente(u_aug)    # Calcula o custo real sem penalidade
    hist_aug.append((k + 1, f_cur, viol_m3))  # Registra a iteração externa no histórico

    # Atualiza os multiplicadores de Lagrange projetados no ortante não-negativo
    lam1 = np.maximum(0.0, lam1 + pen_rho * g1_cur)
    lam2 = np.maximum(0.0, lam2 + pen_rho * g2_cur)

    if viol_m3 < 1e-4:                 # Critério de parada: violação menor que 0,0001 m3
        break                          # Encerra o laço externo
    pen_rho = min(pen_rho * 3.0, 1e6)  # Aumenta a penalidade para forçar viabilidade

tempo_aug = time.perf_counter() - t0   # Calcula tempo total do Lagrangeano Aumentado

# ==============================================================================
# 7. SIMULAÇÃO DO MÉTODO USUAL (SEM OTIMIZAÇÃO — Seção 4.5 do artigo)
# ==============================================================================
def simular_metodo_usual():
    """
    Reproduz o procedimento prático sem planejamento (Seção 4.5 do artigo):
    - Fora da ponta: liga a bomba (x=1) se atingir o mínimo e mantém ligada até atingir o máximo.
    - Na ponta: desliga a bomba (x=0), a menos que o reservatório caia abaixo de h_min.
    """
    x_usual = np.zeros((R, T))         # Inicializa operação das bombas de captação (sem transferências)
    z_usual = np.zeros((E, T))         # No método usual, transferências ficam desligadas
    for j in range(R):                 # Simula cada reservatório de forma independente
        I_ant = I_0[j]                 # Começa com o volume inicial da Tabela 2
        bomba_ligada = False           # Estado inicial da bomba (desligada)
        for t in range(T):             # Percorre cada hora t = 0..47
            # Volume previsto se a bomba ficar desligada nesta hora
            I_sem_bomba = (1.0 - theta) * I_ant - d[j, t]
            if t in ponta_idx:         # Se estiver no horário de ponta (18h-21h):
                bomba_ligada = False   # Regra prática desliga a bomba no início/durante a ponta
                if I_sem_bomba < h_min[j]:  # Se for secar abaixo do mínimo de segurança:
                    # Liga apenas a fração necessária para segurar o reservatório em h_min
                    x_usual[j, t] = min(1.0, (h_min[j] - I_sem_bomba) / v_cap[j])
                else:
                    x_usual[j, t] = 0.0     # Caso contrário, permanece desligada
            else:                      # Fora do horário de ponta:
                if I_sem_bomba <= h_min[j]: # Se atingir ou cair abaixo do mínimo:
                    bomba_ligada = True     # Liga a bomba
                if bomba_ligada:       # Se a bomba estiver no ciclo de enchimento:
                    # Calcula quanto falta para encher até h_max sem transbordar
                    x_nec = (h_max[j] - I_sem_bomba) / v_cap[j]
                    if x_nec <= 1.0:   # Se atingir h_max ainda dentro desta hora:
                        x_usual[j, t] = max(0.0, x_nec)  # Enche até o máximo
                        bomba_ligada = False             # Desliga a bomba ao atingir h_max
                    else:
                        x_usual[j, t] = 1.0              # Mantém ligada em 100% na hora inteira
                else:
                    x_usual[j, t] = 0.0     # Se estiver esvaziando acima do mínimo, mantém desligada
            # Atualiza o estoque real ao final da hora t
            I_ant = (1.0 - theta) * I_ant + v_cap[j] * x_usual[j, t] - d[j, t]

    u_usual = np.concatenate([x_usual.ravel(), z_usual.ravel()])  # Empacota em vetor 1D (384)
    f_usual, _ = objetivo_e_gradiente(u_usual)  # Avalia na mesma função de custo do modelo
    return u_usual, f_usual            # Retorna a operação e o custo total sem otimização

u_usual, f_usual = simular_metodo_usual()  # Executa a simulação sem otimização

# ==============================================================================
# 8. COMPARAÇÃO FINAL: COM OTIMIZAÇÃO vs. SEM OTIMIZAÇÃO
# ==============================================================================
I_slsqp = volume_reservatorios(res_slsqp.x).reshape((R, T))  # Volumes finais do SLSQP
I_aug = volume_reservatorios(u_aug).reshape((R, T))          # Volumes finais do Lagr. Aumentado
I_usual = volume_reservatorios(u_usual).reshape((R, T))      # Volumes do Método Usual

viol_slsqp = max(0.0, np.max(h_min_vec - I_slsqp.ravel()), np.max(I_slsqp.ravel() - h_max_vec))
viol_aug = max(0.0, np.max(h_min_vec - I_aug.ravel()), np.max(I_aug.ravel() - h_max_vec))
viol_usual = max(0.0, np.max(h_min_vec - I_usual.ravel()), np.max(I_usual.ravel() - h_max_vec))

print("\n=== COMPARAÇÃO: SEM OTIMIZAÇÃO vs. COM OTIMIZAÇÃO (4ª CLASSE - 48h) ===")
print(f"Método Usual (Sem otim.)| Viol. máx: {viol_usual:.2e} m3 | Custo = {f_usual:,.2f}")
print(f"SLSQP (Com otim.)       | Status: {res_slsqp.success} | Iter: {res_slsqp.nit:2d} | "
      f"Viol. máx: {viol_slsqp:.2e} m3 | Custo = {f_slsqp:,.2f} | Tempo: {tempo_slsqp:.3f}s")
print(f"Lagrangeano Aumentado   | Iter ext: {len(hist_aug):2d}  | "
      f"Viol. máx: {viol_aug:.2e} m3 | Custo = {f_cur:,.2f} | Tempo: {tempo_aug:.3f}s")

economia_abs = f_usual - f_slsqp       # Economia absoluta em unidades monetárias
economia_pct = (economia_abs / f_usual) * 100.0  # Redução percentual de gastos
diff_rel = abs(f_slsqp - f_cur) / min(f_slsqp, f_cur) * 100.0  # Diferença entre os dois otimizadores

print(f"\nEconomia obtida com a otimização: {economia_abs:,.2f} ({economia_pct:.2f}% de redução)")
print(f"Diferença entre SLSQP e Lagrangeano Aumentado: {diff_rel:.6f}%")

x_opt, _ = unpack(res_slsqp.x if res_slsqp.success else u_aug)  # Extrai solução ótima
x_usu, _ = unpack(u_usual)                                      # Extrai solução usual
print("\nOperação média das bombas de captação (Fora Ponta -> Ponta):")
ponta_mask = np.array([t in ponta_idx for t in range(T)])       # Máscara das horas de ponta
for j in range(R):                                              # Compara os 4 reservatórios
    print(f"  Reservatório {j+1} | Otimizado: {x_opt[j, ~ponta_mask].mean()*100:5.1f}% -> "
          f"{x_opt[j, ponta_mask].mean()*100:5.1f}% | "
          f"Usual: {x_usu[j, ~ponta_mask].mean()*100:5.1f}% -> {x_usu[j, ponta_mask].mean()*100:5.1f}%")
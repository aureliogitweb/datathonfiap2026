# Datathon Passos Mágicos: risco de agravamento de defasagem

Análise de três ciclos da Pesquisa Extensiva do Desenvolvimento Educacional
(PEDE 2022 a 2024) da [Associação Passos Mágicos](https://passosmagicos.org.br/),
com modelo preditivo de risco e uma aplicação.

**1.661 alunos, 3.030 observações aluno/ano, 1.365 transições.**

**Aplicação publicada:** _(colar aqui a URL do Streamlit Cloud)_

---

## Os cinco achados

### 1. O programa funciona, e o resultado aguenta o teste mais duro

Entre os 468 alunos presentes nos três anos, a proporção em nível adequado
dobrou: passou de 32,7% para 65,2%. Olhando aluno por aluno, 58,8% melhoraram
e 10,3% pioraram.

O que torna isso defensável não é o número em si, mas o que ele resiste.
Apliquei os limites de Manski, ou seja, refiz a conta assumindo que
todos os 509 alunos que saíram do programa tivessem piorado. Mesmo nesse
cenário impossível de ser pior, a melhora entre ciclos continua em 9,4 pontos,
contra 10,1 observados. O piso do segundo ciclo (30,9%) já supera o resultado
efetivo do primeiro (30,8%).

### 2. O IAN não mede o que o nome sugere

O Indicador de Adequação ao Nível não é uma avaliação. Ele é a defasagem
recodificada em 10, 5 ou 2,5, num mapeamento fixo. E a defasagem, por sua vez,
é só `Fase menos Fase Ideal`, o que confere em 99,93% das linhas.

Indo mais fundo: 98,7% das pioras têm a mesma assinatura. O aluno ficou na
mesma fase enquanto a fase ideal avançou. Quem não é promovido piora em cerca
de 53% dos casos. Quem é promovido, em 0,3%.

Ou seja, o que a base chama de risco de defasagem é descompasso entre o
calendário da Passos Mágicos e o calendário escolar. Não é reprovação nem
queda de desempenho, e os dois fenômenos se mostraram praticamente
independentes.

### 3. Quem mais precisa de ajuda não sabe que precisa

| Quintil de desempenho | IDA real | Autoavaliação |
|---|---|---|
| 1 (o mais baixo) | 3,54 | 8,50 |
| 5 (o mais alto) | 8,85 | 8,92 |

A correlação entre os dois é de apenas 0,135. Alunos com desempenho 3,54 se
avaliam praticamente igual aos de 8,85.

Isso tem consequência prática direta: um programa que espera o aluno pedir
ajuda nunca vai alcançar o quintil de baixo. A busca precisa ser ativa.

### 4. A evasão é o problema mais grave, e dá para prever

Entre 25% e 30% dos alunos saem por ano. Em todo o painel, só 4 voltaram
depois de sumir. Na prática, quem sai não volta.

| Indicador | Prediz evasão | Prediz defasagem |
|---|---|---|
| IEG (engajamento) | p = 7e-14, o mais forte de todos | AUC 0,523, ou seja, nada |

São dois problemas diferentes e cada um precisa do seu próprio alerta. O
enunciado pede só o segundo, que por acaso é o de sinal mais fraco.

### 5. O programa beneficia mais quem já estava melhor

Partindo da mesma defasagem inicial de -2, alunos Ametista avançam 1,35 fase e
alunos Quartzo avançam 0,30.

Estou reportando como indício, não como conclusão fechada, porque são só 10 alunos
Quartzo nesse recorte. Mas se confirmar, é o achado mais importante para o
desenho do programa, já que contraria a missão de atender quem está em maior
vulnerabilidade.

---

## O modelo

O que ele prevê: `defasagem(t+1) < defasagem(t)`, ou seja, se a defasagem
do aluno vai piorar no ciclo seguinte. Acontece em 17,3% das transições, e a
taxa é idêntica nas duas janelas, o que é importante para a validação fazer
sentido.

Como validamos: treinamos com as transições de 2022 para 2023 e testamos
com as de 2023 para 2024. No ajuste de hiperparâmetros usamos GroupKFold por
RA, porque 468 alunos aparecem nas duas janelas e um sorteio aleatório
colocaria o mesmo aluno dos dois lados.

| Modelo | PR-AUC | IC 95% | Brier | PR-AUC na fase avançada |
|---|---|---|---|---|
| Random Forest | 0,657 | [0,589; 0,725] | 0,152 | 0,262 |
| XGBoost | 0,620 | [0,549; 0,694] | 0,100 | 0,234 |
| **Regressão logística (escolhido)** | 0,557 | [0,489; 0,630] | **0,107** | **0,326** |
| LightGBM | 0,525 | [0,452; 0,605] | 0,113 | 0,189 |
| Árvore de decisão | 0,410 | [0,352; 0,482] | 0,125 | 0,181 |
| Regra simples (só a fase) | 0,363 | [0,313; 0,422] | 0,116 | 0,084 |

Por que a logística, se o Random Forest tem PR-AUC maior? Porque o número
global engana. A taxa de eventos é 48,0% na fase inicial e 8,4% na avançada, e
só separar esses dois grupos já produz PR-AUC alto sem prever nada de fato. No
estrato de fase avançada, onde a regra de fase não ajuda e o modelo precisa
trabalhar, a ordem se inverte e a logística lidera com 0,326.

Como os intervalos de confiança se sobrepõem, valeu o critério que acabei definindo
antes de rodar: em empate estatístico, fica o mais simples e mais bem
calibrado.

Calibração. Brier de 0,107, com o previsto batendo com o observado em todos
os quintis. Quando o modelo diz 30%, cerca de 30% realmente agravam. Isso
importa porque o enunciado pede probabilidade, e a aplicação mostra um
percentual para quem vai decidir onde colocar recurso.

Ganho na prática. No estrato de fase avançada, olhando os 30 alunos de
maior risco, o modelo captura 22,0% dos casos contra 6,0% da regra simples.
São 3,7 vezes mais acertos com a mesma capacidade de atendimento.

O que mais protege é o IPV, com razão de chances de 0,46. Entre as coisas
que a instituição pode influenciar, é a de maior efeito.

---

## Como rodar

```bash
git clone <url-do-repositorio>
cd passos-magicos-datathon

python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# coloque a planilha PEDE em data/raw/. O nome não importa, porque o
# carregador acha qualquer .xlsx que estiver na pasta.
jupyter lab
```

Rode os notebooks na ordem 01, 02 e 03. O terceiro gera o arquivo do modelo que
a aplicação usa.

```bash
streamlit run app/streamlit_app.py
```

Para testar o modo em lote sem montar planilha, envie o `app/exemplo_turma.csv`. 
Há um arquivo gerado de exemplo nessa pasta, pode utilizar ele se quiser.
São 18 alunos fictícios com risco entre 0,8% e 47,3%.

Com anaconda: `conda env create -f environment.yml && conda activate passos-datathon`

---

## Estrutura do repositório

```
passos-magicos-datathon/
├── README.md
├── LICENSE
├── requirements.txt
├── environment.yml
├── config.yaml                      # semente, caminhos e faixas de validação
├── .gitignore
│
├── data/
│   ├── raw/                         # planilha original (não versionada)
│   ├── interim/                     # painel limpo e log de limpeza
│   └── processed/
│
├── notebooks/
│   ├── 01_qualidade_dados.ipynb     # auditoria: drift, zeros, contratos
│   ├── 02_eda_perguntas.ipynb       # as 11 perguntas do enunciado
│   └── 03_modelo_risco.ipynb        # entregável do modelo
│
├── src/
│   ├── data/
│   │   ├── load.py                  # junta as 3 abas num painel longo
│   │   ├── clean.py                 # limpeza com log auditável
│   │   └── validate.py              # contratos que falham cedo
│   ├── features/build.py            # variáveis e verificação de vazamento
│   ├── models/
│   │   ├── train.py                 # pipelines dos cinco modelos
│   │   └── evaluate.py              # PR-AUC, calibração, recall por faixa
│   └── analysis/eda_tecnica.py      # drift, VIF, shift, fluxo do painel
│
├── app/
│   ├── streamlit_app.py             # abas de lote, individual e documentação
│   ├── requirements.txt
│   ├── exemplo_turma.csv            # 18 alunos para testar
│   ├── README.md
│   └── artifacts/modelo_risco.joblib
│
├── reports/
│   ├── deck_gerencial.pptx
│   ├── figures/
│   └── *.csv                        # coeficientes, drift, shift
│
└── docs/
    ├── decisoes_tecnicas.md         # o que decidimos e o que mudamos de ideia
    └── quadro_hipoteses.csv         # 20 hipóteses com veredito
```

---

## Decisões que valem explicar

Vazamento. A cadeia `Fase + Fase Ideal` leva a `Defasagem`, que leva a
`IAN`, que compõe o `INDE` e vira `Pedra`. Tudo determinístico. Por isso IAN,
INDE e Pedra estão proibidos como preditores, e o `src/features/build.py`
levanta erro se algum entrar ou se qualquer variável passar de 0,9 de
correlação com o alvo. A maior que encontramos foi 0,308.

Percentil dentro de cada ano. O IPS vai de 7,50 para 5,00 e volta para
7,51 na corte fechada, com a mesma população. Isso é mudança no jeito de
calcular, não nos alunos. Usando percentil, o modelo fica imune a esse tipo de
deslocamento.

Zeros tratados caso a caso. No IAA existe uma lacuna na distribuição, sem
nenhum valor entre 0 e 1,7, e os zeros não persistem de um ano para o outro.
Isso é cara de não resposta, então viraram nulo. Já IEG e IDA têm distribuição
contínua e o zero ali é medida real, então ficaram como estão. A regra uniforme
que pensamos no começo teria jogado fora informação boa.

Sem SMOTE. Com 17,3% de eventos o problema não é falta de casos positivos,
é calibração. Casos sintéticos distorceriam justamente a probabilidade que
precisamos preservar.

Contratos de integridade. O `src/data/validate.py` confere chave única,
a invariante da defasagem, as faixas dos indicadores e a cobertura por ano.
Testamos cada um contra corrupção injetada de propósito, e todos falharam como
deveriam.

---

## O que estes dados não permitem afirmar

- Nada aqui é causal. A base não tem grupo de controle.
- A análise longitudinal só enxerga quem ficou. Entre 25% e 30% saem por ano.
- Não dá para separar não promoção pedagógica de administrativa.
- O IPP ficou de fora porque não existe em 2022. Testei e ele não faria
  diferença sobre o conjunto das variáveis.
- O modelo mede descompasso de calendário, não desempenho pedagógico.
- A régua de Fase Ideal mudou entre 2022 e 2023, quando ALFA passou de
  "2º e 3º ano" para "1º e 2º ano". Isso invalida comparar nível absoluto
  entre esses dois anos.

---

## O que recomendamos

| # | Recomendação | Por quê | Custo |
|---|---|---|---|
| 1 | Criar alerta de evasão por queda de engajamento | O sinal é forte e usa dado que já é coletado | Baixo |
| 2 | Fazer busca ativa no quintil de baixo | O aluno em dificuldade não se percebe em dificuldade | Médio |
| 3 | Padronizar o cálculo do IPS | A escala mudou entre ciclos sem a população mudar | Baixo |
| 4 | Revisar como as fases acompanham o ano escolar | Origem de 98,7% dos agravamentos medidos | Alto |
| 5 | Entender por que os alunos Quartzo recuperam menos | Contraria a missão de atender quem mais precisa | Médio |

---

## Sobre os dados

Os dados vieram da Associação Passos Mágicos para o Datathon da FIAP e estão
anonimizados. Não são versionados aqui, conforme o `.gitignore`.

O mapeamento real está no
`src/data/load.py`.

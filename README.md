# Datathon Passos Mágicos: risco de agravamento de defasagem

Análise de três ciclos da Pesquisa Extensiva do Desenvolvimento Educacional
(PEDE 2022 a 2024) da [Associação Passos Mágicos] (https://passosmagicos.org.br/).

1.661 alunos, 3.030 observações aluno/ano, 1.365 transições.

Aplicação publicada: https://aureliofase5.streamlit.app/

---

## Os cinco achados

### 1. O programa funciona

Entre os 468 alunos presentes nos três anos, a proporção em nível adequado
dobrou: passou de 32,7% para 65,2%. Olhando aluno por aluno, 58,8% melhoraram
e 10,3% pioraram.

O teste de Wilcoxon pareado dá p = 7,5e-35. Isso é medição direta dentro da
coorte, sem precisar estimar nada sobre quem saiu.

A comparação entre ciclos é mais delicada. A taxa de melhora sobe de 30,8%
para 40,9%, mas só enxergo quem ficou. Aplicando limites de Manski a cada
janela isoladamente, o intervalo é [21,5%; 51,7%] em 2022 para 2023 e
[30,9%; 55,4%] em 2023 para 2024. Como esses intervalos se sobrepõem, os dados
sozinhos não provam que o segundo ciclo foi melhor que o primeiro.

O que sustenta a comparação é a atrição ter sido parecida nos dois anos, 30,2%
e 24,6%. É uma suposição razoável.

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

| Indicador | Associação com evasão | Prediz defasagem |
|---|---|---|
| IEG (engajamento) | p = 7e-14, a mais forte de todas | AUC 0,523, ou seja, nada |

São dois problemas diferentes e cada um precisa do seu próprio alerta.
O enunciado pede só o segundo, que por acaso é o de sinal mais fraco.

Duas ressalvas. A comparação é univariada, sem controlar fase, idade ou
tempo de programa, então não construí um modelo de evasão de fato. E a Fase
8 corresponde ao ensino superior, onde sair pode significar concluir o
programa, não abandoná-lo. Um modelo de evasão precisaria excluir as fases
terminais.

### 5. O programa beneficia mais quem já estava melhor

Partindo da mesma defasagem inicial de -2, alunos Ametista avançam 1,35 fase e
alunos Quartzo avançam 0,30. É o efeito Mateus.

Reporto como indício, não como conclusão fechada, porque são só 10 alunos
Quartzo nesse recorte. Mas se confirmar, é o achado mais importante para o
desenho do programa, já que contraria a missão de atender quem está em maior
vulnerabilidade.

---

## O modelo

O que ele prevê: `defasagem(t+1) < defasagem(t)`, ou seja, se a defasagem
do aluno vai piorar no ciclo seguinte. Acontece em 17,3% das transições, e a
taxa é idêntica nas duas janelas, o que é importante para a validação fazer
sentido.

Como validei: treinei com as transições de 2022 para 2023 e testei
com as de 2023 para 2024. No ajuste de hiperparâmetros usei GroupKFold por
RA, porque 468 alunos aparecem nas duas janelas e um sorteio aleatório
colocaria o mesmo aluno dos dois lados.

| Modelo | PR-AUC | IC 95% | Brier | PR-AUC na fase avançada |
|---|---|---|---|---|
| Random Forest | 0,657 | [0,589; 0,725] | 0,152 | 0,262 |
| XGBoost | 0,620 | [0,549; 0,694] | 0,100 | 0,234 |
| Regressão logística (escolhido) | 0,557 | [0,489; 0,630] | 0,107 | 0,326 |
| LightGBM | 0,525 | [0,452; 0,605] | 0,113 | 0,189 |
| Árvore de decisão | 0,410 | [0,352; 0,482] | 0,125 | 0,181 |
| Regra simples (só a fase) | 0,363 | [0,313; 0,422] | 0,116 | 0,084 |

Por que a logística, se o Random Forest tem PR-AUC maior? Primeiro, porque
o número global engana. A taxa de eventos na janela de teste é 48,0% na fase
inicial e 8,4% na avançada (na base completa, que é a referência usada pelo
app, são 46,2% e 9,2%), e só separar esses dois grupos já produz PR-AUC alto
sem prever nada de fato. No estrato de fase avançada, onde o modelo precisa
realmente trabalhar, os números ficam 0,326 para a logística e 0,262 para o
Random Forest.

Mas seria desonesto chamar isso de vitória. A diferença pareada é +0,057, com
IC 95% de [-0,043; +0,157] e p = 0,25. Os modelos empatam. O que decidiu foi
o critério que defini antes de rodar: em empate estatístico, fica o mais
simples e mais bem calibrado. A logística atende aos dois.

Calibração. Brier de 0,107, com o previsto batendo com o observado em todos
os quintis. Quando o modelo diz 30%, cerca de 30% realmente agravam. Isso
importa porque o enunciado pede probabilidade, e a aplicação mostra um
percentual para quem vai decidir onde colocar recurso.

Ganho na prática. No estrato de fase avançada, entre os 30 alunos de maior
risco, o modelo captura 11 dos 50 casos reais, contra 3 da regra simples. São
oito alunos de diferença com a mesma capacidade de atendimento. O número é
pequeno em termos absolutos, então trato como indicação de ganho, não como
medida precisa.

O que mais protege: o IPV, com razão de chances de 0,46. Entre as coisas
que a instituição pode influenciar, é a de maior efeito.

Uma ressalva importante sobre o IPV. Ele é também o melhor preditor
isolado da promoção de fase (AUC 0,679), que é justamente a decisão que gera o
alvo. Não sei como o IPV é calculado nem se a coordenação o consulta ao
decidir promoções. Se consultar, o modelo estaria em parte reproduzindo uma
decisão que a instituição já toma olhando para a mesma variável. Não dá para
resolver isso com os dados disponíveis, e é a limitação mais séria do
modelo.

\---

## Como rodar

```bash
git clone https://github.com/aureliogitweb/datathonfiap2026
cd datathonfiap2026

python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# coloque a planilha PEDE em data/raw/. o carregador vai achar qualquer .xlsx que estiver na pasta.
jupyter lab
```

Rode os notebooks na ordem 01, 02 e 03. O terceiro gera o arquivo do modelo que
a aplicação usa.

```bash
streamlit run app/streamlit\_app.py
```

Para testar o modo em lote sem montar planilha, envie o `app/exemplo\_turma.csv`.
São 18 alunos fictícios com risco entre 0,8% e 47,3%.

conda: `conda env create -f environment.yml && conda activate passos-datathon`

\---

## Estrutura do repositório

```
passos-magicos-datathon/
├── README.md
├── LICENSE
├── requirements.txt
├── environment.yml
├── config.yaml                      # seed, caminhos e faixas de validação
├── .gitignore
│
├── data/
│   ├── raw/                         # planilha original disponibilizada (não versionada)
│   ├── interim/                     # painel limpo e log de limpeza
│   └── processed/
│
├── notebooks/
│   ├── 01\_qualidade\_dados.ipynb     # auditoria
│   ├── 02\_eda\_perguntas.ipynb       # 11 perguntas do trabalho
│   └── 03\_modelo\_risco.ipynb        # Modelo entregue
│
├── src/
│   ├── data/
│   │   ├── load.py                  # junta as 3 abas num painel
│   │   ├── clean.py                 # limpeza com log.
│   │   └── validate.py              # contratos que falham.
│   ├── features/build.py            # variáveis e verificação de vazamento
│   ├── models/
│   │   ├── train.py                 # pipelines dos cinco modelos
│   │   └── evaluate.py              # PR-AUC, calibração, recall por faixa
│   └── analysis/eda\_tecnica.py      # drift, VIF, shift, fluxo do painel
│
├── app/
│   ├── streamlit\_app.py             # abas lote.
│   ├── requirements.txt
│   ├── exemplo\_turma.csv            # 18 alunos para teste
│   ├── README.md
│   └── artifacts/modelo\_risco.joblib
│
├── reports/
│   ├── deck\_gerencial.pptx
│   ├── figures/
│   └── \*.csv                        # coeficientes, drift, shift
│
└── docs/
    ├── decisoes\_tecnicas.md         # o que decidi e o que mudei de ideia
    └── quadro\_hipoteses.csv         # 20 hipóteses com veredito
```

\---

# Explicação das decisões tomadas...

**Vazamento** A cadeia `Fase + Fase Ideal` leva a `Defasagem`, que leva a `IAN`, que compõe o `INDE` e vira `Pedra`. Tudo determinístico. Por isso deixei IAN, INDE e Pedra proibidos como preditores, e o `src/features/build.py` levanta erro se algum deles entrar ou se qualquer variável passar de 0,9 de correlação com o alvo. A maior que encontrei foi 0,308.

**Percentil dentro de cada ano** O IPS vai de 7,50 para 5,00 e volta para 7,51 na coorte fechada, com a mesma população. Isso é mudança no jeito de calcular, não nos alunos. Usando percentil, o modelo fica imune a esse tipo de deslocamento.

**Zeros tratados caso a caso** No IAA existe uma lacuna na distribuição, sem nenhum valor entre 0 e 1,7, e os zeros não persistem de um ano para o outro. Tem cara de não resposta, então converti para nulo. Já IEG e IDA têm distribuição contínua e ali o zero é medida real então mantive.

*Sem SMOTE* Com 17,3% de eventos o problema não é falta de casos positivos, é calibração. Casos sintéticos distorceriam justamente a probabilidade que eu preciso preservar.

**integridade** O `src/data/validate.py` confere chave única, a invariante da defasagem, as faixas dos indicadores e a cobertura por ano. Testei cada um contra corrupção injetada de propósito, e todos falharam como deveriam.

---

## O que estes dados não permitem afirmar

1° A base não tem grupo de controle.
2° A análise longitudinal só enxerga quem ficou. Entre 25% e 30% saem por ano.
3° Não dá para separar não promoção pedagógica de administrativa.
4° O IPP ficou de fora porque não existe em 2022. Testei e ele não faria diferença sobre o conjunto completo de variáveis.
5° O modelo mede descompasso de calendário, não desempenho pedagógico.
6° O IPV pode ser usado pela própria instituição na hora de decidir a promoção, o que tornaria parte da previsão circular.
7° Onze das treze variáveis pouco agregam. Só `defasagem` e `fase_ideal` já entregam 0,264 de PR-AUC no estrato avançada, contra 0,327 do conjunto completo. O fenômeno é majoritariamente estrutural.
8° As métricas relatadas vêm do modelo treinado apenas em 2022 para 2023. O modelo publicado foi retreinado com todos os dados.

---

# Erros que cometi e corrigi

O parser comeu uma casa decimal. O INDE de 2024 vinha como texto, e minha
regra de separador de milhar removia o ponto de `8.337`, virando `8337`. A média
do ano foi para 15. Só apareceu porque a validação olha distribuição, não só
estrutura da tabela.

O `class_weight='balanced'` destruiu a calibração. Ele melhora o ranking, mas
o modelo passou a prever 0,839 onde o real era 0,464. Como o enunciado pede
probabilidade e não ordenação, tirei.

Errei a aplicação dos limites de Manski. Na primeira versão eu subtraía
limite inferior de limite inferior, o que não é um limite válido para diferença.
Descobri numa auditoria que fiz no fim do projeto, revisando tudo como se fosse
outra pessoa avaliando. A conclusão mudou e o texto foi reescrito.

**Uma variável que eu tinha certeza que ia funcionar, não funcionou.** Criei uma
medida de idade relativa à fase ideal achando que capturaria o ciclo da régua.
AUC de 0,516, ou seja, nada. Mantive no conjunto porque sim, mas registrei
que a expectativa não se confirmou.
